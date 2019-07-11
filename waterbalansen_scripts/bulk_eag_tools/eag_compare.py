import os

import geopandas as gpd
import matplotlib.pyplot as plt
import matplotlib.patheffects as PathEffects
import numpy as np
import pandas as pd
from mpl_toolkits.axes_grid1.inset_locator import inset_axes
from shapely.algorithms import polylabel

import waterbalans as wb


class EagComparison:

    def __init__(self, csvdir, filter_str=None):
        self.csvdir = csvdir
        self.file_df = wb.utils.create_csvfile_table(csvdir)

        if filter_str is not None:
            drop_rows = []
            for i in self.file_df.index:
                if filter_str not in i:
                    drop_rows.append(i)
            self.file_df.drop(drop_rows, axis=0, inplace=True)

        self.modelstructure = self.get_modelstructure()
        self._bakjeid_to_name = self.modelstructure.loc[:, [
            "BakjeID", "BakjePyCode"]]

    def get_all_parameters(self):

        df_list = []

        for f in self.file_df.param:
            idf = pd.read_csv(os.path.join(self.csvdir, f), sep=";")
            df_list.append(idf)

        return pd.concat(df_list, axis=0, ignore_index=True)

    def get_parameter(self, parameter):

        all_params = self.get_all_parameters()
        mask = all_params.ParamCode == parameter
        if mask.sum() == 0:
            raise ValueError("No parameters name '{}'!".format(parameter))
        df = all_params.loc[mask]
        df.set_index("EAGCode", inplace=True)
        return df

    def get_all_timeseries(self):
        df_list = []

        for f in self.file_df.reeks:
            idf = pd.read_csv(os.path.join(self.csvdir, f), sep=";")
            df_list.append(idf)

        return pd.concat(df_list, axis=0, ignore_index=True)

    def get_timeseries(self, timeseries):
        ts = self.get_all_timeseries()
        mask = ts.ClusterType == timeseries
        df = ts.loc[mask]
        df.set_index("EAGCode", inplace=True)
        return df

    def get_all_chloride_params(self):
        df_list = []

        for f in self.file_df.stoffen_chloride:
            if isinstance(f, str):
                idf = pd.read_csv(os.path.join(self.csvdir, f), sep=";")
                df_list.append(idf)

        return pd.concat(df_list, axis=0, ignore_index=True)

    def get_chloride_param(self, flux):
        cl = self.get_all_chloride_params()
        mask = cl.InlaatType == flux
        df = cl.loc[mask]
        df.set_index("EAGCode", inplace=True)
        return df

    def get_all_phosphorus_params(self):
        df_list = []

        for f in self.file_df.stoffen_fosfor:
            idf = pd.read_csv(os.path.join(self.csvdir, f), sep=";")
            df_list.append(idf)

        return pd.concat(df_list, axis=0, ignore_index=True)

    def get_phosphorus_params(self, flux):
        p = self.get_all_phosphorus_params()
        mask = p.InlaatType == flux
        df = p.loc[mask]
        df.set_index("EAGCode", inplace=True)
        return df

    def get_modelstructure(self):
        df_list = []

        for f in self.file_df.opp:
            idf = pd.read_csv(os.path.join(self.csvdir, f), sep=";")
            df_list.append(idf)

        return pd.concat(df_list, axis=0, ignore_index=True)

    def percentage_open_water(self):

        ms = self.modelstructure
        area_water = ms.loc[ms.BakjePyCode == "Water",
                            ["EAGCode", "OppWaarde"]]
        area_water.set_index("EAGCode", inplace=True)
        area_water = area_water.squeeze()
        gr = ms.groupby("EAGCode")
        area_tot = gr["OppWaarde"].sum()
        pw = area_water.divide(area_tot).multiply(100.)
        pw.name = "Open Water %"

        return pw


def create_gdf(df, shapefile, eag_code_column=""):
    shp = gpd.read_file(shapefile)

    # for current shapefile w GAFs and EAgs
    mask = ~shp[eag_code_column].str.contains("EAG")
    shp.loc[mask, eag_code_column] += "-GAF"

    # set index
    shp.set_index(eag_code_column, inplace=True)
    # join other df
    gdf = shp.join(df, how="left")
    return gdf


def plot_gdf(gdf, color_column, ax=None, labels=True, fontsize=5, **kwargs):

    if ax is None:
        fig, ax = plt.subplots(1, 1, figsize=(10, 10), dpi=150)

    gdf.plot(column=color_column, ax=ax, **kwargs)

    fig.tight_layout()

    if "cmap" in kwargs.keys():
        cmap = kwargs["cmap"]
    else:
        cmap = "viridis"
    if "vmin" in kwargs.keys():
        vmin = kwargs["vmin"]
    else:
        vmin = gdf[color_column].min()
    if "vmax" in kwargs.keys():
        vmax = kwargs["vmax"]
    else:
        vmax = gdf[color_column].max()

    sm = plt.cm.ScalarMappable(cmap=cmap,
                               norm=plt.Normalize(vmin=vmin,
                                                  vmax=vmax))
    # fake up the array of the scalar mappable.
    sm._A = []
    cbaxes = inset_axes(ax, width="30%", height="3%", loc="upper right")
    plt.colorbar(sm, cax=cbaxes, orientation='horizontal')
    cbaxes.set_xlabel(color_column)

    if labels:
        xy = find_visual_centers(gdf, tolerance=1.0)
        for i in xy.index:
            ax.annotate(i, (xy.loc[i, "x"], xy.loc[i, "y"]),
                        fontsize=fontsize, horizontalalignment="center",
                        color="k", fontweight="bold",
                        path_effects=[PathEffects.withStroke(linewidth=2,
                                                             foreground="w")])

    return ax


def find_visual_centers(gdf, tolerance=1.0):
    df = pd.DataFrame(index=gdf.index, columns=["x", "y"])
    for i, irow in gdf.iterrows():
        if "Multi" in irow.geometry.geom_type:
            areas = [p.area for p in irow.geometry.geoms]
            idx = areas.index(max(areas))
            geom = irow.geometry.geoms[idx]
        else:
            geom = irow.geometry

        # for polygon crossing itself
        if not geom.is_valid:
            geom = geom.buffer(0)

        pt = polylabel.polylabel(geom, tolerance=tolerance)
        df.loc[i, "x"] = pt.xy[0][0]
        df.loc[i, "y"] = pt.xy[1][0]
    return df


if __name__ == "__main__":
    csvdir = r"../../data/input_csv"
    shpfile = r"../../data/eag_gaf_shp/Waterbalansen_final.shp"
    filt = "GAF"

    ec = EagComparison(csvdir, filter_str=filt)

    # model structure
    ms = ec.modelstructure

    # % open water
    pw = ec.percentage_open_water()

    # param
    hmax = ec.get_parameter("hMax")

    # reeks
    p = ec.get_timeseries("Neerslag")

    # chloride concentratie per flux
    cl = ec.get_chloride_param("Verhard")

    # fosfor concentratie per flux
    f = ec.get_phosphorus_params("Uitspoeling")

    # create geodataframe and mask EAGs or GAFs
    other = pw
    other.name = "% Open Water"
    gdf = create_gdf(other, shpfile, eag_code_column="GAFIDENT")

    mask = gdf.index.str.contains("EAG")
    if filt == "GAF":
        mask = ~mask
    gdf = gdf.loc[mask]

    # plot gdf
    col = other.name
    ax = plot_gdf(gdf, color_column=col, cmap="RdBu",
                  vmin=gdf[col].min(), vmax=gdf[col].max(),
                  labels=True, fontsize=7, alpha=1.0)