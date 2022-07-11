#%% Import

import pandas as pd
import numpy as np
import fiona
import geopandas as gpd

#%%
# Determine the finest layer. 3 is barangay, 2 is city, 1 is province.
finest_layer = 2

#%%
# Save table of all GADM locations
# Get data
gpkg = "./geo_data/gadm36_PHL.gpkg"

# See list of layers in the GPKG.
layers = fiona.listlayers(gpkg)
print("GADM Layers: ", layers)

# Use the finest layer, number 3
gdf = gpd.read_file(gpkg, layer = f"gadm36_PHL_{finest_layer}")
print("\nGADM: ", gdf.columns.tolist())

#%%
# Save table of locations without map configuration data as CSV
gdf.drop("geometry", axis = 1).to_csv("./private/cleaning_outputs/gadm_all_locations.csv")