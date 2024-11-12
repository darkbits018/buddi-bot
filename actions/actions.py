from rasa_sdk import Action
from rasa_sdk.executor import CollectingDispatcher
from rasa_sdk.interfaces import Tracker
from rasa_sdk.events import SlotSet
import requests

class ActionAddItem(Action):

    def name(self) -> str:
        return "action_add_item"

    def run(self, dispatcher: CollectingDispatcher, tracker: Tracker, domain: dict):
        # Set user type, replace this with actual logic to determine user type
        user_type = "farmer"  # Hardcoded for now, replace with your actual logic

        # Check if the user is a farmer or buyer and set the farmer_id accordingly
        if user_type == "farmer":
            farmer_id = 1  # Hardcoded farmer ID for farmers
            dispatcher.utter_message(text="You are registered as a farmer.")
        else:
            farmer_id = None  # No farmer ID for buyers
            dispatcher.utter_message(text="You are registered as a buyer.")

        # Get details from user input (assumed to be set via slots)
        item_name = tracker.get_slot('item_name')  # Item name (set by user)
        description = tracker.get_slot('description')  # Item description (set by user)
        quantity = tracker.get_slot('quantity')  # Quantity (set by user)

        # Set default values if any of these are missing
        price = tracker.get_slot('price') if tracker.get_slot('price') else 100  # Default price if not provided
        item_name = item_name if item_name else "Unknown Item"  # Default item name if not provided
        description = description if description else "No description provided"  # Default description if not provided
        quantity = quantity if quantity else 1  # Default quantity if not provided

        # API URL of your Flask app (ensure this points to your Flask API)
        api_url = 'https://buddiv2-api.onrender.com/items'  # Update if needed

        if user_type == "farmer":  # Only farmers can add items
            # Create the payload
            data = {
                "farmer_id": farmer_id,  # Using default farmer_id 1
                "item_name": item_name,
                "description": description,
                "quantity": quantity,
                "price": price
            }

            # Send POST request to API to add the item
            response = requests.post(api_url, json=data)

            if response.status_code == 201:
                dispatcher.utter_message(text="Item has been added successfully!")
            else:
                dispatcher.utter_message(text=f"Sorry, there was an error while adding the item. Response: {response.text}")
        else:
            dispatcher.utter_message(text="As a buyer, you cannot add items. You can browse or purchase items.")

        return []
