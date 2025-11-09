from fastapi import APIRouter, HTTPException
from typing import List
from ..services.trading import CryptoTradingService
from ..models.transaction import Transaction

router = APIRouter(prefix="/api/crypto", tags=["crypto"])

# Инициализация сервиса
trading_service = CryptoTradingService()


@router.post("/buy")
async def buy_crypto(user_id: str, crypto: str, amount: float):
    """Эндпоинт для покупки криптовалюты"""
    result = trading_service.buy_crypto(user_id, crypto, amount)
    if not result['success']:
        raise HTTPException(status_code=400, detail=result['error'])
    return result


@router.post("/sell")
async def sell_crypto(user_id: str, crypto: str, units: float):
    """Эндпоинт для продажи криптовалюты"""
    result = trading_service.sell_crypto(user_id, crypto, units)
    if not result['success']:
        raise HTTPException(status_code=400, detail=result['error'])
    return result


@router.post("/deposit")
async def deposit_funds(
        user_id: str,
        amount: float,
        payment_method: str = "bank_transfer"
):
    """Ввод средств на крипто-счет"""
    result = trading_service.deposit(user_id, amount, payment_method)
    if not result['success']:
        raise HTTPException(status_code=400, detail=result['error'])
    return result


@router.post("/withdraw")
async def withdraw_funds(
        user_id: str,
        amount: float,
        destination: str = "bank_account"
):
    """Вывод средств с крипто-счета"""
    result = trading_service.withdraw(user_id, amount, destination)
    if not result['success']:
        raise HTTPException(status_code=400, detail=result['error'])
    return result


@router.get("/portfolio/{user_id}")
async def get_portfolio(user_id: str):
    """Получение портфеля пользователя"""
    portfolio = trading_service.get_portfolio(user_id)
    if not portfolio:
        raise HTTPException(status_code=404, detail="User not found")
    return portfolio


@router.get("/transactions/{user_id}")
async def get_transactions(user_id: str, limit: int = 50):
    """История транзакций пользователя"""
    transactions = trading_service.get_transaction_history(user_id, limit)
    return {
        'user_id': user_id,
        'transactions': [
            {
                'id': tx.transaction_id,
                'type': tx.type.value,
                'amount': tx.amount,
                'currency': tx.currency,
                'status': tx.status.value,
                'created_at': tx.created_at.isoformat(),
                'description': tx.description
            }
            for tx in transactions
        ]
    }


@router.get("/balance/{user_id}")
async def get_balance(user_id: str):
    """Полный баланс пользователя (фиат + крипто)"""
    portfolio = trading_service.get_portfolio(user_id)
    if not portfolio:
        raise HTTPException(status_code=404, detail="User not found")

    return {
        'user_id': user_id,
        'fiat_balance': portfolio.get('fiat_balance', 0),
        'total_crypto_value': portfolio.get('total_crypto_value', 0),
        'total_balance': portfolio.get('fiat_balance', 0) + portfolio.get('total_crypto_value', 0),
        'crypto_allocations': portfolio.get('crypto_allocations', {})
    }


@router.post("/close-position/{user_id}/{crypto}")
async def close_position(user_id: str, crypto: str):
    """Закрытие всей позиции по криптовалюте"""
    result = trading_service.close_position(user_id, crypto)
    if not result['success']:
        raise HTTPException(status_code=400, detail=result['error'])
    return result


@router.get("/prices/{crypto}")
async def get_current_prices(crypto: str):
    """Получение текущих цен"""
    try:
        buy_price, sell_price, spread = trading_service.price_oracle.calculate_spread(crypto)
        return {
            'crypto': crypto,
            'buy_price': buy_price,
            'sell_price': sell_price,
            'spread_percent': spread * 100
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/system-status")
async def get_system_status():
    """Получение статуса системы (для админов)"""
    return trading_service.get_system_report()

@router.get("/price-info/{crypto}")
async def get_price_info(crypto: str):
    """Подробная информация о цене криптовалюты"""
    try:
        price_info = trading_service.price_oracle.get_price_info(crypto)
        return price_info
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))