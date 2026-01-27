from dotenv import load_dotenv
load_dotenv()

from fastapi import FastAPI
from bot.routers.leads import router as leads_router
from bot.routers.telegram_webhook import router as telegram_router

app = FastAPI(title="KarmaBox Bot API", version="0.1.0")
app.include_router(leads_router)
app.include_router(telegram_router)