from .baseline import generate_signals_baseline
from .tier1 import generate_signals_tier1

STRATEGIES = {
    "baseline": generate_signals_baseline,
    "tier1":    generate_signals_tier1,
}

def get_strategy(name: str):
    if name not in STRATEGIES:
        raise ValueError(f"Unknown strategy '{name}'. Available: {list(STRATEGIES.keys())}")
    return STRATEGIES[name]