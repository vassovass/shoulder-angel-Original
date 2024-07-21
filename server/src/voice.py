import requests
import os

default_first_msg = "Hello Sam. This is your Shoulder Angel."


def call_user(first_msg=default_first_msg):
    """Trigger a call thru Vapi to a user, with context"""
    # Your Vapi API Authorization token
    auth_token = os.environ["VAPI_AUTH_TOKEN"]
    phone_number_id = os.environ["VAPI_PHONE_NUMBER_ID"]
    # The Phone Number ID, and the Customer details for the call
    customer_number = os.environ["TEST_NUMBER"]
    llm_model = "llama3-70b-8192"

    # Create the header with Authorization token
    headers = {
        "Authorization": f"Bearer {auth_token}",
        "Content-Type": "application/json",
    }

    # Create the data payload for the API request
    data = {
        "assistant": {
            "firstMessage": first_msg,
            "model": {
                "provider": "groq",
                "model": llm_model,
                "messages": [
                    {
                        "role": "system",
                        "content": """Your name is Angel, short for Shoulder Angel. You are a voice agent on a phone call. Your goal is to help a user clarify their goals for the day, and to ensure they're pursuing them.

Start by asking what a user's goals for the day are.""",
                    }
                ],
            },
            "voice": "jennifer-playht",
        },
        "phoneNumberId": phone_number_id,
        "customer": {
            "number": customer_number,
        },
    }

    requests.post(
        os.environ["VAPI_ENDPOINT"],
        headers=headers,
        json=data,
    )

    return None
