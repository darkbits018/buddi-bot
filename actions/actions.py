# actions.py
from typing import Any, Text, Dict, List
from rasa_sdk import Action, Tracker
from rasa_sdk.executor import CollectingDispatcher
import requests
import json


class ActionStoreItemDetails(Action):
    def name(self) -> Text:
        return "action_store_item_details"

    def run(self, dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:

        # Get values from slots
        item_name = tracker.get_slot('item_name')
        quantity = tracker.get_slot('item_quantity')
        price = tracker.get_slot('item_price')

        # Prepare data for API
        data = {
            "farmer_id": 2,  # You'll need to implement a way to get the actual farmer_id
            "item_name": item_name,
            "quantity": int(quantity),
            "price": float(price),
            "description": ""  # Optional field
        }

        try:
            # Make API call
            response = requests.post(
                'https://buddiv2-api.onrender.com/items',  # Replace with your actual API URL
                json=data,
                headers={'Content-Type': 'application/json'}
            )

            if response.status_code == 201:
                dispatcher.utter_message(text="Successfully stored item details in database!")
            else:
                dispatcher.utter_message(text="Sorry, there was an error storing the item details.")

        except requests.exceptions.RequestException as e:
            dispatcher.utter_message(text="Sorry, there was an error connecting to the database.")
            print(f"Error: {str(e)}")

        return []