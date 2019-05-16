# %% Import modules
# -----------------
import os

import tqdm
import numpy as np
import matplotlib as mpl
import pandas as pd
from hkvfewspy import FewsTimeSeriesCollection
from pastas.read import KnmiStation

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

# Neerslag koppeling FEWS -> KNMI
fews2knmi = {"66013cal": 223,
             "66004cal": 458,
             "66015cal": 563,
             "66005cal": 572,
             "66011cal": 548,
             "66017cal": 470,
             "66009cal": 593,
             "66014cal": 559,
             "66016cal": 195,
             "66006cal": 441,  # this FEWS ID is working!
             "66010cal": 437,
             "66002_VerdampingCAL": 240,
             "66003_VerdampingCAL": 260}

# Get KNMI data up front
df = KnmiStation.download(start=pd.Timestamp("1996-01-01"),
                          end=pd.Timestamp("2019-01-01"),
                          stns=list(fews2knmi.values())[-2:],
                          vars="RH:EV24")
df.data.rename(columns={"RH": "RD"}, inplace=True)
df2 = KnmiStation.download(start=pd.Timestamp("1996-01-01"),
                           end=pd.Timestamp("2019-01-01"),
                           stns=list(fews2knmi.values())[:-2],
                           vars="RD")
df2.data["EV24"] = np.nan
if np.any(df2.data.index.hour == 9):
    df2.data.index = df2.data.index.floor(freq="D") - pd.Timedelta(days=1)
elif np.any(df2.data.index.hour == 1):
    df2.data.index = df2.data.index.normalize() - pd.Timedelta(days=1)
if np.any(df.data.index.hour == 1):
    df.data.index = df.data.index.normalize() - pd.Timedelta(days=1)

knmi = pd.concat([df.data, df2.data], axis=0, sort=True)

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

wb_dict = {}

# %% Start loop

# for name in tqdm.tqdm(file_df.index, desc="Waterbalansen", ncols=0):
# print()
for name in ["2510-EAG-3", "2010-GAF", "2140-EAG-6"]:
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

    # # replace FEWS with KNMI
    # for p_or_e, col in zip(["Neerslag", "Verdamping"], [2, 1]):
    #     mask = (tijdreeksen.ClusterType == p_or_e) & (
    #         tijdreeksen.ParamType == "FEWS")
    #     tijdreeksen.loc[mask, "ParamType"] = "KNMI"
    #     fewscode = tijdreeksen.loc[mask, "WaardeAlfa"].iloc[0].split("|")[col]
    #     tijdreeksen.loc[mask, "Waarde"] = int(fews2knmi[fewscode])


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
    else:
        mengriool = e.get_buckets(buckettype="MengRiool")
        if len(mengriool) > 0:
            for b in mengriool:
                b.use_eag_cso_series = False

    mask = (tijdreeksen.ClusterType == "Neerslag") & (
        tijdreeksen.ParamType == "FEWS")
    fewscode = tijdreeksen.loc[mask, "WaardeAlfa"].iloc[0].split("|")[2]
    e.add_timeseries(knmi.loc[knmi.STN == fews2knmi[fewscode], "RD"],
                     name="Neerslag", tmin=tmin, tmax=tmax)
    mask = (tijdreeksen.ClusterType == "Verdamping") & (
        tijdreeksen.ParamType == "FEWS")
    fewscode = tijdreeksen.loc[mask, "WaardeAlfa"].iloc[0].split("|")[1]
    e.add_timeseries(knmi.loc[knmi.STN == fews2knmi[fewscode], "EV24"],
                     name="Verdamping", tmin=tmin, tmax=tmax)

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

# %% End of script
# ----------------
print("Elapsed time: {0:.1f} seconds".format(
    (pd.datetime.now() - starttijd).total_seconds()))

inlaten = pd.DataFrame(index=pd.date_range("1996-01-01", "2019-01-01", freq="D"),
                       columns=[e.name for e in wb_dict.values()])

for name, e in wb_dict.items():
    fluxes = e.aggregate_fluxes()
    inlaten.loc[fluxes.index, name] = fluxes["berekende inlaat"]
