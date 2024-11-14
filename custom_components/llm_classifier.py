# custom_components/llm_classifier.py
from typing import Any, Dict, List, Text
from rasa.nlu.components import Component
from rasa.nlu.model import Metadata
from rasa.shared.nlu.training_data.message import Message
from rasa.shared.nlu.training_data.training_data import TrainingData
import google.generativeai as genai
import cohere
import os


class LLMIntentClassifier(Component):
    """Custom component for intent classification using Gemini and Cohere"""

    defaults = {
        "gemini_api_key": None,
        "cohere_api_key": None,
        "confidence_threshold": 0.7,
    }

    def __init__(self, component_config: Dict[Text, Any] = None) -> None:
        # Load API keys from environment variables
        self.gemini_api_key = os.getenv('GEMINI_API_KEY')
        if not self.gemini_api_key:
            raise ValueError("GEMINI_API_KEY environment variable is not set")

        self.cohere_api_key = os.getenv('COHERE_API_KEY')
        if not self.cohere_api_key:
            raise ValueError("COHERE_API_KEY environment variable is not set")
        super().__init__(component_config)
        self.gemini_api_key = component_config.get("gemini_api_key")
        self.cohere_api_key = component_config.get("cohere_api_key")
        self.confidence_threshold = component_config.get("confidence_threshold", 0.7)

        # Initialize Gemini
        genai.configure(api_key=self.gemini_api_key)
        self.gemini_model = genai.GenerativeModel('gemini-pro')

        # Initialize Cohere
        self.co = cohere.Client(self.cohere_api_key)

    def classify_with_gemini(self, text: Text, possible_intents: List[Text]) -> Dict[Text, float]:
        """Classify intent using Gemini"""
        prompt = f"""
        Given the user message: "{text}"
        And these possible intents: {possible_intents}

        Return the most likely intent and confidence score as JSON:
        {{
            "intent": "intent_name",
            "confidence": 0.95
        }}
        """

        response = self.gemini_model.generate_content(prompt)
        result = eval(response.text)  # Convert string to dict
        return result

    def classify_with_cohere(self, text: Text, possible_intents: List[Text]) -> Dict[Text, float]:
        """Classify intent using Cohere"""
        examples = [
            {"text": "hey", "label": "greet"},
            {"text": "hello", "label": "greet"},
            {"text": "i have 10kg tomatoes", "label": "inform_harvest"},
            {"text": "we harvested 20kg potatoes", "label": "inform_harvest"},
            {"text": "price is 5.99", "label": "inform_price"},
            {"text": "selling at 10.50", "label": "inform_price"},
            {"text": "my farmer id is 123", "label": "provide_farmer_id"},
            {"text": "goodbye", "label": "goodbye"}
        ]

        response = self.co.classify(
            inputs=[text],
            examples=examples
        )

        return {
            "intent": response.classifications[0].prediction,
            "confidence": response.classifications[0].confidence
        }

    def process(self, message: Message, **kwargs: Any) -> None:
        """Process incoming message"""
        text = message.get("text")

        # Get possible intents from training data
        possible_intents = [
            "greet", "goodbye", "inform_harvest",
            "inform_price", "provide_farmer_id"
        ]

        # Get classifications from both models
        gemini_result = self.classify_with_gemini(text, possible_intents)
        cohere_result = self.classify_with_cohere(text, possible_intents)

        # Ensemble the results (using max confidence)
        if gemini_result["confidence"] > cohere_result["confidence"]:
            final_intent = gemini_result["intent"]
            confidence = gemini_result["confidence"]
        else:
            final_intent = cohere_result["intent"]
            confidence = cohere_result["confidence"]

        # If confidence is too low, mark as intentless
        if confidence < self.confidence_threshold:
            intent = {"name": None, "confidence": 0.0}
            message.set("intent", intent, add_to_output=True)
            return

        intent = {
            "name": final_intent,
            "confidence": confidence
        }
        message.set("intent", intent, add_to_output=True)

    def persist(self, file_name: Text, model_dir: Text) -> Dict[Text, Any]:
        """Persist the component"""
        return {
            "file": file_name,
            "gemini_api_key": self.gemini_api_key,
            "cohere_api_key": self.cohere_api_key
        }

    @classmethod
    def load(cls,
             meta: Dict[Text, Any],
             model_dir: Text,
             model_metadata: Metadata = None,
             cached_component: Component = None,
             **kwargs: Any) -> 'LLMIntentClassifier':
        """Load the component"""
        return cls(meta)