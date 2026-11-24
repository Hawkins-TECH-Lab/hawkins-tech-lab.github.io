"""INSTRUCTOR SCRIPT: build the shared Lab 2 estimation file from PSRC HTS data.

Students receive the output (lab2_hbw_2023.csv) so everyone estimates on the
same data. Run once per term:

    python prepare_lab2.py --hh hh.csv --person person.csv --trip trip.csv

The PSRC public files use text labels (e.g. "Drive", "Home"), which is what this
script matches on. Check the labels against the codebook for the release you
download; edit LABELS below if they differ.

Level of service (LOS) for the alternatives is NOT in the survey: the trip table
records only the chosen mode. We impute time and cost for every mode from trip
distance using the assumptions in LOS. Imputing all modes the same way (rather
than using the observed duration for the chosen mode) avoids building the choice
into the explanatory variables. Students are asked to critique these assumptions.
"""

from __future__ import annotations

import argparse

import numpy as np
import pandas as pd

LABELS = {
    "home": "Home",
    "work": "Work",
    "modes": {"Drive": 1, "Transit": 2, "Walk": 3, "Bike": 4},
    "in_region": ["Trip origin in region", "Trip destination in region",
                  "Yes", 1, "1", True],
}

# Imputation assumptions. Distances are multiplied by CIRCUITY because PSRC
# distances for online-survey trips are straight-line.
CIRCUITY = 1.2
LOS = {
    #            speed_mph  fixed_min  cost_per_mile  fixed_cost  max_miles
    "drive":   dict(speed=25, fixed=4,  cpm=0.30, fixed_cost=0.00, max_mi=None),
    "transit": dict(speed=12, fixed=12, cpm=0.00, fixed_cost=2.75, max_mi=None),
    "walk":    dict(speed=3,  fixed=0,  cpm=0.00, fixed_cost=0.00, max_mi=3),
    "bike":    dict(speed=10, fixed=2,  cpm=0.00, fixed_cost=0.00, max_mi=10),
}

INCOME_LOW = {"Under $25,000", "$25,000-$49,999"}
INCOME_HIGH = {"$100,000 or more", "$100,000-$199,000", "$100,000-$199,999",
               "$200,000 or more"}


def vehicle_number(label) -> float:
    """'0 (no vehicles)' -> 0, '2 vehicles' -> 2, '10 or more vehicles' -> 10."""
    s = str(label).strip()
    num = s.split(" ")[0]
    return float(num) if num.isdigit() else np.nan


def build(hh: pd.DataFrame, person: pd.DataFrame, trip: pd.DataFrame,
          year: int = 2023) -> pd.DataFrame:
    t = trip[trip["survey_year"].astype(str) == str(year)].copy()
    t = t[(t["origin_purpose_cat"] == LABELS["home"])
          & (t["dest_purpose_cat"] == LABELS["work"])]
    t = t[t["o_in_region"].isin(LABELS["in_region"])
          & t["d_in_region"].isin(LABELS["in_region"])]
    t = t[t["mode_class_5"].isin(LABELS["modes"])]
    t = t[(t["distance_miles"] > 0.05) & (t["distance_miles"] < 60)]

    hh_cols = ["household_id", "hhsize", "vehicle_count", "hhincome_broad"]
    t = t.merge(hh[hh_cols], on="household_id", how="left")
    t = t.merge(person[["person_id", "age", "gender"]], on="person_id",
                how="left")

    out = pd.DataFrame({
        "person_id": t["person_id"].values,
        "trip_id": t["trip_id"].values,
        "CHOICE": t["mode_class_5"].map(LABELS["modes"]).astype(int).values,
        "dist_mi": (t["distance_miles"] * CIRCUITY).round(3).values,
        "veh": t["vehicle_count"].map(vehicle_number).values,
        "hhsize": pd.to_numeric(t["hhsize"].astype(str).str.extract(r"(\d+)")[0],
                                errors="coerce").values,
        "inc_low": t["hhincome_broad"].isin(INCOME_LOW).astype(int).values,
        "inc_high": t["hhincome_broad"].isin(INCOME_HIGH).astype(int).values,
        "age_lt35": t["age"].isin(["18-24 years", "25-34 years"]).astype(int).values,
        "age_ge55": t["age"].isin(["55-64 years", "65-74 years", "75-84 years",
                                   "85 years or older"]).astype(int).values,
        "weight": t["trip_weight"].values,
    })

    for m, p in LOS.items():
        out[f"time_{m}"] = (p["fixed"] + out["dist_mi"] / p["speed"] * 60).round(2)
        out[f"cost_{m}"] = (p["fixed_cost"] + p["cpm"] * out["dist_mi"]).round(2)
        out[f"av_{m}"] = 1 if p["max_mi"] is None else \
            (out["dist_mi"] <= p["max_mi"]).astype(int)

    # Keep only rows where the chosen alternative is available.
    chosen_av = out[["av_drive", "av_transit", "av_walk", "av_bike"]].to_numpy()
    out = out[chosen_av[np.arange(len(out)), out["CHOICE"] - 1] == 1]
    out = out.dropna(subset=["veh", "hhsize"])
    return out.reset_index(drop=True)


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--hh", required=True)
    ap.add_argument("--person", required=True)
    ap.add_argument("--trip", required=True)
    ap.add_argument("--year", type=int, default=2023)
    ap.add_argument("--out", default="lab2_hbw_2023.csv")
    a = ap.parse_args()
    df = build(pd.read_csv(a.hh, low_memory=False),
               pd.read_csv(a.person, low_memory=False),
               pd.read_csv(a.trip, low_memory=False), a.year)
    df.to_csv(a.out, index=False)
    print(f"{len(df)} home-based work trips written to {a.out}")
    print(df["CHOICE"].value_counts().sort_index()
          .rename({1: "drive", 2: "transit", 3: "walk", 4: "bike"}))


if __name__ == "__main__":
    main()
