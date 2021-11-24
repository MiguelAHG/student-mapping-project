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

# Open the sample student location data.
sheets = pd.read_excel(
    "./private/student_location_data/sample_abm.xlsx",
    sheet_name = None,
)
print("\nStudent sheets: ", sheets.keys())

student_df = pd.concat(
    [sheets["11ABM"], sheets["12ABM"]],
    axis = 0
)

student_df = student_df.reset_index(drop = True)

# Save geodata as CSV
gdf = gdf.drop("geometry", axis = 1)
gdf.to_csv("./private/cleaning_outputs/gadm_all_locations.csv")

# Save concatenated data for ABM students
student_df.to_csv("./private/cleaning_outputs/abm_all_locations.csv")