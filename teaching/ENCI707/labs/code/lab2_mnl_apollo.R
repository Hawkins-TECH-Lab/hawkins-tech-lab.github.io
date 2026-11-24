# ENCI707 Lab 2 starter: MNL mode choice with Apollo.
#
# Same base model as lab2_mnl_biogeme.py, so you can compare results directly.
#
# Data: lab2_hbw_2023.csv (posted on D2L). One row per home-based work trip.
#   CHOICE: 1 drive, 2 transit, 3 walk, 4 bike
#   time_*/cost_*/av_*: imputed level of service and availability per mode
#   veh, hhsize, inc_low, inc_high, age_lt35, age_ge55: person/household traits

library(apollo)

apollo_initialise()

apollo_control <- list(
  modelName  = "lab2_mnl_base",
  modelDescr = "ENCI707 Lab 2: base MNL, PSRC home-based work trips",
  indivID    = "person_id",   # some people report several work trips
  outputDirectory = "output"
)

database <- read.csv("lab2_hbw_2023.csv")

# Starting values; drive is the reference alternative.
apollo_beta <- c(
  asc_drive   = 0,
  asc_transit = 0,
  asc_walk    = 0,
  asc_bike    = 0,
  b_time      = 0,
  b_cost      = 0,
  b_veh_transit = 0
)
apollo_fixed <- c("asc_drive")

apollo_inputs <- apollo_validateInputs()

apollo_probabilities <- function(apollo_beta, apollo_inputs,
                                 functionality = "estimate") {
  apollo_attach(apollo_beta, apollo_inputs)
  on.exit(apollo_detach(apollo_beta, apollo_inputs))

  P <- list()

  V <- list()
  V[["drive"]]   <- asc_drive   + b_time * time_drive   + b_cost * cost_drive
  V[["transit"]] <- asc_transit + b_time * time_transit + b_cost * cost_transit +
                    b_veh_transit * veh
  V[["walk"]]    <- asc_walk    + b_time * time_walk
  V[["bike"]]    <- asc_bike    + b_time * time_bike

  mnl_settings <- list(
    alternatives = c(drive = 1, transit = 2, walk = 3, bike = 4),
    avail        = list(drive = av_drive, transit = av_transit,
                        walk = av_walk, bike = av_bike),
    choiceVar    = CHOICE,
    utilities    = V
  )

  P[["model"]] <- apollo_mnl(mnl_settings, functionality)
  # Trips from the same person are not independent: this gives panel-robust SEs.
  P <- apollo_panelProd(P, apollo_inputs, functionality)
  P <- apollo_prepareProb(P, apollo_inputs, functionality)
  return(P)
}

model <- apollo_estimate(apollo_beta, apollo_fixed,
                         apollo_probabilities, apollo_inputs)
apollo_modelOutput(model)

# Value of travel time savings ($/hour) = 60 * b_time / b_cost
deltaMethod_settings <- list(expression = c(VTTS = "60 * b_time / b_cost"))
apollo_deltaMethod(model, deltaMethod_settings)
