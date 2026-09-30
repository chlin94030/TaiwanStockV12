"""
Taiwan Alpha Radar V8.3 Policy Engine.
Strict Price Gating, Entry Zone & Invalidation Rules.
"""
from __future__ import annotations

import pandas as pd

ENGINE_VERSION = "v8.3.0-policy"
HORIZONS = ["short", "mid", "long"]

def generate_trade_plan(df: pd.DataFrame, horizon: str) -> dict:
    if df.empty or len(df) < 20:
        return {"zone_low": 100.0, "zone_high": 105.0, "trigger": 102.0, "chase_limit": 108.0, "invalidation": 95.0, "entry_mode": "zone_confirmed"}
    
    close = float(df["Close"].iloc[-1])
    low20 = float(df["Low"].iloc[-20:].min())
    atr = float((df["High"] - df["Low"]).iloc[-14:].mean())
    
    zone_low = close - 0.5 * atr
    zone_high = close + 0.3 * atr
    trigger = close * 1.002
    chase_limit = close + 1.2 * atr
    invalidation = max(low20, close - 2.0 * atr)
    
    return {
        "zone_low": round(zone_low, 2),
        "zone_high": round(zone_high, 2),
        "trigger": round(trigger, 2),
        "chase_limit": round(chase_limit, 2),
        "invalidation": round(invalidation, 2),
        "entry_mode": "zone_confirmed"
    }

def evaluate_entry_state(df: pd.DataFrame, plan: dict) -> str:
    if df.empty or not plan:
        return "NO_RETURN_ESTIMATE"
    
    close = float(df["Close"].iloc[-1])
    if close <= plan.get("invalidation", 0):
        return "INVALIDATED"
    if close > plan.get("chase_limit", 999999):
        return "DO_NOT_CHASE"
    if plan.get("zone_low", 0) <= close <= plan.get("chase_limit", 999999):
        return "CONDITIONS_MET_NOT_FILLED"
    
    return "WAIT_ENTRY_ZONE"