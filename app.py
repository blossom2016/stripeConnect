from flask import Flask, request, redirect, jsonify, render_template
import stripe
import os
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)

# Configure Stripe
stripe.api_key = os.getenv("STRIPE_SECRET_KEY")
CLIENT_ID = os.getenv("STRIPE_CLIENT_ID")
PUBLISHABLE_KEY = os.getenv("STRIPE_PUBLISHABLE_KEY")
DOMAIN = os.getenv("DOMAIN") or "http://127.0.0.1:5000"
# print("Stripe Key:", stripe.api_key)

# Use your specific account ID
account_id = "acct_1RdH2lP0dISrUx8n"

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
def webhook():
    payload = request.data
    sig_header = request.headers.get('Stripe-Signature')
    endpoint_secret = os.getenv("STRIPE_WEBHOOK_SECRET")

    try:
        event = stripe.Webhook.construct_event(payload, sig_header, endpoint_secret)
    except ValueError:
        return "Invalid payload", 400
    except stripe.error.SignatureVerificationError:
        return "Invalid signature", 400

    if event["type"] == "checkout.session.completed":
        session = event["data"]["object"]
        print("✅ Payment succeeded for session:", session["id"])

    return "", 200

@app.route("/success")
def success():
    return "✅ Payment completed successfully!"

@app.route("/cancel")
def cancel():
    return "❌ Payment canceled."

if __name__ == "__main__":
    app.run(port=5000, debug=True)