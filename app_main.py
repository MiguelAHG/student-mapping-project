"""
Migs Germar, 2021
Main script for the Student Mapping Project app.
"""

import pandas as pd
import geopandas as gpd
import streamlit as st

# Cache the function that gets the data.
@st.cache(suppress_st_warning = True, allow_output_mutation = True)
def get_data():
    gpkg = "./geo_data/gadm36_PHL.gpkg"
    gdf = gpd.read_file(gpkg, layer = "gadm36_PHL_3")
    return gdf

if __name__ == "__main__":

    emoji = ":earth_asia:"

    st.set_page_config(
        page_title = "ASHS Student-Hazard App",
        page_icon = emoji,
        initial_sidebar_state = "expanded",
    )

    st.title(f"ASHS Student-Hazard App {emoji}")

    gdf = get_data()

    gdf_cols = [
        "GID_1",
        "NAME_1",
        "GID_2",
        "NAME_2",
        "GID_3",
        "NAME_3",
    ]

    gdf = gdf.loc[:, gdf_cols]

    # Set up selection list

    if "entries" not in st.session_state:
        st.session_state.entries = []

    # Begin selection system

    categories = {
        1: "province",
        2: "city or municipality",
        3: "barangay",
    }

    part_list = []

    cols = st.columns(2)

    with cols[0]:

        st.markdown("## Select Areas")

        for level in range(1, 4):
            name_label = f"NAME_{level}"
            gid_label = f"GID_{level}"
            cat = categories[level]

            name = st.selectbox(
                cat.title(),
                options = gdf[name_label].unique(),
                key = "/".join(part_list),
            )

            gdf = gdf.loc[gdf[name_label] == name]

            gid = (gdf.loc[:, gid_label].iloc[0])

            part_list.append(gid)

            if level <= 2:
                next_cat = categories[level + 1]

                radio = st.radio(
                    "Selection Choice",
                    options = [f"Select entire {cat}", f"Select a {next_cat}"],
                    key = f"{level} radio",
                )

                if radio == f"Select entire {cat}":
                    break
        
        if st.button("Add to selection"):

            new_row = {
                "level": level,
                "category": cat,
                "name": name,
                "gid": gid,
            }

            st.session_state.entries.append(new_row)

    with cols[1]:

        st.markdown("## View Selected Areas")

        if len(st.session_state.entries) > 0:
            df_container = st.container()

            # This part is buggy
            st.markdown("## Deletion Options")

            delete_index = st.number_input(
                "Choose a row number",
                min_value = 0,
                max_value = len(st.session_state.entries) - 1,
                value = 0,
            )
            
            if st.button("Delete the entry at the chosen row"):
                del st.session_state.entries[delete_index]

            with df_container:
                selection_df = pd.DataFrame(st.session_state.entries)
                st.dataframe(selection_df.loc[:, ["name", "category"]])
        else:
            st.markdown("No entries yet")