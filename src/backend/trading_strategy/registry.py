from .baseline import generate_signals_baseline
from .tier1 import generate_signals_tier1
from .tier_sentiment import generate_signals_sentiment

STRATEGIES = {
    "baseline": generate_signals_baseline,
    "tier_1":    generate_signals_tier1,
    "tier_sentiment": generate_signals_sentiment,
}

def get_strategy(name: str):
    if name not in STRATEGIES:
        raise ValueError(f"Unknown strategy '{name}'. Available: {list(STRATEGIES.keys())}")
    return STRATEGIES[name]