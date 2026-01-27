from dotenv import load_dotenv
load_dotenv()

from fastapi import FastAPI
from bot.routers.leads import router as leads_router
from bot.routers.telegram_webhook import router as telegram_router
from bot.routers.whatsapp_webhook import router as whatsapp_router
from pathlib import Path
from fastapi.staticfiles import StaticFiles
from fastapi.responses import RedirectResponse

app = FastAPI(title="KarmaBox Bot API", version="0.1.0")
app.include_router(leads_router)
app.include_router(telegram_router)
app.include_router(whatsapp_router)

UI_DIR = Path(__file__).resolve().parent / "bot" / "ui"
app.mount("/ui", StaticFiles(directory=str(UI_DIR), html=True), name="ui")

@app.get("/")
def root():
    return RedirectResponse(url="/ui/")