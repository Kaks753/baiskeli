"""
mpesa.py — Safaricom Daraja STK Push integration
"""
import requests
import base64
from datetime import datetime
import os

# ── Put these in Streamlit secrets, NOT hardcoded ──────────────
CONSUMER_KEY    = os.environ.get("MPESA_CONSUMER_KEY", "")
CONSUMER_SECRET = os.environ.get("MPESA_CONSUMER_SECRET", "")
SHORTCODE       = os.environ.get("MPESA_SHORTCODE", "")      # your till/paybill
PASSKEY         = os.environ.get("MPESA_PASSKEY", "")
CALLBACK_URL    = os.environ.get("MPESA_CALLBACK_URL", "https://baiskeli.streamlit.app")

# Sandbox vs Production
BASE_URL = "https://sandbox.safaricom.co.ke"   # change to api.safaricom.co.ke for live


def get_access_token():
    """Get OAuth token from Safaricom."""
    url = f"{BASE_URL}/oauth/v1/generate?grant_type=client_credentials"
    response = requests.get(url, auth=(CONSUMER_KEY, CONSUMER_SECRET))
    response.raise_for_status()
    return response.json()["access_token"]


def generate_password():
    """Generate the base64 password for STK push."""
    timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
    raw = f"{SHORTCODE}{PASSKEY}{timestamp}"
    password = base64.b64encode(raw.encode()).decode()
    return password, timestamp


def stk_push(phone_number, amount, account_ref, description="Payment"):
    """
    Send STK push to customer phone.
    phone_number: format 2547XXXXXXXX (no + or leading 0)
    amount: integer KES amount
    Returns: (success: bool, message: str, checkout_request_id: str)
    """
    # Normalise phone number
    phone = str(phone_number).strip()
    if phone.startswith("0"):
        phone = "254" + phone[1:]
    elif phone.startswith("+"):
        phone = phone[1:]

    try:
        token    = get_access_token()
        password, timestamp = generate_password()

        headers = {"Authorization": f"Bearer {token}"}
        payload = {
            "BusinessShortCode": SHORTCODE,
            "Password":          password,
            "Timestamp":         timestamp,
            "TransactionType":   "CustomerPayBillOnline",  # or "CustomerBuyGoodsOnline" for till
            "Amount":            int(amount),
            "PartyA":            phone,
            "PartyB":            SHORTCODE,
            "PhoneNumber":       phone,
            "CallBackURL":       CALLBACK_URL,
            "AccountReference":  str(account_ref),
            "TransactionDesc":   description,
        }

        url = f"{BASE_URL}/mpesa/stkpush/v1/processrequest"
        response = requests.post(url, json=payload, headers=headers)
        data = response.json()

        if data.get("ResponseCode") == "0":
            return True, "✅ STK Push sent! Ask customer to check their phone.", data.get("CheckoutRequestID", "")
        else:
            return False, f"❌ {data.get('errorMessage', 'STK push failed')}", ""

    except Exception as e:
        return False, f"❌ Error: {str(e)}", ""


def check_transaction_status(checkout_request_id):
    """
    Query whether the STK push was completed.
    Returns: (paid: bool, message: str)
    """
    try:
        token    = get_access_token()
        password, timestamp = generate_password()

        headers = {"Authorization": f"Bearer {token}"}
        payload = {
            "BusinessShortCode": SHORTCODE,
            "Password":          password,
            "Timestamp":         timestamp,
            "CheckoutRequestID": checkout_request_id,
        }

        url = f"{BASE_URL}/mpesa/stkpushquery/v1/query"
        response = requests.post(url, json=payload, headers=headers)
        data = response.json()

        result_code = data.get("ResultCode")
        if result_code == "0" or result_code == 0:
            return True, "✅ Payment confirmed!"
        elif result_code == "1032":
            return False, "⏳ Customer cancelled the request."
        elif result_code == "1037":
            return False, "⏳ Request timed out — customer did not respond."
        else:
            return False, f"⏳ Pending or failed: {data.get('ResultDesc', '')}"

    except Exception as e:
        return False, f"❌ Error checking status: {str(e)}"