# Hazard map layer creator UI

import streamlit as st
import pandas as pd
import numpy as np

from app_location_selector import location_selector_template

def hazard_map_feature(finest_level, gdf):

    # Set up selection list

    if "entries" not in st.session_state:
        st.session_state.entries = []

    # Begin selection system

    cols = st.columns(2)

    with cols[0]:

        st.markdown("## Select Areas")

        def add_button(level, cat, name, gid):
            """Button that lets the user add the selected location to the hazard map layer. This is used in the location selector template."""

            if st.button(f"Add entire {cat} to selection", key = f"button {level}"):

                new_row = {
                    "level": level,
                    "category": cat,
                    "name": name,
                    "gid": gid,
                }

                st.session_state.entries.append(new_row)

        location_selector_template(finest_level, gdf, inner_func = add_button)

    with cols[1]:

        st.markdown("## View Selected Areas")

        df_container = st.container()

        if len(st.session_state.entries) > 0:
            # Let the user delete a chosen row.
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
            if len(st.session_state.entries) > 0:
                selection_df = pd.DataFrame(st.session_state.entries)
                st.dataframe(selection_df.loc[:, ["name", "category"]])
            else:
                st.markdown("No entries yet")
    
    # Saving and uploading
    st.markdown("---\n\n## Saving and Uploading Options")

    st.markdown("### Save Layer")
    filename = st.text_input(
        "Filename",
        value = "new_layer",
    )

    if st.button("Save hazard map layer as CSV"):
        pass