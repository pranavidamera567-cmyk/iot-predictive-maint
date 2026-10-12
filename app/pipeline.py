"""Data cleaning and feature engineering."""
import numpy as np
import pandas as pd

SENSORS = ["temperature", "vibration", "pressure"]


def clean(raw):
    df = raw.drop_duplicates(["timestamp", "asset_id"]).sort_values(["asset_id", "timestamp"]).copy()
    for col in SENSORS:
        grp = df.groupby("asset_id")[col]
        q1, q3 = grp.transform(lambda s: s.quantile(0.25)), grp.transform(lambda s: s.quantile(0.75))
        iqr = q3 - q1
        df.loc[(df[col] < q1 - 5 * iqr) | (df[col] > q3 + 5 * iqr), col] = np.nan
        df[col] = df.groupby("asset_id")[col].transform(lambda s: s.interpolate(limit_direction="both"))
    return df.reset_index(drop=True)


def add_features(df, window=6):
    out = df.copy()
    g = out.groupby("asset_id")
    for col in ["temperature", "vibration"]:
        out[f"{col}_mean_{window}h"] = g[col].transform(lambda s: s.rolling(window, min_periods=1).mean())
        out[f"{col}_std_{window}h"] = g[col].transform(lambda s: s.rolling(window, min_periods=2).std()).fillna(0)
        out[f"{col}_delta"] = g[col].diff().fillna(0)
    out["temp_vib_ratio"] = out["temperature"] / out["vibration"].clip(lower=0.1)
    return out


def feature_columns(df):
    return [c for c in df.columns if c in SENSORS or c.endswith(("h", "_delta")) or c == "temp_vib_ratio"
            if c not in ("timestamp", "asset_id", "fail_within_24h")]
