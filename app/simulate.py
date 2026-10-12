"""Simulated IoT sensor readings and maintenance history."""
import numpy as np
import pandas as pd

FAILURE_RAMP_HOURS = 48
LABEL_HORIZON_HOURS = 24


def simulate_sensors(n_assets=8, hours=24 * 21, seed=42):
    """Hourly temperature/vibration/pressure per asset.

    Roughly half the assets degrade towards a failure: temperature and
    vibration drift upward over the final FAILURE_RAMP_HOURS. Raw data also
    contains missing values, duplicates and spikes for the cleaning step.
    """
    rng = np.random.default_rng(seed)
    ts = pd.date_range("2025-02-01", periods=hours, freq="h")
    frames = []
    for i in range(n_assets):
        t = np.arange(hours)
        temp = 60 + 5 * np.sin(2 * np.pi * t / 24) + rng.normal(0, 1, hours)
        vib = 2.0 + 0.2 * rng.normal(size=hours)
        pres = 100 + rng.normal(0, 2, hours)
        fails = i % 2 == 1
        hours_to_fail = np.full(hours, np.inf)
        if fails:
            fail_at = int(rng.integers(hours // 2, hours - 1))
            ramp = np.clip((t - (fail_at - FAILURE_RAMP_HOURS)) / FAILURE_RAMP_HOURS, 0, 1)
            ramp[t > fail_at] = 0  # asset repaired after failure
            temp += 25 * ramp
            vib += 3 * ramp
            hours_to_fail = np.where(t <= fail_at, fail_at - t, np.inf)
        df = pd.DataFrame({
            "timestamp": ts, "asset_id": f"A{i + 1:02d}",
            "temperature": temp, "vibration": vib, "pressure": pres,
            "fail_within_24h": (hours_to_fail <= LABEL_HORIZON_HOURS).astype(int),
        })
        frames.append(df)
    raw = pd.concat(frames, ignore_index=True)

    n = len(raw)
    for col in ["temperature", "vibration", "pressure"]:
        raw.loc[rng.choice(n, n // 50, replace=False), col] = np.nan
    spikes = rng.choice(n, n // 200, replace=False)
    raw.loc[spikes, "temperature"] += rng.choice([-1, 1], len(spikes)) * 200
    raw = pd.concat([raw, raw.sample(n // 100, random_state=seed)], ignore_index=True)
    return raw.sample(frac=1, random_state=seed).reset_index(drop=True)


def simulate_maintenance(n_assets=8, seed=42):
    rng = np.random.default_rng(seed + 1)
    types = ["inspection", "lubrication", "part_replacement", "calibration"]
    rows = []
    for i in range(n_assets):
        for d in pd.to_datetime("2025-02-01") + pd.to_timedelta(
                np.sort(rng.integers(0, 180, rng.integers(3, 8))), unit="D"):
            rows.append({
                "asset_id": f"A{i + 1:02d}", "date": d,
                "type": rng.choice(types),
                "downtime_hours": round(float(rng.gamma(2, 2)), 1),
                "cost": round(float(rng.gamma(3, 250)), 2),
            })
    return pd.DataFrame(rows)
