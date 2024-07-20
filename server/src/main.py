import datetime
from fastapi import FastAPI
from contextlib import asynccontextmanager

from apscheduler.schedulers.background import BackgroundScheduler

# from apscheduler import apscheduler


def printit():
    print(datetime.datetime.now())


@asynccontextmanager
async def lifespan(app: FastAPI):
    scheduler = BackgroundScheduler()
    scheduler.add_job(printit, "interval", seconds=5)
    scheduler.start()
    yield


app = FastAPI(lifespan=lifespan)


# @app.get("/")
# async def test():
#     return "Ok"


@app.get("/")
def read_root():
    return {"Hello": "World"}
