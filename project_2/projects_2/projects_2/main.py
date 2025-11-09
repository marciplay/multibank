import logging
import uvicorn
from fastapi import FastAPI
from api.banks import router as banks_router
from api.payments import router as payments_router
from config import settings
from services.multi_bank_service import initialize_connections


logger = logging.getLogger(__name__)


logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

app = FastAPI(title=settings.app_name, debug=settings.debug)


app.include_router(banks_router)
app.include_router(payments_router)

@app.on_event("startup")
async def startup_event():
    await initialize_connections()
    logger.info("Подключения к банкам инициализированы.")

if __name__ == "__main__":
    uvicorn.run(app, host="127.0.0.1", port=8000, log_level="info")