#%% Import

import pandas as pd
import numpy as np
import Levenshtein
import geopandas as gpd

#%%
# Get data
# Choose whether to go down to barangay level (3) or only city level (2).
finest_level = 2

gpkg = "./geo_data/gadm36_PHL.gpkg"

gdf = gpd.read_file(gpkg, layer = f"gadm36_PHL_{finest_level}")

if finest_level == 3:
    # Do not include barangays whose name is n.a.
    gdf = gdf.loc[gdf["NAME_3"] != "n.a."]

# Open the sample student location data.
student_df = pd.read_csv(
    "./private/student_location_data/full_ashs_locations.csv",
)

student_df.head()

#%%
# Check number of non-null values per column
student_df.info()

#%%
# Check for duplicate OBFs
dupes = student_df.loc[
    student_df["student_number"]
    # keep = False so all duplicates are marked True
    .duplicated(keep = False)
]

dupes.shape[0]
#%%
# Check for students with incomplete location data
loc_cols = pd.Series(
    {
        1: "province",
        2: "city_municipality",
        3: "barangay",
    }
)

loc_cols = loc_cols.loc[:finest_level]

inc_students = student_df.loc[student_df[loc_cols].isnull().any(axis = 1)]

inc_df = inc_students[["student_number"]].copy()

for col in loc_cols:
    inc_df[col] = student_df[col].isnull().apply(lambda x: col if x else np.nan)

inc_df["missing_data"] = inc_df[loc_cols].apply(
    lambda row: ", ".join(row.dropna().to_list()),
    axis = 1,
)

inc_result_df = inc_df[["student_number", "missing_data"]]

inc_result_df.to_csv("./private/cleaning_outputs/students_with_missing_data.csv", index = False)

inc_result_df
#%%
# Delete rows with empty cells. This is temporary. For the real thing, we have to make sure all barangays and cities are complete in the data.

# student_df = (
#     student_df
#     .dropna(subset = ["barangay", "city_municipality", "province"])
#     .reset_index(drop = True)
# )

# student_df.info()

#%%
# new code: Raise error if there's missing location data. This is helpful if the matching program is run from the command line instead of interactively.

data_is_missing = inc_students.shape[0] > 0

if data_is_missing:
    raise ValueError("Some location data is missing. Check students_with)missing_data.csv")
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
        .str.replace(r"^((sto)|(sta)|(san)|(santo)|(santa))\b", "saint", regex = True)
    ),
    "barangay": lambda series: (
        series
        .str.replace(r"^((barangay)|(brgy)) ", "", regex = True)
        .str.replace(r"^((sto)|(sta)|(san)|(santo)|(santa))\b", "saint", regex = True)
        .str.replace(r"^[gh]en.?\b", "general", regex = True)
    ),
    "NAME_1": lambda series: (
        series
        .str.replace(r"^metropolitan manila$", "metro manila", regex = True)
    ),
    "NAME_2": lambda series: (
        series
        .str.replace(r" city$", "", regex = True)
        .str.replace(r"^((sto)|(sta)|(san)|(santo)|(santa))\b", "saint", regex = True)
    ),
    "NAME_3": lambda series: (
        series
        .str.replace(r"^((barangay)|(bgy)|(bgy no)) ", "", regex = True)
        .str.replace(r"^((sto)|(sta)|(san)|(santo)|(santa))\b", "saint", regex = True)
    )
}

# Dictionary converting student data labels to their GADM equivalents
label_series = pd.Series(
    {
        "province": "NAME_1",
        "city_municipality": "NAME_2",
        "barangay": "NAME_3",
    }
)

label_series = label_series.iloc[:finest_level]
gid_label = f"GID_{finest_level}"

def full_preprocess(df, label_lst, comparison_filename = None):
    """Fully preprocess a dataset, either student data or GADM.
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

    if comparison_filename is not None:
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

        df_comparison.to_csv(f"./private/cleaning_outputs/{comparison_filename}.csv")

    # Only return the preprocessed data.
    return df_preprocessed

# Student data preprocessing
s_label_lst = label_series.index.tolist()

student_df_pp = full_preprocess(
    student_df,
    s_label_lst,
    comparison_filename = "student_df_comparison",
)

# GADM data preprocessing
g_label_lst = label_series.tolist()

gadm_df_pp = full_preprocess(
    gdf,
    g_label_lst,
    comparison_filename = None,# "gadm_df_comparison",
)

print("Done preprocessing.")

# %%
# For each student location, find a match in GADM.

from time import perf_counter

t_start = perf_counter()

def get_ratio(s1, s2):
    """Obtain Levenshtein ratio of two strings. Can be used in pd.Series.apply()"""
    ratio = Levenshtein.ratio(s1, s2)
    return ratio

match_rows = []
for s_index, s_row in student_df_pp.iterrows():
    score_dct = {}

    for s_label in s_row.index:
        s_text = s_row[s_label]

        g_label = label_series[s_label]
        g_col = gadm_df_pp[g_label]
        score_dct[g_label] = g_col.apply(get_ratio, s2 = s_text)

    score_df = pd.DataFrame(score_dct)

    score_df["total"] = score_df.sum(axis = 1)
    highest_score = score_df["total"].max()
    g_index = score_df["total"].argmax()

    g_row_orig = gdf.iloc[g_index].loc[g_label_lst + [gid_label]]
    g_row_orig["score"] = highest_score
    s_row_orig = (
        student_df
        .iloc[s_index]
        .loc[
            ["strand", "grade_level", "section"] + s_label_lst
        ]
    )

    final_row = pd.concat([s_row_orig, g_row_orig], axis = 0)
    match_rows.append(final_row)

match_df = (
    pd.DataFrame(match_rows)
    # Sort by score increasing so we can see what must be fixed
    .sort_values("score")
)

t_stop = perf_counter()

t_elapsed = t_stop - t_start

print("Done matching.")
print(f"Time to match locations: {t_elapsed} s")

# Save the DF of matches
match_df.to_csv(
    "./private/cleaning_outputs/full_matches.csv",
    index = False,
)

match_df.head()

#%%
# Check the match df. I made this cell read the saved file so I can choose to run the cell without first running everything before it.
match_df = pd.read_csv("./private/cleaning_outputs/full_matches.csv")

match_df.loc[match_df.score < finest_level]