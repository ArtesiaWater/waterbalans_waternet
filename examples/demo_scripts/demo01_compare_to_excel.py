import waterbalans as wb

""" DEMO 01: Compare waterbalance to original Excel balance

Minimal example that compares a water balance run in Python to
the original data from Excel.

Author: D.A. Brakenhoff
Date: 11-04-2019

"""
# %% Import modules
# -----------------
import os

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
tmax = "2015"

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

# Edit input files to match excel
parameters.loc[parameters.ParamCode == "QInMax", "Waarde"] = 0.0
dropmask = (
    (tijdreeksen.ParamType == "FEWS")
    | (tijdreeksen.ParamType == "KNMI")
    | (tijdreeksen.ParamType == "Local")
)
tijdreeksen.drop(tijdreeksen.loc[dropmask].index, inplace=True)


# %% Model
# --------
# Maak bakjes model
e = wb.create_eag(eag_id, eag_name, deelgebieden)

# Voeg tijdreeksen toe
e.add_series_from_database(tijdreeksen, tmin=tmin, tmax=tmax)

# Voeg overige tijdreeksen toe
wb.add_timeseries_to_obj(e, series)

# Simuleer waterbalans met parameters
e.simulate(parameters, tmin=tmin, tmax=tmax)

# %% Visualisatie
# ---------------
# Inladen resultaten uit Excel balans
exceldir = r"../../data/excel_pklz"
excelbalance = pd.read_pickle(
    os.path.join(exceldir, "{}_wbalance.pklz".format(e.name)), compression="zip"
)
# Kolommen omzetten naar getallen
for icol in excelbalance.columns:
    excelbalance.loc[:, icol] = pd.to_numeric(excelbalance[icol], errors="coerce")

# Maak figuur met vergelijking per flux + peil
fig = e.plot.compare_fluxes_to_excel_balance(excelbalance, showdiff=True)

print(
    "Elapsed time: {0:.1f} seconds".format(
        (pd.datetime.now() - starttijd).total_seconds()
    )
)
