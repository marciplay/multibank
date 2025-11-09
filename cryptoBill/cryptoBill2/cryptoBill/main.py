from fastapi import FastAPI
import uvicorn
from contextlib import asynccontextmanager
from crypto_module.api.routes import router as crypto_router

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup код
    print("🚀 Крипто-модуль мультибанка запущен!")
    print("📊 Доступные эндпоинты:")
    print("   - /api/crypto/buy - Покупка крипты")
    print("   - /api/crypto/sell - Продажа крипты")
    print("   - /api/crypto/deposit - Ввод средств")
    print("   - /api/crypto/withdraw - Вывод средств")
    print("   - /docs - Документация API")
    yield

app = FastAPI(
    title="Мультибанк Крипто Модуль",
    description="API для работы с синтетической криптовалютой",
    version="1.0.0",
    lifespan=lifespan
)

# Подключаем крипто-роуты
app.include_router(crypto_router)

@app.get("/")
async def root():
    return {
        "message": "Мультибанк Крипто Модуль запущен",
        "version": "1.0.0",
        "endpoints": {
            "crypto": "/api/crypto",
            "docs": "/docs"
        }
    }

if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8002,
        reload=True,
        log_level="info"
    )