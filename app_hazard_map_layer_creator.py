# Hazard map layer creator UI

import streamlit as st
import pandas as pd
import numpy as np

from app_location_selector import location_selector_template

def hazard_map_feature(finest_level, gdf):

    # Set up selection list

    if "entries" not in st.session_state:
        st.session_state.entries = []

    def entries_present():
        """Returns True if there are entries recorded."""
        result = len(st.session_state.entries) > 0
        return result

    # Uploading
    st.markdown("## Upload Layer")

    uploaded_file = st.file_uploader(
        "Select a File (CSV)",
        type = "csv",
    )

    if uploaded_file is not None:
        up_df = pd.read_csv(uploaded_file)

        correct_columns = up_df.columns.tolist() == ["level", "category", "name", "gid"]

        if not correct_columns:
            st.warning("The format of this file is invalid.")
            st.stop()

        if st.button("Append this layer to the current layer"):
            list_of_dicts = up_df.to_dict(orient = "records")
            st.session_state.entries.extend(list_of_dicts)

    st.markdown("---")

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

        # df_container = st.container()
        st.markdown("## Delete Areas")

        if entries_present():
            # Let the user delete a chosen row.

            delete_index = st.number_input(
                "Choose a row number",
                min_value = 0,
                max_value = len(st.session_state.entries) - 1,
                value = 0,
            )
            
            if st.button("Delete the entry at the chosen row"):
                del st.session_state.entries[delete_index]

            if st.button("Delete all entries"):
                st.session_state.entries = []
        else:
            st.warning("No entries yet.")
    
    # Display the hazard map layer.
    # This must come last before saving so that it is immediately seen after any changes are made.
    st.markdown("---\n\n## View Areas")

    if entries_present():
        selection_df = pd.DataFrame(st.session_state.entries)
        st.dataframe(selection_df.loc[:, ["name", "category"]])
    else:
        st.warning("No entries yet.")

    # Saving and uploading
    st.markdown("---\n\n## Save Layer")

    if entries_present():
        filename = st.text_input(
            "Filename",
            value = "new_layer",
        )

        @st.cache(suppress_st_warning = True)
        def convert_df_for_download(df):
            """Convert a dataframe so that it can be downloaded using st.download_button()"""
            result = df.to_csv(index = False).encode("utf-8")
            return result

        csv = convert_df_for_download(selection_df)

        st.download_button(
            "Download hazard map layer as CSV",
            data = csv,
            file_name = f"{filename}.csv",
            mime = "text/csv",
        )
    else:
        st.warning("No entries yet.")