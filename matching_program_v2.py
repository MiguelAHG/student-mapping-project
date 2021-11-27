#%% Import

import pandas as pd
import numpy as np
import Levenshtein
import geopandas as gpd

#%% Get data
gpkg = "./geo_data/gadm36_PHL.gpkg"

# Use the finest layer, number 3
gdf = gpd.read_file(gpkg, layer = "gadm36_PHL_3")
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
    student_df["obf_email"]
    # keep = False so all duplicates are marked True
    .duplicated(keep = False)
]

print(dupes.shape[0])

dupes

#%%
# Delete rows with empty cells. This is temporary. For the real thing, we have to make sure all barangays and cities are complete in the data.

student_df = (
    student_df
    .dropna(subset = ["barangay", "city_municipality", "province"])
    .reset_index(drop = True)
)

student_df.info()
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

# DF of student DF labels and their GADM equivalents

label_df = pd.DataFrame([
    [1, "province", "NAME_1"],
    [2, "city_municipality", "NAME_2"],
    [3, "barangay", "NAME_3"]
])

label_df.columns = ["level", "students", "gadm"]

label_df = label_df.set_index("level")

# Choose whether to go down to barangay level (3) or only city level (2).
finest_level = 3

label_df = label_df.iloc[:finest_level + 1]
gid_label = f"GID_{finest_level}"

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
s_label_lst = label_df["students"].tolist()

# Make this True to save files (students)
save_student_pp = True

if save_student_pp:
    p_filename = "student_df_preprocessed"
    c_filename = "student_df_comparison"
else:
    p_filename = None
    c_filename = None

student_df_pp = full_preprocess(
    student_df,
    s_label_lst,
    p_filename = p_filename,
    c_filename = c_filename,
)

# GADM data preprocessing
g_label_lst = label_df["gadm"].tolist()

# Make this True to save files (GADM)
save_gadm_pp = False

if save_gadm_pp:
    p_filename = "gadm_df_preprocessed"
    c_filename = "gadm_df_comparison"
else:
    p_filename = None
    c_filename = None

gadm_df_pp = full_preprocess(
    gdf,
    g_label_lst,
    p_filename = p_filename,
    c_filename = c_filename,
)

# %%
# For each student location, find a match in GADM.

def lvratio(s1, s2, memo = {}):
    """Given two strings, return the Levenshtein score. Memoized."""

    args_tup = (s1, s2)

    if args_tup in memo:
        return memo[args_tup]

    score = Levenshtein.ratio(*args_tup)
    memo[args_tup] = score

    return score

def full_match(s_row, memo = {}):
    """Given the student's full location, find the GADM location that best matches. Note that s_row is only a tuple, not a Series.
    
    memo: Keys are full location names in the form of Series. Values contain the score, GADM index, and NAME_s of the the best match."""
    
    if s_row in memo:
        return memo[s_row]

    score_per_location = []

    # Iterate through GADM rows
    for g_index, g_row in gdf[g_label_lst].iterrows():
        score_per_level = []

        # Iterate through levels
        for level in range(1, finest_level + 1):
            g_label = label_df.at[level, "gadm"]

            s_text = s_row[level - 1]
            g_text = g_row[g_label]

            score = lvratio(s_text, g_text)
            score_per_level.append(score)

        # Break if perfect score is found
        if np.sum(score_per_level) == 3.0:
            highest_score = 3.0
            match_index = g_index
            break

        score_per_location.append((score, g_index))

    else:
        # If a perfect score is not found, settle for the highest score.
        scores_df = pd.DataFrame(score_per_location)
        scores_df.columns = ("score", "g_index")

        highest_row = scores_df.iloc[scores_df["score"].argmax()]
        highest_score, match_index = highest_row

    # Store result in memo
    result = (highest_score, match_index)
    memo[s_row] = result

    return result

# Final list of matches, will become DF
match_rows = []

# Iterate through student locations
for s_index, s_row in student_df_pp.iterrows():

    highest_score, g_index = full_match(tuple(s_row))
    g_index = int(g_index)

    g_row_orig = gdf.iloc[g_index].loc[g_label_lst + [gid_label]]
    g_row_orig["score"] = highest_score

    s_row_orig = (
        student_df
        .iloc[s_index]
        .loc[
            ["full_name", "obf_email", "strand", "grade_level", "section"] + s_label_lst
        ]
    )

    final_row = pd.concat([s_row_orig, g_row_orig], axis = 0)
    match_rows.append(final_row)

match_df = (
    pd.DataFrame(match_rows)
    # Sort by score increasing so we can see what must be fixed
    .sort_values("score")
)

# Save the DF of matches
match_df.to_csv(
    "./private/cleaning_outputs/full_matches.csv",
    index = False,
)

match_df.head()

#%%
# Check the match df. I made this cell read the saved file so I can run the cell without first running everything before it.
match_df = pd.read_csv("./private/cleaning_outputs/full_matches.csv")

match_df.loc[match_df.score < 3]