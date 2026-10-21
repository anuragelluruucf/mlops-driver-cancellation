"""Feature definitions, mirroring strategic_prediction_models.py in Anurag's research repo."""
PEAK_HOURS = {12, 13, 14, 18, 19, 20, 21}

# Raw inputs the API accepts (interaction features are derived).
RAW_FEATURES = [
    "lifetime_order_count", "bike_issue_rate", "post_pickup_rate",
    "total_distance", "first_mile_distance", "last_mile_distance",
    "session_time", "hour", "time_to_accept", "time_to_pickup",
]
FEATURES = RAW_FEATURES[:8] + ["is_peak_hour", "time_to_accept", "time_to_pickup",
                               "distance_x_peak", "distance_x_session"]
LABEL = "is_strategic_order"


def add_derived(df):
    df = df.copy()
    df["is_peak_hour"] = df["hour"].isin(PEAK_HOURS).astype(int)
    df["distance_x_peak"] = df["total_distance"] * df["is_peak_hour"]
    df["distance_x_session"] = df["total_distance"] * df["session_time"]
    return df[FEATURES].fillna(0)
