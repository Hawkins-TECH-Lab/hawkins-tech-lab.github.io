"""ENCI707 Lab 2 starter: MNL mode choice with Biogeme.

Tested with biogeme 3.3.2. Install with:  pip install biogeme "tomlkit<0.14"

Data: lab2_hbw_2023.csv (posted on D2L). One row per home-based work trip.
  CHOICE: 1 drive, 2 transit, 3 walk, 4 bike
  time_*/cost_*/av_*: imputed level of service and availability per mode
  veh, hhsize, inc_low, inc_high, age_lt35, age_ge55: person/household traits

This is a deliberately minimal base model. Your job in the lab is to improve
it, interpret it, and test it.
"""

import pandas as pd

import biogeme.biogeme as bio
from biogeme import models
from biogeme.database import Database
from biogeme.expressions import Beta, Variable
from biogeme.results_processing import get_pandas_estimated_parameters

df = pd.read_csv("lab2_hbw_2023.csv")
database = Database("lab2", df.select_dtypes("number"))

# ---- Variables --------------------------------------------------------------
CHOICE = Variable("CHOICE")
time = {m: Variable(f"time_{m}") for m in ("drive", "transit", "walk", "bike")}
cost = {m: Variable(f"cost_{m}") for m in ("drive", "transit")}
av = {1: Variable("av_drive"), 2: Variable("av_transit"),
      3: Variable("av_walk"), 4: Variable("av_bike")}
veh = Variable("veh")

# ---- Parameters: Beta(name, start, lower, upper, fixed) -------------------------
ASC_TRANSIT = Beta("ASC_TRANSIT", 0, None, None, 0)
ASC_WALK = Beta("ASC_WALK", 0, None, None, 0)
ASC_BIKE = Beta("ASC_BIKE", 0, None, None, 0)
B_TIME = Beta("B_TIME", 0, None, None, 0)        # generic travel time (min)
B_COST = Beta("B_COST", 0, None, None, 0)        # generic cost ($)
B_VEH_TRANSIT = Beta("B_VEH_TRANSIT", 0, None, None, 0)

# ---- Utilities (drive is the reference alternative) -------------------------
V = {
    1: B_TIME * time["drive"] + B_COST * cost["drive"],
    2: ASC_TRANSIT + B_TIME * time["transit"] + B_COST * cost["transit"]
       + B_VEH_TRANSIT * veh,
    3: ASC_WALK + B_TIME * time["walk"],
    4: ASC_BIKE + B_TIME * time["bike"],
}

logprob = models.loglogit(V, av, CHOICE)

the_biogeme = bio.BIOGEME(database, logprob,
                          generate_html=False, generate_yaml=False)
the_biogeme.model_name = "lab2_mnl_base"
results = the_biogeme.estimate()

print(results.short_summary())
print(get_pandas_estimated_parameters(estimation_results=results))

# Value of travel time savings ($/hour) = 60 * B_TIME / B_COST
b = results.get_beta_values()
print(f"VTTS: ${60 * b['B_TIME'] / b['B_COST']:.2f} per hour")
