import logging
from typing import Dict
from ..config.settings import config

logger = logging.getLogger(__name__)


class HedgingService:
    def __init__(self):
        self.hedge_positions: Dict[str, float] = {}
        self.total_hedged_value = 0.0

    def calculate_hedge_need(self, net_exposure: float, current_prices: Dict[str, float]) -> Dict[str, float]:
        hedge_needs = {}
        btc_exposure = net_exposure * 0.6
        eth_exposure = net_exposure * 0.4

        if 'BTC' in current_prices:
            hedge_needs['BTC'] = btc_exposure / current_prices['BTC']
        if 'ETH' in current_prices:
            hedge_needs['ETH'] = eth_exposure / current_prices['ETH']

        return hedge_needs

    def execute_hedge(self, hedge_needs: Dict[str, float], current_prices: Dict[str, float]):
        try:
            for symbol, units in hedge_needs.items():
                if symbol in current_prices:
                    current_position = self.hedge_positions.get(symbol, 0.0)
                    hedge_difference = units - current_position

                    if abs(hedge_difference) > 0.001:
                        logger.info(f"Hedging {symbol}: {hedge_difference:.6f} units")
                        self.hedge_positions[symbol] = units
                        self._log_hedge_transaction(symbol, hedge_difference, current_prices[symbol])

            self._update_total_hedged_value(current_prices)
        except Exception as e:
            logger.error(f"Hedging execution error: {e}")

    def _log_hedge_transaction(self, symbol: str, units: float, price: float):
        action = "BUY" if units > 0 else "SELL"
        logger.info(f"HEDGE {action} | {symbol} | Units: {abs(units):.6f}")

    def _update_total_hedged_value(self, current_prices: Dict[str, float]):
        total = 0.0
        for symbol, units in self.hedge_positions.items():
            if symbol in current_prices:
                total += units * current_prices[symbol]
        self.total_hedged_value = total

    def get_hedge_report(self) -> Dict:
        return {
            'positions': self.hedge_positions,
            'total_hedged_value': self.total_hedged_value
        }