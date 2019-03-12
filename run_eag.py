import waterbalans as wb
import pandas as pd

# Basisgegevens
# -------------
# Naam en ID van gebied
eag_id = "3"
eag_name = "2140-EAG-3"

# Begin en eindtijd simulatie
tmin = "2000"
tmax = "2015"

# Inlezen gegevens
# ----------------
# bestand met deelgebieden en oppervlaktes:
deelgebieden = pd.read_csv(
    r"./data/input_csv/opp_1207_2140-EAG-3.csv", delimiter=";")
# bestand met tijdreeksen, b.v. neerslag/verdamping:
tijdreeksen = pd.read_csv(
    r"./data/input_csv/reeks_1207_2140-EAG-3.csv", delimiter=";")
# bestand met parameters per deelgebied
parameters = pd.read_csv(
    r"./data/input_csv/param_1207_2140-EAG-3.csv", delimiter=";")

# Model
# -----
# Maak bakjes model
e = wb.create_eag(eag_id, eag_name, deelgebieden)

# Voeg tijdreeksen toe
e.add_series(tijdreeksen, tmin=tmin, tmax=tmax)

# Simuleer waterbalans met parameters
e.simulate(parameters, tmin=tmin, tmax=tmax)

# Plot waterbalans op maandbasis
e.plot.aggregated(tmin=tmin, tmax=tmax)
