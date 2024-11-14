# actions/actions.py
from typing import Any, Text, Dict, List
from rasa_sdk import Action, Tracker
from rasa_sdk.executor import CollectingDispatcher
from rasa_sdk.events import SlotSet
import requests
import os
from dotenv import load_dotenv
from datetime import datetime

# Load environment variables
load_dotenv()


class ActionRecordHarvest(Action):
    """Custom action to record harvest in the database via API"""

    def name(self) -> Text:
        return "action_record_harvest"

    def run(self, dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:

        # Get API endpoint from environment variable, with default fallback
        API_URL = os.getenv('API_URL', 'http://localhost:5000/items')

        # Get all required slots
        quantity = tracker.get_slot('quantity')
        item_name = tracker.get_slot('item_name')
        price = tracker.get_slot('price')
        farmer_id = tracker.get_slot('farmer_id')

        # Validate required fields
        missing_fields = []
        if not quantity:
            missing_fields.append("quantity")
        if not item_name:
            missing_fields.append("item name")
        if not price:
            missing_fields.append("price")
        if not farmer_id:
            missing_fields.append("farmer ID")

        if missing_fields:
            missing_str = ", ".join(missing_fields)
            dispatcher.utter_message(text=f"I'm missing some required information: {missing_str}")
            return []

        try:
            # Convert values to proper types
            quantity = int(float(quantity))
            price = float(price)
            farmer_id = int(farmer_id)

            # Validate value ranges
            if quantity <= 0:
                dispatcher.utter_message(text="Quantity must be greater than 0")
                return []
            if price <= 0:
                dispatcher.utter_message(text="Price must be greater than 0")
                return []

            # Prepare data according to your API structure
            harvest_data = {
                "farmer_id": farmer_id,
                "item_name": item_name,
                "description": f"Harvest recorded via chatbot on {datetime.now().strftime('%Y-%m-%d')}",
                "quantity": quantity,
                "price": price
            }

            # Make API call
            response = requests.post(
                API_URL,
                json=harvest_data,
                headers={"Content-Type": "application/json"},
                timeout=10  # 10 seconds timeout
            )

            # Handle API response
            if response.status_code == 201:
                item_id = response.json().get("item_id")
                dispatcher.utter_message(
                    text=f"Successfully recorded your harvest!\n"
                         f"- {quantity} units of {item_name}\n"
                         f"- Price: ${price:.2f} per unit\n"
                         f"- Item ID: {item_id}"
                )

                # Clear slots after successful recording
                return [SlotSet(slot, None) for slot in ["quantity", "item_name", "price"]]

            else:
                dispatcher.utter_message(
                    text="Sorry, there was a problem recording your harvest. "
                         "Please try again or contact support if the problem persists."
                )

        except ValueError as e:
            dispatcher.utter_message(text=f"Invalid input: {str(e)}")

        except requests.RequestException as e:
            dispatcher.utter_message(
                text="Sorry, I couldn't connect to the database. "
                     "Please try again in a few minutes."
            )

        except Exception as e:
            dispatcher.utter_message(
                text="An unexpected error occurred. Please try again or contact support."
            )

        return []