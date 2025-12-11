import requests
import os

ADMIN_WHATSAPP = os.getenv('ADMIN_WHATSAPP', '94766226039')
WABOT_URL = 'https://app.wabot.my/api/send'
WABOT_INSTANCE_ID = os.getenv('WABOT_INSTANCE_ID')
WABOT_ACCESS_TOKEN = os.getenv('WABOT_ACCESS_TOKEN')

def send_admin_order_alert(order_id, customer_name, customer_phone, cart_items, total_price, user_comments):
    items_str = ""
    for item in cart_items:
        years = f"{item.selected_years[0]}-{item.selected_years[-1]}" if hasattr(item, 'selected_years') and item.selected_years else "N/A"
        items_str += f"- {item.name} ({years}) [{item.design_type}]\n"

    if not user_comments:
        user_comments = "None"

    message_body = (
        f"📦 *NEW ORDER RECEIVED* 📦\n"
        f"Order ID: *#{order_id}*\n\n"
        f"👤 *Customer:*\n"
        f"Name: {customer_name}\n"
        f"Contact: {customer_phone}\n\n"
        f"🛒 *Items:*\n"
        f"{items_str}\n"
        f"📝 *Comments:* {user_comments}\n"
        f"💰 *Total:* LKR {total_price:.2f}\n"
        f"-----------------------------"
    )
    
    payload = {
        "number": ADMIN_WHATSAPP,
        "type": "text",
        "message": message_body,
        "instance_id": WABOT_INSTANCE_ID,
        "access_token": WABOT_ACCESS_TOKEN
    }

    try:
        requests.post(WABOT_URL, json=payload)
        return True
    except requests.exceptions.RequestException:
        return False

def send_customer_order_confirmation(customer_phone, cart_items, total_price):
    items_str = ""
    for item in cart_items:
        years = f"{item.selected_years[0]}-{item.selected_years[-1]}" if hasattr(item, 'selected_years') and item.selected_years else "N/A"
        items_str += f"- {item.name} ({years}) [{item.design_type}]\n"

    message_body = (
        f"🎉 *Order Confirmation - Thank You!* 🎉\n\n"
        f"Your order has been successfully placed with the following details:\n\n"
        f"🛒 *Your Order Items:*\n"
        f"{items_str}\n"
        f"💰 *Total Price: LKR {total_price:.2f}*\n\n"
        f"--- 🏦 *Payment Instructions* 🏦 ---\n"
        f"Please transfer the total price to the following account to confirm your order:\n\n"
        f"🏦 *Bank:* Commercial Bank\n"
        f"💳 *Account No:* 8019889777\n"
        f"👤 *Account Name:* MASTER K AMODH PANDITHA GUNAWARDANA\n"
        f"📍 *Branch:* 121 - KOTTAWA BRANCH\n"
        f"-----------------------------------------\n"
        f"We will begin processing your order once payment is confirmed.\n"
        f"Thank you for choosing us!"
    )
    
    payload = {
        "number": customer_phone,
        "type": "text",
        "message": message_body,
        "instance_id": WABOT_INSTANCE_ID,
        "access_token": WABOT_ACCESS_TOKEN
    }

    try:
        requests.post(WABOT_URL, json=payload)
        return True
    except requests.exceptions.RequestException:
        return False

def send_contact_message(name, email, subject, user_message):
    message_body = (
        f"📨 *NEW CONTACT INQUIRY* 📨\n"
        f"👤 *Name:* {name}\n"
        f"📧 *Email:* {email}\n"
        f"📌 *Subject:* {subject}\n"
        f"📝 *Message:* {user_message}\n"
    )
    
    payload = {
        "number": ADMIN_WHATSAPP,
        "type": "text",
        "message": message_body,
        "instance_id": WABOT_INSTANCE_ID,
        "access_token": WABOT_ACCESS_TOKEN
    }

    try:
        requests.post(WABOT_URL, json=payload)
        return True
    except Exception:
        return False