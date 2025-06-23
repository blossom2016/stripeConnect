Goal: Build a small web application that simulates a multi-vendor marketplace using Stripe Connect. When a customer checks out, the payment is split between the platform and the vendor.

Main Concepts:

Stripe Connect (Express/Standard accounts)

OAuth onboarding for sellers

Payment Intent + Application Fee + Transfer

Webhooks for order tracking


# Stripe Connect Marketplace

A Flask-based marketplace application that demonstrates Stripe Connect integration for handling payments between customers and vendors.

## Features

- **Vendor Onboarding**: Automated Stripe Connect account creation and onboarding
- **Product Catalog**: Display products from different vendors
- **Payment Processing**: Secure checkout with Stripe Checkout
- **Revenue Sharing**: Automatic platform fee collection (10%)
- **Payment Transfers**: Direct transfers to vendor accounts
- **Webhook Handling**: Real-time payment event processing

## Prerequisites

- Python 3.7+
- Stripe account with Connect enabled
- Stripe API keys

## Installation

1. **Clone the repository**
   ```bash
   git clone <your-repo-url>
   cd stripeConnect
   ```

2. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

3. **Set up environment variables**
   Create a `.env` file in the root directory:
   ```env
   STRIPE_SECRET_KEY=sk_test_your_secret_key_here
   STRIPE_PUBLISHABLE_KEY=pk_test_your_publishable_key_here
   STRIPE_CLIENT_ID=ca_your_client_id_here
   STRIPE_WEBHOOK_SECRET=whsec_your_webhook_secret_here
   DOMAIN=http://127.0.0.1:5000
   ```

4. **Update your Stripe Connect Account ID**
   In `app.py`, replace the account ID with your own:
   ```python
   account_id = "acct_your_account_id_here"
   ```

## Usage

### Running the Application

```bash
python app.py
```

The application will be available at `http://127.0.0.1:5000`

### API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/` | GET | Home page with product catalog |
| `/onboard-vendor/<vendor_id>` | GET | Start vendor onboarding process |
| `/vendor-onboarded/<vendor_id>` | GET | Vendor onboarding completion page |
| `/buy/<product_id>` | GET | Create checkout session for product |
| `/webhook` | POST | Stripe webhook endpoint |
| `/success` | GET | Payment success page |
| `/cancel` | GET | Payment cancellation page |

### Workflow

1. **Vendor Onboarding**
   - Navigate to `/onboard-vendor/v3` (or any vendor ID)
   - Complete Stripe Connect onboarding
   - Vendor account is created and stored

2. **Product Purchase**
   - Browse products on the home page
   - Click "Buy" on any product
   - Complete payment through Stripe Checkout
   - Platform collects 10% fee
   - Remaining amount transferred to vendor

3. **Payment Tracking**
   - Webhooks handle payment confirmations
   - Real-time payment status updates

## Configuration

### Stripe Connect Account Setup

1. **Enable Connect** in your Stripe Dashboard
2. **Configure capabilities**:
   - Card payments
   - Transfers
3. **Set up webhooks** for payment events

### Platform Fee Structure

- **Platform Fee**: 10% of transaction amount
- **Vendor Payout**: 90% of transaction amount
- **Automatic Transfer**: Funds transferred to vendor account

## File Structure

```
stripeConnect/
├── app.py                 # Main Flask application
├── requirements.txt       # Python dependencies
├── templates/
│   └── index.html        # Product catalog template
├── .env                  # Environment variables (not in git)
└── README.md            # This file
```

## Security Notes

- **Never commit** your `.env` file to version control
- **Rotate API keys** regularly
- **Use webhook signatures** for webhook verification
- **Validate all inputs** before processing

## Testing

### Test Cards

Use Stripe's test card numbers for testing:
- **Success**: `4242 4242 4242 4242`
- **Decline**: `4000 0000 0000 0002`
- **3D Secure**: `4000 0025 0000 3155`

### Webhook Testing

Use Stripe CLI to test webhooks locally:
```bash
stripe listen --forward-to localhost:5000/webhook
```

## Troubleshooting

### Common Issues

1. **"Account not found" errors**
   - Verify your Stripe Connect account ID is correct
   - Ensure the account has required capabilities

2. **Webhook signature verification fails**
   - Check your webhook secret in the `.env` file
   - Verify the webhook endpoint URL

3. **Payment transfers fail**
   - Ensure vendor accounts are fully onboarded
   - Check account capabilities and country settings

### Debug Mode

The application runs in debug mode by default. Check the console for detailed error messages and API responses.

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Test thoroughly
5. Submit a pull request

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Support

For issues related to:
- **Stripe API**: Check [Stripe Documentation](https://stripe.com/docs)
- **This Application**: Open an issue in the repository
- **Connect Setup**: Refer to [Stripe Connect Guide](https://stripe.com/docs/connect)

