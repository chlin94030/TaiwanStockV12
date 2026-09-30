"""
Taiwan Alpha Radar V8.3 Presentation Helpers.
Plain-text Summary Generation.
"""
from __future__ import annotations

def plain_summary(f: dict) -> str:
    if not f or not isinstance(f, dict) or not f.get("estimate_available"):
        return "本標的目前局部歷史數據不足，僅供基礎觀察。"
    
    strat = f.get("strategy", {})
    ev = strat.get("mean", 0.0) * 100
    es10 = strat.get("expected_shortfall10_loss", 0.0) * 100
    alpha = f.get("alpha_mean", 0.0) * 100
    
    return f"歷史相似結構扣除成本後，推估淨效益 (EV) 約為 {ev:+.1f}%（相對超額 Alpha {alpha:+.1f}%）；若遇到最差 10% 極端狀況，平均損失約為 {es10:.1f}%。"