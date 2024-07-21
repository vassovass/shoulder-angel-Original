import datetime
import requests
from contextlib import asynccontextmanager
from fastapi import FastAPI
from apscheduler.schedulers.background import BackgroundScheduler
import weave
from dotenv import load_dotenv

load_dotenv()

# local
from src.models import GroqScheduler
from src.voice import call_user

weave.init("shoulder-angel")

scheduler = GroqScheduler(
    model="llama3-70b-8192",
    system_message="Your role is to check whether the user is working when they should be. Compare their stated schedule with the current time.",
)


def printit():
    print(datetime.datetime.now())


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
    user_last_active = now
    llm_user_last_active = llmnow

    # have LLM check if it's within schedule or not
    res = scheduler.predict(user_sched_str, llmnow)

    print(res)

    print(res == "True")
    # if inactive and also outside of schedule, trigger call
    if res == "True":
        call_user()

    return res


@asynccontextmanager
async def lifespan(app: FastAPI):
    scheduler = BackgroundScheduler()
    scheduler.add_job(check_schedule, "interval", seconds=60)
    scheduler.start()
    yield


app = FastAPI(lifespan=lifespan)


# @app.get("/")
# async def test():
#     return "Ok"


@app.get("/")
def read_root():
    return {"Hello": "World"}


@app.post("/handle_activity")
@weave.op()
def handle_activity(data):
    """Take in OCR info, decide if it's relevant to current goals"""

    print(data)

    ocr_str = data["data"][0]["content"]["text"]

    user_goals = "I want to be super productive and looking at coding things. I don't want to look at social sites, youtube, things like that."

    return None
