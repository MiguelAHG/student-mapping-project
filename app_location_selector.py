# Location selector feature

import streamlit as st
import pandas as pd
import numpy as np

def location_selector_template(finest_level, gdf, inner_func = None, key = "location_selector"):
    """Template function for location selector. Returns the GID and the list of the parts of the location name.
inner_func: provide a function and it will be run at the bottom of each selectbox."""

    gdf_cols = [
        "GID_1",
        "NAME_1",
        "GID_2",
        "NAME_2",
        "GID_3",
        "NAME_3",
    ]

    gdf_subset = gdf.loc[:, gdf_cols].copy()

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
            inner_func(level, cat, cur_name, gid, name_list)

    return gid, name_list

def location_selector_feature(finest_level, gdf):
    """The location selector page of the web app."""

    st.markdown("# Location Selector")

    gid, name_list = location_selector_template(
        finest_level,
        gdf,
        key = "location selector - feature",
    )

    full_location_name = ", ".join(reversed(name_list))

    # Display the full location name and GID.
    # Provide a button to copy each of these to the clipboard.

    display_dict = {
        "Name": full_location_name,
        "GID": gid,
    }

    for dct_key in display_dict:
        dct_value = display_dict[dct_key]

        st.markdown(f"Location {dct_key}: **{dct_value}**")

        clipboard_button = st.button(
            f"Copy {dct_key} to Clipboard",
            key = dct_key,
        )

        if clipboard_button:
            cb_df = pd.DataFrame([dct_value])
            cb_df.to_clipboard(index = False, header = False)