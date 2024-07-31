import datetime
from contextlib import asynccontextmanager
from dotenv import load_dotenv
from fastapi import FastAPI
from apscheduler.schedulers.background import BackgroundScheduler
import weave


load_dotenv()

# local
from src.models import GroqScheduler, GroqOnTaskAnalyzer, GroqTaskReminderFirstMsg
from src.voice import call_user, router as voice_router
from src.memory import router as mem_router, get_user_goals
from src.state import load_convo, get_convo_history_as_groq

weave.init("shoulder-angel")

scheduler = GroqScheduler(
    model="llama3-70b-8192",
    system_message="Your role is to check whether the user is working when they should be. Compare their stated schedule with the current time.",
)

on_task_analyzer = GroqOnTaskAnalyzer(
    model="llama3-70b-8192",
    system_message="Your role is to analyze the user's OCR output and determine if it's relevant to their stated goals (infer this from recent conversation). Return the single word 'True' if it is otherwise return 'False', with nothing else. Use recent messages to understand a user's goals, but only use the OCR for current activity.",
)

activity_checkin_msg_generator = GroqTaskReminderFirstMsg(
    model="llama3-70b-8192",
    system_message="You're having a voice conversation with Sam. Their recent activity seems unaligned with their goals. You should ask about their current activities, and how it relates to their goals. Keep it within two sentences. Reply directly to Sam.",
)


# Shitty temporary state
last_seen = datetime.datetime.now().replace(hour=5)

# Pull conversation from pickled file (if available)
load_convo()


@weave.op()
def check_schedule():
    "Check if the user is active, also check their schedule. If scheduled but not active, place call"

    # fetch setting for work schedule (string initially)
    # gonna do a string literal for testing purposes
    user_sched_str = "I want to work literally all the time"

    # get current timestamp & format as something LLM readable
    # e.g. "Monday August 3rd at 5pm"
    now = datetime.datetime.now()
    llmnow = now.strftime("%A %B %d at %I%p PST")

    # check backend to see if user has been active (program sending pings)
    user_last_active = last_seen
    # llm_user_last_active = user_last_active.strftime("%A %B %d at %I%p PST")

    # have LLM check if it's currently scheduled time or not
    currently_within_schedule = scheduler.predict(user_sched_str, llmnow) == "True"

    # have LLM check if the last seen timestamp is within the last 30 minutes
    minutes_since_last_seen = int((now - user_last_active).seconds / 60)

    # working_recently = scheduler.evaluate_last_seen_ts(llm_user_last_active, llmnow)
    working_recently = minutes_since_last_seen < 30

    print(
        f"Currently within schedule: {currently_within_schedule}. User working recently: {working_recently}"
    )
    # if inactive and also outside of schedule, trigger call
    if currently_within_schedule and not working_recently:
        user_goal_m = get_user_goals(user_goal_m)
        call_user(
            first_msg=f"Hey Sam, checking in. It's been {minutes_since_last_seen} minutes since you were last active, but you'd intended to be productive right now. Are you still working?"
        )

    return None


@asynccontextmanager
async def lifespan(app: FastAPI):
    scheduler = BackgroundScheduler()
    scheduler.add_job(check_schedule, "interval", seconds=360)
    scheduler.start()
    yield


app = FastAPI(lifespan=lifespan)

app.include_router(mem_router)
app.include_router(voice_router)


# @app.get("/")
# async def test():
#     return "Ok"


@app.get("/")
def read_root():
    return {"Hello": "World"}


from pydantic import BaseModel


class ActivityData(BaseModel):
    data: list | None = None
    phone_data: str | None = None


@app.post("/handle_activity")
@weave.op()
def handle_activity(activity: ActivityData):
    """Take in OCR info, decide if it's relevant to current goals"""

    global last_seen
    last_seen = datetime.datetime.now()

    ocr_str = ""
    if activity.data:
        ocr_str = activity.data[0]["content"]["text"]
    elif activity.phone_data:
        ocr_str = activity.phone_data

    if not ocr_str:
        return None

    user_goal_m = get_user_goals()

    groq_convo_history = get_convo_history_as_groq()

    is_on_task = (
        on_task_analyzer.predict(
            user_goal_m, ocr_str, recent_messages=groq_convo_history[-20:]
        )
        == "True"
    )

    print(f"User is on task: {is_on_task}")

    # Draft first message with LLM

    if not is_on_task:
        first_msg = activity_checkin_msg_generator.predict(
            user_goal_m, ocr_str, recent_messages=groq_convo_history[-25:]
        )

        call_user(first_msg=first_msg, recent_ocr=ocr_str)

    return None
