import waterbalans as wb

""" DEMO 03: Update waterbalance with data from FEWS

Minimal example that updates a water balance with data from FEWS.

Author: D.A. Brakenhoff
Date: 11-04-2019

"""
# %% Import modules
# -----------------
import matplotlib as mpl
import pandas as pd

mpl.interactive(True)

starttijd = pd.datetime.now()

# Basisgegevens
# -------------
# Naam en ID van gebied
eag_id = "3"
eag_name = "2140-EAG-3"

# Begin en eindtijd simulatie
tmin = "1996"
tmax = "2019"

# %% Inlezen gegevens
# -------------------
# bestand met deelgebieden en oppervlaktes:
deelgebieden = pd.read_csv(r"../../data/input_csv/opp_60_2140-EAG-3.csv", delimiter=";")
# bestand met tijdreeksen, b.v. neerslag/verdamping:
tijdreeksen = pd.read_csv(
    r"../../data/input_csv/reeks_60_2140-EAG-3.csv", delimiter=";"
)
# bestand met parameters per deelgebied
parameters = pd.read_csv(r"../../data/input_csv/param_60_2140-EAG-3.csv", delimiter=";")
# bestand met overige tijdreeksen
series = pd.read_csv(
    r"../../data/input_csv/series_60_2140-EAG-3.csv",
    delimiter=";",
    index_col=[0],
    parse_dates=True,
)

# %% Model
# --------
# Maak bakjes model
e = wb.create_eag(eag_id, eag_name, deelgebieden)

# Voeg tijdreeksen toe
e.add_series_from_database(tijdreeksen, tmin=tmin, tmax=tmax)

# Voeg overige tijdreeksen toe
wb.add_timeseries_to_obj(e, series, overwrite=True)

# Simuleer waterbalans met parameters
e.simulate(parameters, tmin=tmin, tmax=tmax)

# %% Visualisatie
# ---------------
e.plot.water_level()
e.plot.aggregated()

print(
    "Elapsed time: {0:.1f} seconds".format(
        (pd.datetime.now() - starttijd).total_seconds()
    )
)
