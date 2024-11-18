# actions.py
from typing import Any, Text, Dict, List
from rasa_sdk import Action, Tracker
from rasa_sdk.events import SlotSet
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


class ActionShowItems(Action):
    def name(self) -> Text:
        return "action_show_items"

    def run(self, dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:

        # You'll need to implement a way to get the actual farmer_id
        farmer_id = 1

        try:
            # Make API call to get items
            response = requests.get(
                f'https://buddiv2-api.onrender.com/items/farmer/{farmer_id}',
                headers={'Content-Type': 'application/json'}
            )

            if response.status_code == 200:
                items = response.json()

                if items:
                    # Create a formatted message with all items
                    message = "Here are your items:\n\n"
                    for item in items:
                        message += (f"📦 Item: {item['item_name']}\n"
                                    f"   Quantity: {item['quantity']}\n"
                                    f"   Price: ₹{float(item['price'])}\n"
                                    f"   ID: {item['item_id']}\n\n")

                    dispatcher.utter_message(text=message)
                else:
                    dispatcher.utter_message(text="You don't have any items listed yet.")

            elif response.status_code == 404:
                dispatcher.utter_message(text="You don't have any items listed yet.")
            else:
                dispatcher.utter_message(text="Sorry, I couldn't fetch your items at the moment.")

        except requests.exceptions.RequestException as e:
            dispatcher.utter_message(text="Sorry, I'm having trouble connecting to the database.")
            print(f"Error: {str(e)}")

        return []


class ActionShowItemDetails(Action):
    def name(self) -> Text:
        return "action_show_item_details"

    def run(self, dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:

        # Get item_id from slot
        item_id = tracker.get_slot('item_id')

        if not item_id:
            dispatcher.utter_message(text="Please provide an item ID to view its details.")
            return []

        try:
            # Make API call to get specific item
            response = requests.get(
                f'https://buddiv2-api.onrender.com/items/{item_id}',
                headers={'Content-Type': 'application/json'}
            )

            if response.status_code == 200:
                item = response.json()

                # Format the item details
                message = (f"📦 Item Details:\n\n"
                           f"Name: {item['item_name']}\n"
                           f"Quantity: {item['quantity']}\n"
                           f"Price: ₹{float(item['price'])}\n"
                           f"Farmer ID: {item['farmer_id']}\n")

                if item['description']:
                    message += f"Description: {item['description']}\n"

                dispatcher.utter_message(text=message)

            elif response.status_code == 404:
                dispatcher.utter_message(text=f"Sorry, I couldn't find any item with ID {item_id}.")
            else:
                dispatcher.utter_message(text="Sorry, I couldn't fetch the item details at the moment.")

        except requests.exceptions.RequestException as e:
            dispatcher.utter_message(text="Sorry, I'm having trouble connecting to the database.")
            print(f"Error: {str(e)}")

        return []



class ActionRecordSale(Action):
    def name(self) -> Text:
        return "action_record_sale"

    def run(self, dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:

        # Extract slot values
        item_id = tracker.get_slot("item_id")
        buyer_id = tracker.get_slot("buyer_id")
        quantity_sold = tracker.get_slot("quantity_sold")
        sale_price = tracker.get_slot("sale_price")

        # Prepare payload
        payload = {
            "item_id": int(item_id),
            "buyer_id": int(buyer_id) if buyer_id else None,
            "quantity_sold": int(quantity_sold),
            "sale_price": float(sale_price)
        }

        # API call
        try:
            response = requests.post("http://your-server-url/sales", json=payload)
            if response.status_code == 201:
                sale_id = response.json().get("sale_id")
                dispatcher.utter_message(text=f"Sale recorded successfully! Sale ID: {sale_id}")
                return [SlotSet("sale_id", sale_id)]
            else:
                dispatcher.utter_message(text=f"Failed to record sale: {response.json().get('message', 'Unknown error')}")
                return []
        except Exception as e:
            dispatcher.utter_message(text=f"Error: {str(e)}")
            return []


