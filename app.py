import os
import logging
from slack_bolt import App
from slack_bolt.adapter.socket_mode import SocketModeHandler
import stripe
from dotenv import load_dotenv

load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO)

# Initialize Slack app
app = App(
    token=os.environ.get("SLACK_BOT_TOKEN"),
    signing_secret=os.environ.get("SLACK_SIGNING_SECRET")
)

# Configure Stripe
stripe.api_key = os.environ.get("STRIPE_SECRET_KEY")

# Store for user sessions (in production, use a proper database)
user_sessions = {}

@app.message("hello")
def message_hello(message, say):
    """Respond to hello messages"""
    say(f"Hey there <@{message['user']}>! 👋")

@app.command("/support")
def support_command(ack, respond, command):
    """Handle /support slash command"""
    ack()
    
    blocks = [
        {
            "type": "section",
            "text": {
                "type": "mrkdwn",
                "text": "👋 Welcome to AI Support! How can I help you today?"
            }
        },
        {
            "type": "actions",
            "elements": [
                {
                    "type": "button",
                    "text": {
                        "type": "plain_text",
                        "text": "Ask a Question"
                    },
                    "value": "ask_question",
                    "action_id": "ask_question_btn"
                },
                {
                    "type": "button",
                    "text": {
                        "type": "plain_text",
                        "text": "Request Refund"
                    },
                    "style": "danger",
                    "value": "request_refund",
                    "action_id": "request_refund_btn"
                }
            ]
        }
    ]
    
    respond(blocks=blocks)

@app.command("/refund")
def refund_command(ack, respond, command):
    """Handle /refund slash command with charge ID"""
    ack()
    
    charge_id = command.get('text', '').strip()
    
    # Validate charge ID
    if not charge_id:
        respond({
            "response_type": "ephemeral",
            "blocks": [
                {
                    "type": "section",
                    "text": {
                        "type": "mrkdwn",
                        "text": "❌ Please provide a charge ID.\n\nUsage: `/refund ch_xxxxxxxxxxxxx`"
                    }
                }
            ]
        })
        return
    
    if not charge_id.startswith('ch_'):
        respond({
            "response_type": "ephemeral",
            "blocks": [
                {
                    "type": "section",
                    "text": {
                        "type": "mrkdwn",
                        "text": "❌ Invalid charge ID format. Charge IDs must start with `ch_`.\n\nUsage: `/refund ch_xxxxxxxxxxxxx`"
                    }
                }
            ]
        })
        return
    
    # Show processing message
    respond({
        "response_type": "in_channel",
        "blocks": [
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": "⏳ Processing refund..."
                }
            }
        ]
    })
    
    try:
        # Get charge details first
        charge = stripe.Charge.retrieve(charge_id)
        
        # Process full refund
        refund = stripe.Refund.create(
            charge=charge_id,
            reason='requested_by_customer',
            metadata={
                'slack_user_id': command['user_id'],
                'slack_channel_id': command['channel_id']
            }
        )
        
        # Format amounts for display
        refund_amount = refund.amount / 100
        currency = refund.currency.upper()
        
        # Create receipt blocks
        receipt_blocks = [
            {
                "type": "header",
                "text": {
                    "type": "plain_text",
                    "text": "💰 Refund Receipt"
                }
            },
            {
                "type": "section",
                "fields": [
                    {
                        "type": "mrkdwn",
                        "text": f"*Refund ID:*\n{refund.id}"
                    },
                    {
                        "type": "mrkdwn",
                        "text": f"*Amount:*\n${refund_amount:.2f} {currency}"
                    },
                    {
                        "type": "mrkdwn",
                        "text": f"*Status:*\n{refund.status.upper()}"
                    },
                    {
                        "type": "mrkdwn",
                        "text": f"*Original Charge:*\n{charge_id}"
                    },
                    {
                        "type": "mrkdwn",
                        "text": f"*Reason:*\nRequested by customer"
                    },
                    {
                        "type": "mrkdwn",
                        "text": f"*Timestamp:*\n<!date^{refund.created}^{{date_short}} {{time}}|{refund.created}>"
                    }
                ]
            },
            {
                "type": "divider"
            },
            {
                "type": "context",
                "elements": [
                    {
                        "type": "mrkdwn",
                        "text": "🧪 *TEST MODE* - Refund will appear on the original payment method within 5-10 business days."
                    }
                ]
            }
        ]
        
        # Post receipt in channel
        respond({
            "response_type": "in_channel",
            "replace_original": True,
            "blocks": receipt_blocks
        })
        
    except stripe.error.InvalidRequestError as e:
        error_msg = str(e)
        if "No such charge" in error_msg:
            error_text = f"❌ Charge ID `{charge_id}` not found. Please verify the charge ID is correct."
        elif "already been refunded" in error_msg:
            error_text = f"❌ This charge has already been fully refunded."
        else:
            error_text = f"❌ Invalid request: {error_msg}"
            
        respond({
            "response_type": "ephemeral",
            "replace_original": True,
            "blocks": [
                {
                    "type": "section",
                    "text": {
                        "type": "mrkdwn",
                        "text": error_text
                    }
                }
            ]
        })
        
    except stripe.error.StripeError as e:
        respond({
            "response_type": "ephemeral",
            "replace_original": True,
            "blocks": [
                {
                    "type": "section",
                    "text": {
                        "type": "mrkdwn",
                        "text": f"❌ Stripe error: {str(e)}"
                    }
                }
            ]
        })
        
    except Exception as e:
        respond({
            "response_type": "ephemeral",
            "replace_original": True,
            "blocks": [
                {
                    "type": "section",
                    "text": {
                        "type": "mrkdwn",
                        "text": f"❌ An error occurred while processing the refund: {str(e)}"
                    }
                }
            ]
        })

@app.action("ask_question_btn")
def handle_ask_question(ack, body, client):
    """Handle ask question button click"""
    ack()
    
    # Open modal for question input
    client.views_open(
        trigger_id=body["trigger_id"],
        view={
            "type": "modal",
            "callback_id": "question_modal",
            "title": {
                "type": "plain_text",
                "text": "Ask AI Support"
            },
            "submit": {
                "type": "plain_text",
                "text": "Submit"
            },
            "close": {
                "type": "plain_text",
                "text": "Cancel"
            },
            "blocks": [
                {
                    "type": "input",
                    "block_id": "question_input",
                    "element": {
                        "type": "plain_text_input",
                        "action_id": "question",
                        "multiline": True,
                        "placeholder": {
                            "type": "plain_text",
                            "text": "Enter your support question here..."
                        }
                    },
                    "label": {
                        "type": "plain_text",
                        "text": "Your Question"
                    }
                }
            ]
        }
    )

@app.view("question_modal")
def handle_question_submission(ack, body, client, view):
    """Handle question modal submission"""
    ack()
    
    user_id = body["user"]["id"]
    question = view["state"]["values"]["question_input"]["question"]["value"]
    
    # For now, provide a placeholder response
    # TODO: Integrate with OpenAI for actual AI responses
    response = f"Thank you for your question: '{question}'\n\nI'm currently being set up to provide AI-powered responses. Once the training data is available, I'll be able to help with support questions!"
    
    # Send response to user
    client.chat_postMessage(
        channel=user_id,
        text=response
    )

@app.action("request_refund_btn")
def handle_refund_request(ack, body, client):
    """Handle refund request button click"""
    ack()
    
    # Open modal for refund details
    client.views_open(
        trigger_id=body["trigger_id"],
        view={
            "type": "modal",
            "callback_id": "refund_modal",
            "title": {
                "type": "plain_text",
                "text": "Request Refund"
            },
            "submit": {
                "type": "plain_text",
                "text": "Process Refund"
            },
            "close": {
                "type": "plain_text",
                "text": "Cancel"
            },
            "blocks": [
                {
                    "type": "input",
                    "block_id": "payment_intent_input",
                    "element": {
                        "type": "plain_text_input",
                        "action_id": "payment_intent_id",
                        "placeholder": {
                            "type": "plain_text",
                            "text": "pi_1234567890abcdef"
                        }
                    },
                    "label": {
                        "type": "plain_text",
                        "text": "Payment Intent ID"
                    }
                },
                {
                    "type": "input",
                    "block_id": "amount_input",
                    "element": {
                        "type": "plain_text_input",
                        "action_id": "amount",
                        "placeholder": {
                            "type": "plain_text",
                            "text": "e.g., 1999 (for $19.99)"
                        }
                    },
                    "label": {
                        "type": "plain_text",
                        "text": "Refund Amount (in cents)"
                    }
                },
                {
                    "type": "input",
                    "block_id": "reason_input",
                    "element": {
                        "type": "plain_text_input",
                        "action_id": "reason",
                        "multiline": True,
                        "placeholder": {
                            "type": "plain_text",
                            "text": "Please explain the reason for the refund..."
                        }
                    },
                    "label": {
                        "type": "plain_text",
                        "text": "Refund Reason"
                    }
                }
            ]
        }
    )

@app.view("refund_modal")
def handle_refund_submission(ack, body, client, view):
    """Handle refund modal submission and process Stripe refund"""
    ack()
    
    user_id = body["user"]["id"]
    payment_intent_id = view["state"]["values"]["payment_intent_input"]["payment_intent_id"]["value"]
    amount = view["state"]["values"]["amount_input"]["amount"]["value"]
    reason = view["state"]["values"]["reason_input"]["reason"]["value"]
    
    try:
        # Process refund through Stripe
        refund = stripe.Refund.create(
            payment_intent=payment_intent_id,
            amount=int(amount),
            reason='requested_by_customer',
            metadata={
                'slack_user_id': user_id,
                'reason': reason
            }
        )
        
        # Format refund amount for display
        refund_amount = refund.amount / 100
        
        # Create receipt message
        receipt_blocks = [
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": f"✅ *Refund Processed Successfully*"
                }
            },
            {
                "type": "section",
                "fields": [
                    {
                        "type": "mrkdwn",
                        "text": f"*Refund ID:*\n{refund.id}"
                    },
                    {
                        "type": "mrkdwn",
                        "text": f"*Amount:*\n${refund_amount:.2f}"
                    },
                    {
                        "type": "mrkdwn",
                        "text": f"*Status:*\n{refund.status.title()}"
                    },
                    {
                        "type": "mrkdwn",
                        "text": f"*Payment Intent:*\n{payment_intent_id}"
                    }
                ]
            },
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": f"*Reason:* {reason}"
                }
            },
            {
                "type": "context",
                "elements": [
                    {
                        "type": "mrkdwn",
                        "text": f"Refund will appear on your original payment method within 5-10 business days."
                    }
                ]
            }
        ]
        
        # Send receipt to user
        client.chat_postMessage(
            channel=user_id,
            text=f"Refund processed: ${refund_amount:.2f}",
            blocks=receipt_blocks
        )
        
        # Also post to the channel where the command was issued
        if body.get("channel"):
            client.chat_postMessage(
                channel=body["channel"]["id"],
                text=f"Refund of ${refund_amount:.2f} has been processed for <@{user_id}>",
                blocks=[
                    {
                        "type": "section",
                        "text": {
                            "type": "mrkdwn",
                            "text": f"✅ Refund of *${refund_amount:.2f}* processed for <@{user_id}>"
                        }
                    }
                ]
            )
        
    except stripe.error.StripeError as e:
        # Handle Stripe errors
        error_message = f"❌ Refund failed: {str(e)}"
        client.chat_postMessage(
            channel=user_id,
            text=error_message
        )
    except Exception as e:
        # Handle other errors
        error_message = f"❌ An error occurred while processing the refund: {str(e)}"
        client.chat_postMessage(
            channel=user_id,
            text=error_message
        )

if __name__ == "__main__":
    # Start the app
    handler = SocketModeHandler(app, os.environ["SLACK_APP_TOKEN"])
    handler.start()