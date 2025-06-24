from flask import Flask, request, redirect, jsonify, render_template
import stripe
import os
import requests
from dotenv import load_dotenv
from datetime import datetime

load_dotenv()

app = Flask(__name__)

# Configure Stripe
stripe.api_key = os.getenv("STRIPE_SECRET_KEY")
CLIENT_ID = os.getenv("STRIPE_CLIENT_ID")
PUBLISHABLE_KEY = os.getenv("STRIPE_PUBLISHABLE_KEY")
DOMAIN = os.getenv("DOMAIN") or "http://127.0.0.1:5000"
SLACK_WEBHOOK_URL = os.getenv("SLACK_WEBHOOK_URL")
STRIPE_WEBHOOK_SECRET = os.getenv("STRIPE_WEBHOOK_SECRET")
# print("Stripe Key:", stripe.api_key)

# Use your specific account ID
account_id = "acct_1RdH2lP0dISrUx8n"

def send_slack_notification(message):
    """Send notification to Slack channel"""
    if not SLACK_WEBHOOK_URL:
        print("Slack webhook URL not configured")
        return
    
    payload = {
        "text": message,
        "username": "Stripe Payment Bot",
        "icon_emoji": ":money_with_wings:"
    }
    
    try:
        response = requests.post(SLACK_WEBHOOK_URL, json=payload)
        response.raise_for_status()
        print("✅ Slack notification sent successfully")
    except Exception as e:
        print(f"❌ Failed to send Slack notification: {str(e)}")

account_link = stripe.AccountLink.create(
    account=account_id,
    refresh_url="http://127.0.0.1:5000/reauth",
    return_url="http://127.0.0.1:5000/return",
    type="account_onboarding",
)
# print("Send user to:", account_link.url)

VENDORS = {
    "v3": account_id,  # Using your specific account ID
}

# Mock DB
PRODUCTS = {
    "1": {"name": "Handmade Mug", "price": 2000, "vendor_id": "v3"},
    "2": {"name": "Canvas Tote Bag", "price": 1500, "vendor_id": "v3"},
    "3": {"name": "Organic Beeswax Candle", "price": 1800, "vendor_id": "v3"},
    "4": {"name": "Wool Knit Scarf", "price": 2500, "vendor_id": "v3"},
    "5": {"name": "Custom Portrait Sketch", "price": 4000, "vendor_id": "v3"},
    "6": {"name": "Leather Journal", "price": 2200, "vendor_id": "v3"},
    "7": {"name": "Wooden Cutting Board", "price": 2700, "vendor_id": "v3"},
    "8": {"name": "Artisan Coffee Sampler", "price": 1600, "vendor_id": "v3"},
    "9": {"name": "Ceramic Plant Pot", "price": 1900, "vendor_id": "v3"},
    "10": {"name": "Hand-dyed Throw Blanket", "price": 3200, "vendor_id": "v3"},
}

# Home page with products
@app.route("/")
def home():
    return render_template("index.html", products=PRODUCTS)

@app.route("/onboard-vendor/<vendor_id>")
def onboard_vendor(vendor_id):
    if vendor_id in VENDORS:
        account_id = VENDORS[vendor_id]
    else:
        account = stripe.Account.create(
            type="express",
            capabilities={"transfers": {"requested": True}},
        )
        account_id = account.id
        VENDORS[vendor_id] = account_id

    account_link = stripe.AccountLink.create(
        account=account_id,
        refresh_url=f"{DOMAIN}/onboard-vendor/{vendor_id}",
        return_url=f"{DOMAIN}/vendor-onboarded/{vendor_id}",
        type="account_onboarding",
    )
    return redirect(account_link.url)

@app.route("/vendor-onboarded/<vendor_id>")
def vendor_onboarded(vendor_id):
    account_id = VENDORS.get(vendor_id)
    if not account_id:
        return f"Vendor {vendor_id} not found or not onboarded.", 404
    return f"Vendor {vendor_id} onboarded with Stripe Account ID: {account_id}"

@app.route("/buy/<product_id>", methods=["GET"])
def buy(product_id):
    product = PRODUCTS.get(product_id)
    if not product:
        return "Product not found", 404

    vendor_id = product.get("vendor_id")
    vendor_stripe_id = VENDORS.get(vendor_id)

    if not vendor_stripe_id:
        return f"Vendor {vendor_id} not onboarded yet.", 400

    try:
        session = stripe.checkout.Session.create(
            payment_method_types=["card"],
            line_items=[{
                'price_data': {
                    'currency': 'usd',
                    'product_data': {'name': product["name"]},
                    'unit_amount': product["price"],
                },
                'quantity': 1,
            }],
            mode='payment',
            payment_intent_data={
                'application_fee_amount': int(product["price"] * 0.10),  # 10% platform fee
                'transfer_data': {'destination': vendor_stripe_id},
            },
            success_url=f"{DOMAIN}/success",
            cancel_url=f"{DOMAIN}/cancel",
        )
        return redirect(session.url, code=303)
    except Exception as e:
        return f"Error creating checkout session: {str(e)}", 500

# Stripe webhook to track payments
@app.route("/webhook", methods=["POST"])
def stripe_webhook():
    print("🔔 Webhook received!")
    
    payload = request.data
    sig_header = request.headers.get("Stripe-Signature")
    
    # Use the webhook secret from Stripe CLI
    webhook_secret = "whsec_59d5442ef468a768b07995916b789e033f0fe1ff1ec2f90b7d85a447c8906489"
    
    print(f"🔑 Using webhook secret: {webhook_secret[:20]}...")
    print(f"📝 Payload length: {len(payload)}")
    print(f"🔐 Signature header: {sig_header[:50]}...")

    try:
        event = stripe.Webhook.construct_event(
            payload, sig_header, webhook_secret
        )
        print(f"✅ Webhook verified! Event type: {event['type']}")
    except ValueError as e:
        print(f"❌ Invalid payload: {e}")
        return jsonify(success=False, error="Invalid payload"), 400
    except stripe.error.SignatureVerificationError as e:
        print(f"❌ Invalid signature: {e}")
        return jsonify(success=False, error="Invalid signature"), 400
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        return jsonify(success=False, error=str(e)), 400

    event_type = event["type"]
    data = event["data"]["object"]
    print(f"📊 Processing event: {event_type}")

    # Success event
    if event_type == "checkout.session.completed":
        customer_email = data.get("customer_details", {}).get("email", "Unknown")
        amount = data.get("amount_total", 0) / 100
        print(f"💰 Payment successful: ${amount} from {customer_email}")
        send_slack_notification(f"✅ Checkout succeeded for {customer_email}. Amount: ${amount:.2f}")

    # Failure-like events (Stripe doesn't have a direct 'failed' event for Checkout)
    elif event_type == "checkout.session.expired":
        print("⏰ Checkout session expired")
        send_slack_notification("⚠️ Checkout session expired — user did not complete payment.")

    elif event_type == "payment_intent.payment_failed":
        error_message = data.get("last_payment_error", {}).get("message", "Unknown error")
        print(f"❌ Payment failed: {error_message}")
        send_slack_notification(f"❌ Payment failed: {error_message}")
    else:
        print(f"ℹ️ Unhandled event type: {event_type}")

    return jsonify(success=True)

@app.route("/success")
def success():
    return "✅ Payment completed successfully!"

@app.route("/cancel")
def cancel():
    return "❌ Payment canceled."

@app.route("/test-slack")
def test_slack():
    """Test endpoint to verify Slack notifications work"""
    test_message = """
🧪 *Test Notification*
• This is a test message from your Stripe Connect app
• Time: """ + str(datetime.now()) + """
• Status: Testing Slack integration
    """
    send_slack_notification(test_message)
    return "Test Slack notification sent! Check your Slack channel."

if __name__ == "__main__":
    app.run(port=5000, debug=True)