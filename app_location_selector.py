# Location selector feature

import streamlit as st
import pandas as pd
import numpy as np

def location_selector_template(finest_level, gdf, inner_func = None, key = "location_selector"):
    """Template function for location selector. Returns the GID and the list of the parts of the location name.
inner_func: provide a function and it will be run at the bottom of each selectbox."""

    # List of columns to take from GDF.
    # Should include only GID and NAME columns down to the finest level.
    gdf_cols = [
        s.format(level)
        for level in range(1, finest_level + 1)
        for s in ["GID_{}", "NAME_{}"]
    ]

    gdf_subset = gdf[gdf_cols].copy()

    categories = pd.Series(
        {
            1: "province",
            2: "city or municipality",
            3: "barangay",
        }
    )

    categories = categories.loc[:finest_level]

    gid_list = []

    # Note that "name" here refers to location name.
    name_list = []

    for level in range(1, finest_level + 1):
        name_label = f"NAME_{level}"
        gid_label = f"GID_{level}"
        cat = categories[level]

        cur_name = st.selectbox(
            cat.title(),
            options = gdf_subset[name_label].unique(),
            # Use a key so that multiple instances of location selectors are not connected.
            key = key + " " + "/".join(gid_list),
        )

        gdf_subset = gdf_subset.loc[gdf_subset[name_label] == cur_name]

        gid = (gdf_subset.loc[:, gid_label].iloc[0])

        gid_list.append(gid)
        name_list.append(cur_name)

        if inner_func is not None:
            inner_func(level, cat, gid, name_list)

    return gid, name_list