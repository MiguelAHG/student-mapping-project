#%% Import

import pandas as pd
import numpy as np
import fiona
import Levenshtein
import geopandas as gpd

#%% Get data
gpkg = "./geo_data/gadm36_PHL.gpkg"

# See list of layers in the GPKG.
layers = fiona.listlayers(gpkg)
print("GADM Layers: ", layers)

# Use the finest layer, number 3
gdf = gpd.read_file(gpkg, layer = "gadm36_PHL_3")
print("\nGADM: ", gdf.columns.tolist())

# Save geodata as CSV
gdf = gdf.drop("geometry", axis = 1)
gdf.to_csv("./private/cleaning_outputs/gadm_all_locations.csv")