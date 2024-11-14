#llm_classifier
from typing import Any, Dict, List, Text, Type
from rasa.engine.recipes.default_recipe import DefaultV1Recipe
from rasa.engine.graph import GraphComponent, ExecutionContext
from rasa.engine.storage.resource import Resource
from rasa.engine.storage.storage import ModelStorage
from rasa.shared.nlu.training_data.message import Message
from rasa.shared.nlu.training_data.training_data import TrainingData
import google.generativeai as genai
import cohere
import os
import json


@DefaultV1Recipe.register(
    [DefaultV1Recipe.ComponentType.INTENT_CLASSIFIER], is_trainable=True
)
class LLMIntentClassifier(GraphComponent):
    """Custom component for intent classification using Gemini and Cohere"""

    @classmethod
    def required_components(cls) -> List[Type]:
        """Components that should be included in the pipeline before this component."""
        return []

    @staticmethod
    def get_default_config() -> Dict[Text, Any]:
        """Default config"""
        return {
            "gemini_api_key": None,
            "cohere_api_key": None,
            "confidence_threshold": 0.7,
        }

    def __init__(
            self,
            config: Dict[Text, Any],
            model_storage: ModelStorage,
            resource: Resource,
            execution_context: ExecutionContext,
    ) -> None:
        """Initialize the component"""
        self._config = config

        # Load API keys from environment variables
        self.gemini_api_key = os.getenv('GEMINI_API_KEY')
        if not self.gemini_api_key:
            raise ValueError("GEMINI_API_KEY environment variable is not set")

        self.cohere_api_key = os.getenv('COHERE_API_KEY')
        if not self.cohere_api_key:
            raise ValueError("COHERE_API_KEY environment variable is not set")

        self.confidence_threshold = config.get("confidence_threshold", 0.7)

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
        try:
            result = json.loads(response.text)
            return result
        except json.JSONDecodeError:
            # Fallback in case of invalid JSON
            return {"intent": None, "confidence": 0.0}

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

    def train(self, training_data: TrainingData) -> Resource:
        """Training is not required for this component."""
        return None

    def process_training_data(self, training_data: TrainingData) -> TrainingData:
        """Process the training data if needed."""
        return training_data

    def process(self, messages: List[Message]) -> List[Message]:
        """Process a list of messages."""
        for message in messages:
            text = message.get("text")

            # Get possible intents
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
            else:
                intent = {
                    "name": final_intent,
                    "confidence": confidence
                }

            message.set("intent", intent)

        return messages