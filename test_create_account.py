import stripe
import os
from dotenv import load_dotenv

load_dotenv()
stripe.api_key = os.getenv("STRIPE_SECRET_KEY")

try:
    account = stripe.Account.create(type="express")
    print("Connected account created:", account.id)
except stripe.error.StripeError as e:
    print("Stripe error occurred:", e)
    print("Full response:", e.user_message if hasattr(e, 'user_message') else str(e))
