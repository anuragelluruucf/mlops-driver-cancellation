"""SYNTHETIC data generator.

The original research used a proprietary dataset (447,187 orders) that is NOT public and
not in the repo. This script creates a clearly labeled synthetic sample with the same
feature schema so the pipeline can run end to end. Metrics on it say nothing about the
real-world model.
"""
import argparse
import numpy as np
import pandas as pd


def generate(n_orders=60000, n_riders=3000, seed=42):
    rng = np.random.default_rng(seed)
    strategic = rng.random(n_riders) < 0.05          # latent "strategic rider" trait
    rider = rng.integers(0, n_riders, n_orders)
    s = strategic[rider]
    hour = rng.choice(np.arange(8, 24), n_orders)
    peak = np.isin(hour, [12, 13, 14, 18, 19, 20, 21])
    fm = rng.gamma(2.0, 0.8, n_orders)
    lm = rng.gamma(2.5, 1.4, n_orders)
    session = rng.gamma(2.0, 90, n_orders)
    df = pd.DataFrame({
        "order_seq": np.arange(n_orders),               # time order for temporal split
        "rider_id": rider,
        "lifetime_order_count": rng.poisson(np.where(s, 60, 120)) + 1,
        "bike_issue_rate": np.clip(rng.beta(1, 12, n_orders) + s * rng.beta(2, 4, n_orders), 0, 1),
        "post_pickup_rate": np.clip(rng.beta(2, 5, n_orders) + s * 0.3, 0, 1),
        "total_distance": fm + lm, "first_mile_distance": fm, "last_mile_distance": lm,
        "session_time": session, "hour": hour,
        "time_to_accept": rng.gamma(1.5, 1.2, n_orders),
        "time_to_pickup": rng.gamma(3.0, 4.0, n_orders),
    })
    logit = (-6.2 + 2.6 * s + 0.12 * (fm + lm) + 0.5 * peak * s + 0.002 * session
             + rng.normal(0, 0.5, n_orders))
    df["is_strategic_order"] = (rng.random(n_orders) < 1 / (1 + np.exp(-logit))).astype(int)
    return df


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default="data/synthetic_orders.csv")
    ap.add_argument("--n", type=int, default=60000)
    ap.add_argument("--seed", type=int, default=42)
    a = ap.parse_args()
    df = generate(a.n, seed=a.seed)
    df.to_csv(a.out, index=False)
    print(f"wrote {len(df):,} SYNTHETIC rows -> {a.out}; positive rate {df.is_strategic_order.mean():.2%}")
