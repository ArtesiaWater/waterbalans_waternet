# %% Import modules
# -----------------
import os

import tqdm
import numpy as np
import matplotlib as mpl
import pandas as pd

import waterbalans as wb

mpl.interactive(True)

starttijd = pd.datetime.now()

# Basisgegevens
# -------------
csvdir = r"./data/input_csv"
file_df = wb.utils.create_csvfile_table(csvdir)

# Begin en eindtijd simulatie
tmin = "1996"
tmax = "2019"

# Eag koppeling
eag_koppeltabel = pd.read_csv("./data/eag_koppeling.txt", index_col=[0])
# Sorteer EAGs zodat afhankelijke EAGs als laatste komen
last, first = [], []
for i in file_df.index:
    if i in eag_koppeltabel.index:
        last.append(i)
    else:
        first.append(i)
file_df = file_df.loc[first+last]

# %% Start loop
wb_dict = {}

# for name in tqdm.tqdm(file_df.index, desc="Waterbalansen", ncols=0):
for name in ["2010-GAF", "2140-EAG-6", "2500-EAG-6"]:
    print()
    # Get CSV files
    fbuckets, fparams, freeks, fseries, fcl, ffos = file_df.loc[name]

    # Naam en ID van gebied
    eag_id = name.split("-")[-1]
    eag_name = name

# %% Inlezen gegevens
# -------------------
    # bestand met deelgebieden en oppervlaktes:
    deelgebieden = pd.read_csv(os.path.join(csvdir, fbuckets), delimiter=";")
    # bestand met tijdreeksen, b.v. neerslag/verdamping:
    tijdreeksen = pd.read_csv(os.path.join(csvdir, freeks), delimiter=";")
    # bestand met parameters per deelgebied
    parameters = pd.read_csv(os.path.join(csvdir, fparams), delimiter=";")
    # bestand met overige tijdreeksen
    if not isinstance(fseries, float):
        series = pd.read_csv(os.path.join(csvdir, fseries),
                             delimiter=";", index_col=[0], parse_dates=True)
    else:
        series = None

# %% Simulation settings based on parameters
# ------------------------------------------
    if parameters.loc[parameters.ParamCode == "hTargetMin", "Waarde"].iloc[0] != -9999.:
        use_wl = True
    else:
        use_wl = False

# %% Model
# --------
    # Maak bakjes model
    e = wb.create_eag(eag_id, eag_name, deelgebieden,
                      use_waterlevel_series=use_wl)

    # Voeg tijdreeksen toe
    e.add_series_from_database(tijdreeksen, tmin=tmin, tmax=tmax)

    # Voeg overige tijdreeksen toe (overschrijf FEWS met Excel)
    if series is not None:
        wb.add_timeseries_to_obj(e, series, overwrite=True)

    # Force MengRiool to use external timeseries
    mengriool = e.get_buckets(buckettype="MengRiool")
    if len(mengriool) > 0:
        for b in mengriool:
            b.use_eag_cso_series = False

    # Voeg tijdreeksen uit andere EAGs toe
    if e.name in eag_koppeltabel.index:
        for series_name, other_eag in eag_koppeltabel.loc[e.name].dropna().iteritems():
            try:
                o = wb_dict[other_eag]
                fluxes = o.aggregate_fluxes()
                if series_name.startswith("Inlaat"):
                    addseries = -1*fluxes.loc[:, "berekende uitlaat"]
                elif series_name.startswith("Uitlaat"):
                    addseries = fluxes.loc[:, "berekende inlaat"]

                e.add_timeseries(addseries, series_name, tmin=tmin, tmax=tmax)
            except KeyError as e:
                print("No EAG with name {}!".format(other_eag))

    # Simuleer waterbalans met parameters
    e.simulate(parameters, tmin=tmin, tmax=tmax)

    # Add balance to dictionary
    wb_dict[e.name] = e

# %% Collect information from EAGs and save to file
# ----------------
print("Elapsed time: {0:.1f} seconds".format(
    (pd.datetime.now() - starttijd).total_seconds()))

inlaten = pd.DataFrame(index=pd.date_range("1996-01-01", "2019-01-01", freq="D"),
                       columns=[e.name for e in wb_dict.values()])

for name, e in wb_dict.items():
    fluxes = e.aggregate_fluxes()
    inlaten.loc[fluxes.index, name] = fluxes["berekende inlaat"]

inlaat_df = inlaten.stack().reset_index()
inlaat_df.columns = ["Datetime", "Loc_ID", "Value"]
inlaat_df["Variable"] = "Inlaat Debiet"
inlaat_df["Unit"] = "m3/s"
inlaat_df["Value"] = inlaat_df["Value"] / (24*60*60)
inlaat_df.sort_values(by=["Loc_ID", "Datetime"], inplace=True)

inlaat_df.to_csv("inlaten_testfile.csv", index=False)
