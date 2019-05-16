""" DEMO 04: Calculate phosphor concentration

Minimal example that calculates the phosphor concentration
for a water balance.

Author: D.A. Brakenhoff
Date: 11-04-2019

"""
# %% Import modules
# -----------------
import os
import pandas as pd
import matplotlib as mpl
mpl.interactive(True)
import matplotlib.pyplot as plt
import waterbalans as wb

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
deelgebieden = pd.read_csv(
    r"../data/input_csv/opp_1207_2140-EAG-3.csv", delimiter=";")

# bestand met tijdreeksen, b.v. neerslag/verdamping:
tijdreeksen = pd.read_csv(
    r"../data/input_csv/reeks_1207_2140-EAG-3.csv", delimiter=";")
dropmask = (tijdreeksen.ParamType == "FEWS") | (tijdreeksen.ParamType == "KNMI") | \
            (tijdreeksen.ParamType == "Local")
tijdreeksen.drop(tijdreeksen.loc[dropmask].index, inplace=True)

# bestand met parameters per deelgebied
parameters = pd.read_csv(
    r"../data/input_csv/param_1207_2140-EAG-3.csv", delimiter=";")

# bestand met overige tijdreeksen
series = pd.read_csv(
    r"../data/input_csv/series_1207_2140-EAG-3.csv", delimiter=";",
    index_col=[1], parse_dates=True)

# bestand met concentraties van stof per flux
fosfor = pd.read_csv(
    r"..\data\input_csv\stoffen_fosfor_1207_2140-EAG-3.csv", delimiter=";",
        decimal=",")
fosfor.columns = [icol.capitalize() for icol in fosfor.columns]
fosfor.replace("Riolering", "q_cso", inplace=True)

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

# Simuleer de waterkwaliteit
mass_in, mass_out, mass_fosfor = e.simulate_wq(fosfor)
mass_in_max, mass_out_max, mass_fosfor_max = e.simulate_wq(fosfor, increment=True)

# Bereken de concentratie
C_fosfor = mass_fosfor / e.water.storage["storage"]
C_fosfor_max = mass_fosfor_max / e.water.storage["storage"]

# %% Visualisatie
# ---------------
fig, ax = plt.subplots(1, 1, figsize=(12, 6), dpi=150)
ax.plot(C_fosfor.index, C_fosfor, label="Fosfor concentratie")
ax.plot(C_fosfor_max.index, C_fosfor_max, label="Maximale fosfor concentratie")
ax.legend(loc="best")
ax.set_ylabel("Concentratie (mgP/l)")
ax.grid(b=True)
fig.tight_layout()

ax = e.plot.wq_loading(mass_in, mass_out)

print("Elapsed time: {0:.1f} seconds".format((pd.datetime.now() - starttijd).total_seconds()))
