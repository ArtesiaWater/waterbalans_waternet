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
# for name in ["2010-GAF"]:
for name in ["2510-EAG-3", "2010-GAF", "2140-EAG-6"]:
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
                      use_waterlevel_series=use_wl,
                      logfile="waterbalans.log")

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
            b.path_to_cso_series = r"./data/cso_series/240_cso_timeseries.pklz"

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
                       columns=[e.name for e in wb_dict.values()], dtype=np.float)

for name, e in wb_dict.items():
    fluxes = e.aggregate_fluxes()
    # get inlaat columns and add together
    inlaat_cols = [col for col in fluxes.columns if col.lower().startswith("inlaat")] + \
        ["berekende inlaat"]
    inlaten.loc[fluxes.index, name] = fluxes.loc[:, inlaat_cols].sum(axis=1)

inlaat_df = inlaten.stack().reset_index()
inlaat_df.columns = ["datetime", "loc_ID", "value"]
# convert to m3/s and round to 4 decimals
inlaat_df["value"] = (inlaat_df["value"] / (24*60*60)).round(4)
# remove -GAF from name
inlaat_df["loc_ID"] = inlaat_df["loc_ID"].str.replace('-GAF', '', regex=True)
# sort values bij location then date
inlaat_df.sort_values(by=["loc_ID", "datetime"], inplace=True)
# convert to different datetime str
inlaat_df["datetime"] = inlaat_df['datetime'].dt.strftime("%d-%m-%y %H:%M")

# export file
inlaat_df.to_csv("inlaten_testfile.csv", index=False)
