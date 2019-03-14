import waterbalans as wb
import pandas as pd

# Basisgegevens
# -------------
# Naam en ID van gebied
gaf_id = "2110"
gaf_name = "2110-GAF"

# Begin en eindtijd simulatie
tmin = "2000"
tmax = "2012-12-31"

# Inlezen gegevens
# ----------------
# bestand met deelgebieden en oppervlaktes:
deelgebieden = pd.read_csv(
    r"./data/input_csv/opp_1557_2110-GAF.csv", delimiter=";")
# bestand met tijdreeksen, b.v. neerslag/verdamping:
tijdreeksen = pd.read_csv(
    r"./data/input_csv/reeks_1557_2110-GAF.csv", delimiter=";")
# bestand met parameters per deelgebied
parameters = pd.read_csv(
    r"./data/input_csv/param_1557_2110-GAF.csv", delimiter=";")
parameters.rename(columns={"ParamCode": "Code"}, inplace=True)
# extra timeseries
series = pd.read_csv(
    r"./data/input_csv/series_1557_2110-GAF.csv", delimiter=";",
    index_col=[1], parse_dates=True)

# Model
# -----
# Maak bakjes model
g = wb.create_gaf(gaf_id, gaf_name, gafbuckets=deelgebieden)

# Voeg tijdreeksen toe
g.add_series(tijdreeksen, tmin=tmin, tmax=tmax)

# Voeg extra tijdreeksen toe
wb.utils.add_timeseries_to_obj(g, series, tmin=tmin, tmax=tmax)

# Simuleer waterbalans met parameters
g.simulate(parameters, tmin=tmin, tmax=tmax)

# Plot waterbalans op maandbasis voor eag
e, = g.get_eags()
e.plot.aggregated(tmin=tmin, tmax=tmax)
