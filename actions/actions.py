# actions.py
import re
from typing import Any, Text, Dict, List
from rasa_sdk import Action, Tracker, logger
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

        # Get slot values (reusing existing slots)
        item_id = tracker.get_slot('item_id')
        buyer_id = tracker.get_slot('buyer_id')
        quantity = int(float('item_quantity'))  # Handles cases like "98.0" or "98"
        price = float('item_price')  # Ensures a numeric price

        # Validate required slots
        if not all([item_id, quantity, price]):
            dispatcher.utter_message(text="Missing required sale information. Please provide all details.")
            return []

        # Clean price value (remove currency symbols if present)
        price = price.replace("USD", "").replace("Dollar", "").replace("INR", "").replace("Rs", "").replace("Rupees",
                                                                                                            "").strip()

        # Prepare data for API
        sale_data = {
            "item_id": int(item_id),
            "buyer_id": int(buyer_id) if buyer_id else None,
            "quantity_sold": int(quantity),
            "sale_price": float(price)
        }

        try:
            # Make API call
            response = requests.post(
                'https://buddiv2-api.onrender.com/sales',
                json=sale_data,
                headers={'Content-Type': 'application/json'}
            )

            if response.status_code == 201:
                sale_id = response.json().get('sale_id')
                dispatcher.utter_message(text=f"Sale recorded successfully! Sale ID: {sale_id}")
            else:
                dispatcher.utter_message(text="Failed to record sale. Please try again.")

        except Exception as e:
            dispatcher.utter_message(text="Error connecting to sales system. Please try again later.")

        # Clear slots after sale
        return [SlotSet("item_id", None),
                SlotSet("buyer_id", None),
                SlotSet("item_quantity", None),
                SlotSet("item_price", None)]


class ActionGetSaleDetails(Action):
    def name(self) -> Text:
        return "action_get_sale_details"

    def run(self, dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:

        # Check multiple possible entity names
        sale_id = (
                next(tracker.get_latest_entity_values("sale_id"), None) or
                next(tracker.get_latest_entity_values("item_id"), None) or
                tracker.get_slot("sale_id")
        )

        if not sale_id:
            dispatcher.utter_message("Sorry, I couldn't find a sale ID to retrieve details.")
            return []

        try:
            # Replace with your actual API endpoint base URL
            url = f"https://buddiv2-api.onrender.com/sales/{sale_id}"
            response = requests.get(url)

            if response.status_code == 404:
                dispatcher.utter_message(f"No sale found with ID {sale_id}.")
                return []

            sale_data = response.json()

            # Enhanced formatting
            message = f"""📦 Sale Details (ID: {sale_data['sale_id']})
----------------------------------------
🛍️ Item ID: {sale_data['item_id']}
👤 Buyer ID: {sale_data['buyer_id']}
📊 Quantity: {sale_data['quantity_sold']}
💰 Unit Price: ${sale_data['sale_price']}
💵 Total Sale: ${sale_data['total_sale_amount']}
"""

            dispatcher.utter_message(message)

            return [
                SlotSet("last_retrieved_sale_id", sale_id),
                SlotSet("last_sale_total", sale_data['total_sale_amount'])
            ]

        except requests.RequestException:
            dispatcher.utter_message("Sorry, there was an error retrieving the sale details.")
            return []


# class ActionGetFarmerSales(Action):
#     def name(self) -> Text:
#         return "action_get_farmer_sales"
#
#     def run(self, dispatcher: CollectingDispatcher,
#             tracker: Tracker,
#             domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:
#
#         # Extract farmer ID using multiple methods
#         import re
#
#         # Try to extract farmer ID directly from the message text
#         message_text = tracker.latest_message['text'].lower()
#         farmer_id_match = re.search(r'farmer\s+(\d+)', message_text)
#
#         if farmer_id_match:
#             farmer_id = farmer_id_match.group(1)
#         else:
#             # Fallback to entities
#             farmer_id = (
#                     next(tracker.get_latest_entity_values("farmer_id"), None) or
#                     next(tracker.get_latest_entity_values("item_id"), None) or
#                     tracker.get_slot("farmer_id")
#             )
#
#         if not farmer_id:
#             dispatcher.utter_message("Sorry, I couldn't find a farmer ID to retrieve sales.")
#             return []
#
#         try:
#             # Ensure farmer_id is a string
#             farmer_id = str(farmer_id)
#
#             # API call
#             url = f"https://buddiv2-api.onrender.com/sales/farmer/{farmer_id}"
#             response = requests.get(url)
#
#             if response.status_code == 404:
#                 dispatcher.utter_message(f"No sales found for farmer with ID {farmer_id}.")
#                 return []
#
#             sales_data = response.json()
#
#             # Format the message
#             message = f"Sales for Farmer {farmer_id}:\n"
#             total_sales = 0
#             for sale in sales_data:
#                 message += f"\n- Sale ID: {sale['sale_id']}"
#                 message += f"\n  Item ID: {sale['item_id']}"
#                 message += f"\n  Quantity: {sale['quantity_sold']}"
#                 message += f"\n  Total Amount: ${sale['total_sale_amount']}\n"
#                 total_sales += float(sale['total_sale_amount'])
#
#
#             message += f"\nTotal Sales: ${total_sales}"
#
#             dispatcher.utter_message(message)
#
#             return [
#                 SlotSet("last_retrieved_farmer_id", farmer_id),
#                 SlotSet("farmer_total_sales", total_sales)
#             ]
#
#         except Exception as e:
#             dispatcher.utter_message(f"Sorry, there was an error retrieving farmer sales: {str(e)}")
#             return []

class ActionGetFarmerSales(Action):
    def name(self) -> Text:
        return "action_get_farmer_sales"

    def run(self, dispatcher: CollectingDispatcher, tracker: Tracker, domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:
        # Extract Farmer ID
        message_text = tracker.latest_message['text'].lower()
        farmer_id = re.search(r'farmer\s+(\d+)', message_text)
        if farmer_id:
            farmer_id = farmer_id.group(1)
        else:
            farmer_id = next(tracker.get_latest_entity_values("farmer_id"), None) or tracker.get_slot("farmer_id")

        if not farmer_id:
            dispatcher.utter_message("Sorry, I couldn't find a farmer ID to retrieve sales.")
            return []

        logger.debug(f"Extracted Farmer ID: {farmer_id}")

        try:
            # Fetch Sales Data
            url = f"https://buddiv2-api.onrender.com/sales/farmer/{farmer_id}"
            response = requests.get(url, timeout=10)

            if response.status_code == 200:
                sales_data = response.json()

                if not isinstance(sales_data, list):
                    dispatcher.utter_message("Unexpected response format from the API.")
                    return []

                # Process Sales Data
                total_sales = 0
                message = f"Sales for Farmer {farmer_id}:\n"

                for sale in sales_data:
                    try:
                        total_sales += float(sale.get('total_sale_amount', 0))
                        message += (
                            f"\n- Sale ID: {sale.get('sale_id', 'unknown')}"
                            f"\n  Item ID: {sale.get('item_id', 'unknown')}"
                            f"\n  Quantity: {sale.get('quantity_sold', 'unknown')}"
                            f"\n  Total Amount: ${sale.get('total_sale_amount', 0):,.2f}\n"
                        )
                    except ValueError:
                        message += f"\n  Skipping sale due to invalid data: {sale}"

                message += f"\nTotal Sales: ${total_sales:,.2f}"
                dispatcher.utter_message(message)

                # Set Slots
                return [
                    SlotSet("last_retrieved_farmer_id", farmer_id),
                    SlotSet("farmer_total_sales", total_sales),
                ]

            elif response.status_code == 404:
                dispatcher.utter_message(f"No sales found for farmer with ID {farmer_id}.")
            else:
                dispatcher.utter_message(f"Error fetching sales data. API returned status {response.status_code}.")

        except requests.exceptions.Timeout:
            dispatcher.utter_message("The request to the sales API timed out. Please try again later.")
        except requests.exceptions.RequestException as e:
            dispatcher.utter_message(f"An error occurred while connecting to the sales API: {str(e)}")
        except Exception as e:
            dispatcher.utter_message(f"Sorry, there was an error retrieving farmer sales: {str(e)}")

        return []
