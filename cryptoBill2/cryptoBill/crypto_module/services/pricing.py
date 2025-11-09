import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import requests
import time
import statistics
from typing import Dict, Tuple
import logging
from datetime import datetime

logger = logging.getLogger(__name__)


class RealTimePriceOracle:
    def __init__(self):
        self.last_prices: Dict[str, float] = {}
        self.price_history: Dict[str, list] = {}
        self.last_update: Dict[str, float] = {}
        self.cache_ttl = 30  # Увеличим кеш до 30 секунд

        # Приоритетные API (сначала бесплатные и надежные)
        self.exchanges = [
            self._get_coingecko_price,  # Самый надежный бесплатный
            self._get_binance_price,  # Основная биржа
            self._get_coinbase_price,  # Резервный
            self._get_mexc_price,  # Альтернативная биржа
            self._get_gateio_price  # Еще одна альтернатива
        ]

        self._initialize_prices()

    def _initialize_prices(self):
        """Инициализирует начальные цены"""
        for symbol in ['BTC', 'ETH']:
            price = self._get_real_time_price_sync(symbol)
            if symbol not in self.price_history:
                self.price_history[symbol] = []
            self.price_history[symbol].append(price)
            print(f"💰 Инициализирована цена {symbol}: ${price:,.2f}")

    def _get_real_time_price_sync(self, symbol: str) -> float:
        """Получает реальную цену с приоритетом на рабочие API"""
        prices = []

        for exchange_func in self.exchanges:
            try:
                price = exchange_func(symbol)
                if price and self._is_valid_price(price, symbol):
                    prices.append(price)
                    print(f"✅ {exchange_func.__name__} для {symbol}: ${price:,.2f}")
                    if len(prices) >= 2:  # Хватит 2 источников
                        break
            except Exception as e:
                print(f"❌ {exchange_func.__name__} ошибка: {e}")

        if prices:
            final_price = statistics.median(prices)
            print(f"🎯 ФИНАЛЬНАЯ ЦЕНА {symbol}: ${final_price:,.2f} из {len(prices)} источников")
            self.last_prices[symbol] = final_price
            self.last_update[symbol] = time.time()
            return final_price

        # Если все API упали, используем реалистичные цены
        print(f"⚠️ ВСЕ API недоступны для {symbol}, используем реалистичные цены")
        return self._get_realistic_fallback_price(symbol)

    def _get_coingecko_price(self, symbol: str) -> float:
        """CoinGecko API - самый надежный бесплатный источник"""
        try:
            # Маппинг символов на CoinGecko ID
            coin_mapping = {
                'BTC': 'bitcoin',
                'ETH': 'ethereum',
                'USDT': 'tether'
            }

            coin_id = coin_mapping.get(symbol)
            if not coin_id:
                return self._get_fallback_price(symbol)

            url = f"https://api.coingecko.com/api/v3/simple/price?ids={coin_id}&vs_currencies=usd"

            response = requests.get(url, timeout=10)
            response.raise_for_status()
            data = response.json()

            return data[coin_id]['usd']

        except Exception as e:
            raise Exception(f"CoinGecko: {e}")

    def _get_binance_price(self, symbol: str) -> float:
        """Binance API"""
        try:
            pair = f"{symbol}USDT"
            url = f"https://api.binance.com/api/v3/ticker/price?symbol={pair}"

            response = requests.get(url, timeout=10)
            response.raise_for_status()
            return float(response.json()['price'])

        except Exception as e:
            raise Exception(f"Binance: {e}")

    def _get_coinbase_price(self, symbol: str) -> float:
        """Coinbase API"""
        try:
            if symbol == 'USDT':
                return 1.0

            url = f"https://api.coinbase.com/v2/prices/{symbol}-USD/spot"
            response = requests.get(url, timeout=10)
            response.raise_for_status()
            return float(response.json()['data']['amount'])

        except Exception as e:
            raise Exception(f"Coinbase: {e}")

    def _get_mexc_price(self, symbol: str) -> float:
        """MEXC API - альтернативная биржа"""
        try:
            pair = f"{symbol}USDT"
            url = f"https://api.mexc.com/api/v3/ticker/price?symbol={pair}"

            response = requests.get(url, timeout=10)
            response.raise_for_status()
            return float(response.json()['price'])

        except Exception as e:
            raise Exception(f"MEXC: {e}")

    def _get_gateio_price(self, symbol: str) -> float:
        """Gate.io API - альтернативная биржа"""
        try:
            pair = f"{symbol}_USDT"
            url = f"https://api.gateio.ws/api/v4/spot/tickers?currency_pair={pair}"

            response = requests.get(url, timeout=10)
            response.raise_for_status()
            data = response.json()
            return float(data[0]['last'])

        except Exception as e:
            raise Exception(f"Gate.io: {e}")

    def _get_realistic_fallback_price(self, symbol: str) -> float:
        """Текущие реалистичные цены (обновляйте вручную)"""
        current_prices = {
            'BTC': 65000.0,  # ← ОБНОВИТЕ НА ТЕКУЩУЮ РЫНОЧНУЮ ЦЕНУ
            'ETH': 3500.0,  # ← ОБНОВИТЕ НА ТЕКУЩУЮ РЫНОЧНУЮ ЦЕНУ
            'USDT': 1.0
        }
        return current_prices.get(symbol, 1.0)

    # Остальные методы остаются без изменений
    def get_market_price(self, symbol: str) -> float:
        cache_key = symbol

        if (cache_key not in self.last_update or
                time.time() - self.last_update[cache_key] > self.cache_ttl):

            price = self._get_real_time_price_sync(symbol)
            if price:
                if symbol not in self.price_history:
                    self.price_history[symbol] = []
                self.price_history[symbol].append(price)
                if len(self.price_history[symbol]) > 100:
                    self.price_history[symbol].pop(0)
                return price

        return self.last_prices.get(cache_key, self._get_realistic_fallback_price(symbol))

    def calculate_spread(self, symbol: str, client_imbalance: float = 0.5) -> Tuple[float, float, float]:
        market_price = self.get_market_price(symbol)

        base_spread = 0.02
        volatility = self._calculate_volatility(symbol)
        volatility_adjustment = min(volatility * 0.5, 0.03)
        imbalance_adjustment = abs(client_imbalance - 0.5) * 0.02

        total_spread = base_spread + volatility_adjustment + imbalance_adjustment
        total_spread = min(total_spread, 0.05)

        buy_price = market_price * (1 + total_spread / 2)
        sell_price = market_price * (1 - total_spread / 2)

        return buy_price, sell_price, total_spread

    def _calculate_volatility(self, symbol: str) -> float:
        if symbol not in self.price_history or len(self.price_history[symbol]) < 5:
            return 0.01

        prices = self.price_history[symbol][-10:]
        if len(prices) < 2:
            return 0.01

        min_price = min(prices)
        max_price = max(prices)
        avg_price = sum(prices) / len(prices)

        if avg_price > 0:
            return (max_price - min_price) / avg_price * 0.1
        else:
            return 0.01

    def _is_valid_price(self, price: float, symbol: str) -> bool:
        expected_ranges = {
            'BTC': (10000, 150000),
            'ETH': (500, 10000),
            'USDT': (0.95, 1.05)
        }

        if symbol in expected_ranges:
            min_p, max_p = expected_ranges[symbol]
            return min_p <= price <= max_p
        return True

    def get_price_info(self, symbol: str) -> Dict:
        current_price = self.get_market_price(symbol)
        buy_price, sell_price, spread = self.calculate_spread(symbol)

        return {
            'symbol': symbol,
            'market_price': round(current_price, 2),
            'buy_price': round(buy_price, 2),
            'sell_price': round(sell_price, 2),
            'spread_percent': round(spread * 100, 2),
            'price_change_24h': round(self.get_price_change_24h(symbol), 2),
            'volatility': round(self._calculate_volatility(symbol) * 100, 2),
            'last_updated': datetime.now().isoformat()
        }

    def get_price_change_24h(self, symbol: str) -> float:
        if symbol not in self.price_history or len(self.price_history[symbol]) < 2:
            return 0.0

        current = self.price_history[symbol][-1]
        old_price = self.price_history[symbol][0] if len(self.price_history[symbol]) > 50 else \
        self.price_history[symbol][0]

        return ((current - old_price) / old_price) * 100