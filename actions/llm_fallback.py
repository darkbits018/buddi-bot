# actions/llm_fallback.py
from typing import Any, Dict, Text, List
from rasa_sdk import Action, Tracker
from rasa_sdk.executor import CollectingDispatcher
import google.generativeai as genai
import cohere


class ActionLLMFallback(Action):
    """Fallback action for intentless messages using LLMs"""

    def name(self) -> Text:
        return "action_llm_fallback"

    def __init__(self):
        # Load API keys from environment variables
        gemini_api_key = os.getenv('GEMINI_API_KEY')
        if not gemini_api_key:
            raise ValueError("GEMINI_API_KEY environment variable is not set")

        cohere_api_key = os.getenv('COHERE_API_KEY')
        if not cohere_api_key:
            raise ValueError("COHERE_API_KEY environment variable is not set")
        # Initialize Gemini
        genai.configure(api_key="YOUR_GEMINI_API_KEY")
        self.gemini_model = genai.GenerativeModel('gemini-pro')

        # Initialize Cohere
        self.co = cohere.Client("YOUR_COHERE_API_KEY")

    def run(self, dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:
        # Get the last user message
        user_message = tracker.latest_message.get("text")

        # Context for the conversation
        context = """
        You are a chatbot helping farmers record their harvests. You can:
        1. Record harvest quantities (e.g., "10kg tomatoes")
        2. Record prices (e.g., "price is $5.99")
        3. Handle farmer IDs
        4. Provide basic assistance

        Try to guide the user towards providing structured information about their harvest.
        """

        # Get response from Gemini
        gemini_prompt = f"{context}\nUser: {user_message}\nBot:"
        gemini_response = self.gemini_model.generate_content(gemini_prompt)

        # Get response from Cohere
        cohere_response = self.co.generate(
            prompt=f"{context}\nUser: {user_message}\nBot:",
            max_tokens=100,
            temperature=0.7,
        )

        # Use the more relevant response
        # For now, we'll use Gemini's response as primary
        response_text = gemini_response.text

        dispatcher.utter_message(text=response_text)
        return []