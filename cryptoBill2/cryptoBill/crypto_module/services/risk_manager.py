from typing import Dict
import logging
from datetime import datetime
from ..config.settings import config

logger = logging.getLogger(__name__)


class RiskManager:
    def __init__(self):
        self.daily_volume = 0.0
        self.net_exposure = 0.0
        self.last_reset = datetime.now()
        self.client_positions: Dict[str, float] = {}

    def check_trade_limits(self, user_id: str, amount: float, operation: str) -> bool:
        if self.daily_volume + amount > config.RISK_LIMITS['max_daily_volume']:
            logger.warning(f"Daily volume limit exceeded")
            return False

        current_position = self.client_positions.get(user_id, 0.0)
        if operation == 'buy' and current_position + amount > config.MAX_CLIENT_BALANCE:
            logger.warning(f"Client limit exceeded for {user_id}")
            return False

        if operation == 'buy':
            new_exposure = self.net_exposure + amount
        else:
            new_exposure = self.net_exposure - amount

        if abs(new_exposure) > config.RISK_LIMITS['max_net_exposure']:
            logger.warning(f"Net exposure limit exceeded")
            return False

        return True

    def update_metrics(self, user_id: str, amount: float, operation: str):
        self.daily_volume += amount
        current = self.client_positions.get(user_id, 0.0)

        if operation == 'buy':
            self.net_exposure += amount
            self.client_positions[user_id] = current + amount
        else:
            self.net_exposure -= amount
            self.client_positions[user_id] = current - amount

    def get_risk_report(self) -> Dict:
        client_imbalance = self._calculate_client_imbalance()
        return {
            'daily_volume': self.daily_volume,
            'net_exposure': self.net_exposure,
            'client_imbalance': client_imbalance,
            'active_clients': len(self.client_positions)
        }

    def _calculate_client_imbalance(self) -> float:
        if not self.client_positions:
            return 0.5
        total_long = sum(pos for pos in self.client_positions.values() if pos > 0)
        total_short = abs(sum(pos for pos in self.client_positions.values() if pos < 0))
        if total_long + total_short == 0:
            return 0.5
        return total_long / (total_long + total_short)