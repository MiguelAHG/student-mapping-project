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

print("\nStudent data: ", student_df.columns.tolist())
#%%
# Save geodata as CSV
(
    gdf
    [["NAME_0", "NAME_1", "NAME_2", "NAME_3"]]
    .to_csv("./private/cleaning_outputs_private/gadm_location_names.csv")
)

# Save concatenated data for ABM students
student_df.to_csv("./private/cleaning_outputs_private/abm_all_locations.csv")
# %%
student_df.isnull().sum()

# %%
# Delete rows with empty cells. This is temporary. For the real thing, we have to make sure all barangays and cities are complete in the data.

student_df = student_df.dropna(subset = ["barangay", "city_municipality", "province"])

# %%
# Dictionary mapping student location data labels to their GADM equivalents

def preprocess_series(series):
    """Perform standard text preprocessing on a Series."""
    result = (
        series
        .str.strip()
        .str.replace(r"[\.\,\'\-]", "", regex = True)
        .str.lower()
        .str.replace("ñ", "n", regex = False)
    )

    return result

# Dictionary of custom preprocessing steps per column
# Note to self: after custom preprocessing, use .strip()
preprocess_dct = {
    "province": lambda series: series,
    "city_municipality": lambda series: (
        series
        .str.replace(r" city$", "", regex = True)
        .str.replace(r"^san\b", "saint", regex = True)
    ),
    "barangay": lambda series: (
        series
        .str.replace(r"^((barangay)|(brgy)) ", "", regex = True)
        .str.replace(r"^((sto)|(sta)|(san)|(santo)|(santa))\b", "saint", regex = True)
        .str.replace(r"^gen\b", "general", regex = True)
    ),
    "NAME_1": lambda series: (
        series
        .str.replace(r"^metropolitan manila$", "metro manila", regex = True)
    ),
    "NAME_2": lambda series: (
        series
        .str.replace(r" city$", "", regex = True)
        .str.replace(r"^((santo)|(santa))\b", "saint", regex = True)
    ),
    "NAME_3": lambda series: (
        series
        .str.replace(r"^((barangay)|(bgy)|(bgy no)) ", "", regex = True)
        .str.replace(r"^((st)|(santo)|(santa))\b", "saint", regex = True)
    )
}

# Dictionary converting student data labels to their GADM equivalents
label_dct = {
    "province": "NAME_1",
    "city_municipality": "NAME_2",
    "barangay": "NAME_3",
}

def full_preprocess(df, label_lst, save = False, filename = "new"):
    """Fully preprocess a dataset, either student data or GADM."""

    # Initial preprocessing
    df_preprocessed = (
        df[label_lst]
        .apply(preprocess_series, axis = 0)
    )

    # For each column, perform unique preprocessing steps.
    for col in df_preprocessed:
        specific_func = preprocess_dct[col]

        df_preprocessed[col] = (
            specific_func(df_preprocessed[col])
            .str.strip()
        )

    # Append _preprocessed to labels
    df_preprocessed.columns = [
        label + "_preprocessed"
        for label in df_preprocessed.columns
    ]

    # Put the original columns next to the preprocessed ones.
    df_comparison = pd.concat(
        [df[label_lst], df_preprocessed],
        axis = 1,
    )

    if save:
        df_comparison.to_csv(f"./private/cleaning_outputs_private/{filename}.csv")

    return df_comparison

# Student data preprocessing
s_label_lst = list(label_dct.keys())

student_df_comparison = full_preprocess(student_df, s_label_lst, save = True, filename = "student_df_comparison")

# GADM data preprocessing
g_label_lst = list(label_dct.values())

gadm_df_comparison = full_preprocess(gdf, g_label_lst, save = True, filename = "gadm_df_comparison")

# %%
def get_ratio(s1, s2):
    """Obtain Levenshtein ratio of two strings. Can be used in pd.Series.apply()"""
    ratio = Levenshtein.ratio(s1, s2)
    return ratio

def find_matches(df_preprocessed):
    """For each student location, find a match in GADM."""

    for index, row in df_preprocessed.iterrows():
        ratio_results = []
        for s_label in s_label_lst:

            s_text = row[s_text]

            g_label = label_dct[s_label]

            # in progress