import requests
import os

default_first_msg = "Hello Sam. This is your Shoulder Angel."


def call_user(
    first_msg=default_first_msg, user_goal_m="No goals found, you should ask about them"
):
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
                        "content": """Your name is Angel, short for Shoulder Angel. You are a voice agent on a phone call. Your goal is to help a user stay on track for their goals for the day. End the conversation if A) they were actually focused on the right thing and you called them in error, B) they were distracted and are refocusing, or C) they otherwise request the conversation to end. If you have no memories of their goals, ask what they are.""",
                    },
                    {
                        "role": "system",
                        "content": f"Here are memories of the user's goals: {user_goal_m}",
                    },
                ],
                "toolIds": [
                    "84d7620b-83ef-4e75-a42f-9f22c3a407a7",  # add_new_memory
                    "e7f0b7c1-fb3a-43f1-a4e1-dca78e3d0675",  # fetch_memories
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
