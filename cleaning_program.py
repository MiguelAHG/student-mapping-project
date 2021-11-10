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

# Delete rows with empty cells. This is temporary. For the real thing, we have to make sure all barangays and cities are complete in the data.

student_df = student_df.dropna(subset = ["barangay", "city_municipality", "province"])

student_df = student_df.reset_index(drop = True)

print("\nStudent data: ", student_df.columns.tolist())
#%%
# Save geodata as CSV
(
    gdf
    [["NAME_0", "NAME_1", "NAME_2", "NAME_3"]]
    .to_csv("./private/cleaning_outputs/gadm_location_names.csv")
)

# Save concatenated data for ABM students
student_df.to_csv("./private/cleaning_outputs/abm_all_locations.csv")

# %%
# This cell preprocesses both of the datasets and saves them to files.

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
    # "barangay": "NAME_3",
}

def full_preprocess(df, label_lst, p_filename = None, c_filename = None):
    """Fully preprocess a dataset, either student data or GADM.
If p_filename is set, the preprocessed data is saved.
If c_filename is set, a comparison of the original and preprocessed data will be saved to a file."""

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

    if p_filename is not None:
        # Save preprocessed data only.
        df_preprocessed.to_csv(f"./private/cleaning_outputs/{p_filename}.csv")

    if c_filename is not None:
        # Save a table that compares the original location data to the preprocessed version.

        # Append _preprocessed to labels
        df_pp_copy = df_preprocessed.copy()
        df_pp_copy.columns = [
            label + "_preprocessed"
            for label in df_preprocessed.columns
        ]

        # Put the original columns next to the preprocessed ones.
        df_comparison = pd.concat(
            [df[label_lst], df_pp_copy],
            axis = 1,
        )

        df_comparison.to_csv(f"./private/cleaning_outputs/{c_filename}.csv")

    # Only return the preprocessed data.
    return df_preprocessed

# Student data preprocessing
s_label_lst = list(label_dct.keys())

student_df_pp = full_preprocess(
    student_df,
    s_label_lst,
    p_filename = "student_df_preprocessed",
    c_filename = "student_df_comparison",
)

# GADM data preprocessing
g_label_lst = list(label_dct.values())

gadm_df_pp = full_preprocess(
    gdf,
    g_label_lst,
    p_filename = "gadm_df_preprocessed",
    c_filename = "gadm_df_comparison",
)

# %%
def get_ratio(s1, s2):
    """Obtain Levenshtein ratio of two strings. Can be used in pd.Series.apply()"""
    ratio = Levenshtein.ratio(s1, s2)
    return ratio

# For each student location, find a match in GADM.

match_rows = []
for s_index, s_row in student_df_pp.iterrows():
    score_dct = {}

    for s_label in s_row.index:
        s_text = s_row[s_label]

        g_label = label_dct[s_label]
        g_col = gadm_df_pp[g_label]
        score_dct[g_label] = g_col.apply(get_ratio, s2 = s_text)

    score_df = pd.DataFrame(score_dct)

    score_df["total"] = score_df.sum(axis = 1)
    highest_score = score_df["total"].max()
    g_index = score_df["total"].argmax()

    g_row_orig = gdf.iloc[g_index].loc[g_label_lst + ["GID_3"]]
    g_row_orig["score"] = highest_score
    s_row_orig = student_df.iloc[s_index].loc[s_label_lst]

    final_row = pd.concat([s_row_orig, g_row_orig], axis = 0)
    match_rows.append(final_row)

match_df = pd.DataFrame(match_rows)

match_df.to_csv("./private/cleaning_outputs/matches.csv")

match_df.head()
