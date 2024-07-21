from datetime import datetime
import weave
from groq import Groq
from dotenv import load_dotenv

load_dotenv()


class GroqScheduler(weave.Model):
    model: str
    system_message: str

    @weave.op()
    def predict(self, user_sched: str, now_ts: str):
        client = Groq()

        messages = [
            {
                "role": "system",
                "content": self.system_message,
            },
            {"role": "user", "content": f"My preferred schedule is {user_sched}"},
            {"role": "system", "content": f"Current time is {now_ts}"},  # FIX THIS
            {
                "role": "system",
                "content": (
                    "Return a single word `True` or `False`. Say 'True' if the current time is"
                    " within the user's schedule. Say 'False' if it's outside the schedule."
                ),
            },
        ]

        completion = client.chat.completions.create(
            model=self.model,
            messages=messages,
            temperature=1,
            max_tokens=1024,
            top_p=1,
            stream=True,
            stop=None,
        )

        for chunk in completion:
            print(chunk.choices[0].delta.content or "", end="")

        return None

        return None
