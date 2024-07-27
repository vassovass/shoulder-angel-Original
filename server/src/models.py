from datetime import datetime
import weave
from groq import Groq


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
            {"role": "system", "content": f"Current time is {now_ts}"},
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
            stream=False,
            stop=None,
        )

        result = completion

        return result.choices[0].message.content

        # for chunk in completion:
        #     print(chunk.choices[0].delta.content or "", end="")

        # return completion.choices[0].message.content


class GroqOnTaskAnalyzer(weave.Model):
    model: str
    system_message: str

    def predict(self, user_goals: str, recent_ocr: str):
        client = Groq()

        messages = [
            {
                "role": "system",
                "content": self.system_message,
            },
            {"role": "user", "content": f"The user's current goals are: {user_goals}"},
            {
                "role": "system",
                "content": f"The user's screen last showed the following OCR'd text: {recent_ocr}",
            },
            {
                "role": "system",
                "content": (
                    "Return a single word `True` or `False`. Return 'True' if the text on the screen seems to line up"
                    " with the user's stated goals. If it doesn't line up with the user's stated goals, return 'False' with nothing else."
                    "Also return 'False' if there doesn't seem to be any OCR'd text. "
                ),
            },
        ]

        completion = client.chat.completions.create(
            model=self.model,
            messages=messages,
            temperature=1,
            max_tokens=1024,
            top_p=1,
            stream=False,
            stop=None,
        )

        result = completion

        return result.choices[0].message.content


class GroqTaskReminderFirstMsg(weave.Model):
    model: str
    system_message: str

    def predict(self, user_goals: str, recent_ocr: str):
        client = Groq()

        messages = [
            {
                "role": "system",
                "content": self.system_message,
            },
            {"role": "user", "content": f"The user's current goals are: {user_goals}"},
            {
                "role": "system",
                "content": f"The user's screen last showed the following OCR'd text: {recent_ocr}",
            },
            {
                "role": "system",
                "content": (
                    "Greet the user and ask them about their current activity, especially how it relates to their stated goals. Keep it within two sentences."
                ),
            },
            {
                "role": "system",
                "content": "<phone call to Sam connected>",
            },
        ]

        completion = client.chat.completions.create(
            model=self.model,
            messages=messages,
            temperature=1,
            max_tokens=1024,
            top_p=1,
            stream=False,
            stop=None,
        )

        result = completion

        return result.choices[0].message.content
