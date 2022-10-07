from .strategy_1 import calculate_strategy_1
from .strategy_2 import calculate_strategy_2


STRATEGY = {
    'strategy_1': calculate_strategy_1,
    'strategy_2': calculate_strategy_2
}


def get_strategy(key: str):
    return STRATEGY.get(key)