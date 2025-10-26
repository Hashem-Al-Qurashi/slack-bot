# Slack AI Support Bot with Stripe Integration

A Python-based Slack bot that provides AI-powered support responses and handles Stripe refund processing.

## Features

- 🤖 AI-powered support question answering (ready for OpenAI integration)
- 💳 Stripe refund processing with test mode support
- 📋 Interactive Slack UI with buttons and modals
- 🧾 Automatic receipt generation and posting
- 🔐 Secure environment variable configuration

## Quick Start

### 1. Prerequisites

- Python 3.8+
- Slack workspace with admin access
- Stripe account (test mode)
- OpenAI API key (for AI features)

### 2. Installation

```bash
git clone <repository-url>
cd slack-ai-support-bot
pip install -r requirements.txt
```

### 3. Environment Setup

Copy `.env.example` to `.env` and fill in your credentials:

```bash
cp .env.example .env
```

Edit `.env` with your actual values:
- Get Slack tokens from https://api.slack.com/apps
- Get Stripe keys from https://dashboard.stripe.com/test/apikeys
- Get OpenAI key from https://platform.openai.com/api-keys

### 4. Slack App Configuration

1. Go to https://api.slack.com/apps and create a new app
2. Enable Socket Mode and generate an App-Level Token
3. Add these OAuth scopes:
   - `app_mentions:read`
   - `chat:write`
   - `commands`
   - `im:write`
4. Add slash command `/support`
5. Install app to your workspace

### 5. Run the Bot

```bash
python app.py
```

## Usage

### Support Command
Type `/support` in any channel to access the main menu with options to:
- Ask AI support questions
- Request refunds

### Refund Processing
1. Click "Request Refund" button
2. Enter Payment Intent ID from Stripe
3. Specify refund amount in cents
4. Provide reason for refund
5. Bot processes refund via Stripe API and posts receipt

## Architecture

```
slack-ai-support-bot/
├── app.py              # Main bot application
├── requirements.txt    # Python dependencies
├── .env.example       # Environment template
└── README.md          # This file
```

## Current Status

✅ **Completed:**
- Basic Slack bot framework using Bolt Python
- Stripe refund integration with test mode
- Interactive UI with buttons and modals
- Receipt generation and posting
- Error handling for Stripe API

🔄 **Pending (awaiting training data):**
- OpenAI integration for AI responses
- CSV ticket data processing
- 90% accuracy validation system

## Stripe Test Mode

The bot is configured for Stripe test mode. Use test payment intents:
- Test Payment Intent: `pi_1234567890abcdef`
- Test amounts: Any value in cents (e.g., 1999 = $19.99)

## Development

### Adding AI Training
When CSV ticket data becomes available:
1. Add training data processing in `ai_trainer.py`
2. Update question handler to use OpenAI API
3. Implement accuracy validation system

### Testing Refunds
Use Stripe's test environment:
1. Create test payment intents in Stripe Dashboard
2. Use bot to process refunds
3. Verify in Stripe Dashboard

## API Documentation

### Slack Commands
- `/support` - Main support menu

### Interactive Elements
- `ask_question_btn` - Opens question modal
- `request_refund_btn` - Opens refund modal

### Environment Variables
- `SLACK_BOT_TOKEN` - Bot user OAuth token
- `SLACK_SIGNING_SECRET` - App signing secret
- `SLACK_APP_TOKEN` - App-level token for Socket Mode
- `STRIPE_SECRET_KEY` - Stripe secret key (test mode)
- `OPENAI_API_KEY` - OpenAI API key

## Support

For issues and questions, refer to the codebase or Slack app documentation.