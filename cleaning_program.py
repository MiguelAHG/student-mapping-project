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
    "./student_location_data/sample_abm.xlsx",
    sheet_name = None,
)
print("\nStudent data: ", sheets.keys())

student_df = sheets["11ABM"]
print("\n11ABM: ", student_df.columns.tolist())
# %%
student_df.isnull().sum()

# %%
# This is temporary. For the real thing, we have to make sure all barangays and cities are complete in the data.

student_df = student_df.dropna(subset = ["barangay", "city_municipality"])
# %%
# Dictionary mapping student location data labels to their GADM equivalents
label_dct = {
    "city_municipality": "NAME_2",
    "barangay": "NAME_3",
}

def preprocess_series(series):
    """Perform standard text preprocessing on a Series."""
    result = (
        series.str.strip()
        .str.replace("[\.\,]", "", regex = True)
        .str.lower()
        .str.replace("ñ", "n", regex = False)
    )

    return result

final_cols = {
    "barangay": student_df["barangay"],
    "city_municipality": student_df["city_municipality"],
}

# Note to self: Fix this part so that we go row by row instead of column by column.
for s_label in ["barangay", "city_municipality"]:
    s_col = preprocess_series(student_df[s_label])

    g_label = label_dct[s_label]
    g_col = preprocess_series(gdf[g_label])

    if g_label == "NAME_3":
        g_col = g_col.str.replace(" poblacion$", "", regex = True)

    print(s_col.head(), "\n")
    print(g_col.head(), "\n")

    def get_geo_match(s_text, g_col):
        ratios = pd.Series([
            Levenshtein.ratio(s_text, g_text)
            for g_text in g_col
        ])

        g_index = ratios.argmax()

        g_text = gdf.iloc[g_index, :].loc[g_label]

        return g_text

    matches = s_col.apply(
        get_geo_match,
        g_col = g_col,
    )
    matches.name = f"{s_label}_matches"

    final_cols[matches.name] = matches

final_df = pd.DataFrame(final_cols)
final_df.to_csv("final_matches.csv")

final_df.head()