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
                    "Return a single word 'True' if the text on the screen seems to line up"
                    " with the user's stated goals. If it doesn't, draft a greeting message "
                    "to the user, reminding them of their goal, and asking about their current"
                    " activity. Keep it within two sentences"
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
                    "Return a single word `True` or `False`. Say 'True' if the text on the screen seems to line up"
                    " with the user's stated goals. Say 'False' if it doesn't."
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
