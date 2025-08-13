def decide_entry(structure, divergence, liquidity, volume):
    signal = {"action": "hold"}

    if all([structure['long'], divergence['long'], liquidity['long'], volume['long']]):
        signal = {
            "action": "buy",
            "direction": "long",
            "reason": "Market Structure + Divergence + Liquidity Grab + Volume"
        }

    elif all([structure['short'], divergence['short'], liquidity['short'], volume['short']]):
        signal = {
            "action": "sell",
            "direction": "short",
            "reason": "Market Structure + Divergence + Liquidity Grab + Volume"
        }

    return signal
