"""
Taiwan Alpha Radar V8.3 Input Validation Layer.
CSV Data Unit Checks & Sanitization.
"""
from __future__ import annotations

from pathlib import Path
import io
import pandas as pd

def publish_inputs(data_dir: Path, uploads: dict, units_mode: str = "decimal", acknowledge_extremes: bool = False):
    for filename, content in uploads.items():
        df = pd.read_csv(io.BytesIO(content))
        
        if units_mode == "percent_points":
            for col in ["revenue_yoy", "eps_yoy", "roe"]:
                if col in df.columns:
                    df[col] = df[col] / 100.0
        
        num_cols = df.select_dtypes(include=["number"]).columns
        has_extremes = (df[num_cols].abs() > 5.0).any().any()
        
        if has_extremes and not acknowledge_extremes:
            raise ValueError("數據包含超過 500% (>5.0) 的極端值，請確認單位是否為小數，並勾選手動確認。")
        
        target_path = data_dir / filename
        df.to_csv(target_path, index=False)