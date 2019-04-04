import os
import numpy as np
import pandas as pd

# %% Get Excel balances and delete all but latest files
exceldir = r"C:\Users\dbrak\Documents\01-Projects\17026004_WATERNET_Waterbalansen\03data\balansen"
excelfiles = [i for i in os.listdir(exceldir) 
              if i.endswith(".xls") or i.endswith(".xlsx")]

# Keep only most recent versions
df = pd.DataFrame()
df["locations"] = [f.split("_")[0] for f in excelfiles]
df["filenames"] = excelfiles
dfkeep = df.drop_duplicates(subset="locations", keep="last")

# delete old versions of excel files
dfdelete = df.drop(dfkeep.index)
    
for fd in dfdelete.filenames:
    print("Deleting ... {}".format(fd))
    os.remove(os.path.join(exceldir, fd))

# %% Read FEWS from old reeksen files
reeksendir = r"c:\Users\dbrak\Documents\01-Projects\17026004_WATERNET_Waterbalansen\03data\DataExport_frompython"
reeksenfiles = [i for i in os.listdir(reeksendir) if i.startswith("reeks_") and i.endswith(".csv")]

fewskoppeldf = pd.DataFrame(index=[i.split("_")[-1].replace(".csv", "") for i in reeksenfiles])

for f in reeksenfiles:
    reeksen = pd.read_csv(os.path.join(reeksendir, f), delimiter=";",
                          decimal=".")

    fewsids = reeksen.loc[reeksen.ParamType == "FEWS"]
    
    gr = fewsids.groupby(by="ClusterType")
    
    for name, group in gr:
        count = 1
        for _, irow in group.iterrows():
            icol = name + "_" + str(count)
            fewskoppeldf.loc[irow.EAGCode, icol] = irow.WaardeAlfa
            count += 1

    sorted_cols = fewskoppeldf.columns.sort_values()
    fewskoppeldf = fewskoppeldf.loc[:, sorted_cols]
