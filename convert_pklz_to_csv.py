import os
import pandas as pd
import tqdm

datadir = r"./data/excel_pklz"

files = [i for i in os.listdir(datadir) if i.endswith("_series.pklz")]

for f in tqdm.tqdm(files, desc="Process series pklz"):
    df = pd.read_pickle(os.path.join(datadir, f), compression="zip")
    # df.dropna(how="all", axis=1, inplace=True)
    # df.drop(columns=df.loc[:, (df.sum(axis=0)==0).values].columns, inplace=True)
    df.to_csv(os.path.join(datadir, f.replace(".pklz", ".csv")))
