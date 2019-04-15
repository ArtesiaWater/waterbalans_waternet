""" DEMO 02: Run 10 balances and plot output

Minimal example that runs 10 waterbalances either 
on EAG or GAF level and plots results.

Author: D.A. Brakenhoff
Date: 11-04-2019

"""
# %% Import modules
# -----------------
import os
import pandas as pd
import matplotlib as mpl
mpl.interactive(True)
import waterbalans as wb
from tqdm import tqdm

starttijd = pd.datetime.now()

# Basisgegevens
# -------------
# Namen van EAGs/GAFs:
eag_gaf_ids = ['2130-EAG-2', '2140-EAG-3', '2140-EAG-6', '2250-EAG-2', '2500-EAG-6',
               '2010-GAF', '2110-GAF', '2100-GAF', '2120-GAF', '2130-GAF',]

# Tabel met alle bestanden per EAG/GAF:
csvdir = r"../data/input_csv"
file_df = wb.create_csvfile_table(csvdir)

# Begin en eindtijd simulaties
tmin = "1996"
tmax = "2015"

# List to store waterbalances
wb_list = []

# Loop over namen
for obj_name in tqdm(eag_gaf_ids, desc="Building and simulating", ncols=0):
    print()
    eag_id = obj_name.split("-")[-1]

    # Haal csv bestandnamen op
    fbuckets, fparams, freeks, fseries, _, _ = file_df.loc[obj_name]
    
    # %% Inlezen gegevens
    # -------------------    
    # bestand met deelgebieden en oppervlaktes:
    deelgebieden = pd.read_csv(os.path.join(csvdir, fbuckets), delimiter=";")
    
    # bestand met tijdreeksen, b.v. neerslag/verdamping:
    tijdreeksen = pd.read_csv(os.path.join(csvdir, freeks), delimiter=";")
    
    # bestand met parameters per deelgebied
    parameters = pd.read_csv(os.path.join(csvdir, fparams), delimiter=";")

    # bestand met overige tijdreeksen
    series = pd.read_csv(os.path.join(csvdir, fseries), delimiter=";", 
                         index_col=[1], parse_dates=True)

    # %% Model
    # --------
    # Maak bakjes model
    e = wb.create_eag(eag_id, obj_name, deelgebieden)

    # Voeg tijdreeksen toe
    e.add_series(tijdreeksen, tmin=tmin, tmax=tmax)

    # Voeg overige tijdreeksen toe
    wb.add_timeseries_to_obj(e, series)

    # Simuleer waterbalans met parameters
    e.simulate(parameters, tmin=tmin, tmax=tmax)

    # Opslaan in lijst
    wb_list.append(e)

print(wb_list)
print("Elapsed time: {0:.1f} seconds".format((pd.datetime.now() - starttijd).total_seconds()))
