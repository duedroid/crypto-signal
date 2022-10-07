from .signal import (
    binance_future_signal_4h,
    binance_future_signal_1d,
    calculate_strategy,
)
from .klines import save_klines


TASKS = [
    binance_future_signal_4h,
    binance_future_signal_1d,
    calculate_strategy,
    save_klines,
]