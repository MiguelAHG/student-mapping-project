# Hazard map layer creator UI

import streamlit as st
import pandas as pd
import numpy as np

from app_location_selector import location_selector

def hazard_map_feature(finest_level, gdf):

    # Set up list of selected areas affected by a hazard
    if "entries" not in st.session_state:
        st.session_state.entries = pd.DataFrame()

    def entries_present():
        """Returns True if there are entries recorded."""
        result = st.session_state.entries.shape[0] > 0
        return result

    st.markdown("# Hazard Map Layer Creator")

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

            st.session_state.entries = pd.concat(
                [st.session_state.entries, up_df],
                axis = 0,
            ).reset_index(drop = True)

    st.markdown("---")

    # Begin selection system

    cols = st.columns(2)

    with cols[0]:

        st.markdown("## Select Areas")

        location_selector(
            finest_level,
            gdf,
            key = "location selector - hazard map layer creator",
        )

    with cols[1]:

        st.markdown("## Delete Areas")

        # An Empty contains one element, which may be replaced.
        deletion_empty = st.empty()
        
        # If there are entries, give the user options to delete them.
        if entries_present():
            
            # Use a Container to place multiple widgets inside the Empty.
            with deletion_empty.container():

                delete_index = st.number_input(
                    "Choose a row number",
                    min_value = 0,
                    max_value = len(st.session_state.entries) - 1,
                    value = 0,
                )
                
                if st.button("Delete the entry at the chosen row"):
                    st.session_state.entries = st.session_state.entries.drop(
                        delete_index,
                        axis = 0,
                    ).reset_index(
                        drop = True,
                    )

                if st.button("Delete the most recently added entry"):
                    st.session_state.entries.drop(
                        index = st.session_state.entries.index[-1],
                        axis = 0,
                        inplace = True,
                    )

                if st.button("Delete all entries"):
                    st.session_state.entries = pd.DataFrame()

        # I used a new if-clause.
        # If a deletion action leaves the layer empty, this will immediately remove the deletion options and put a Warning instead.
        if not entries_present():
            deletion_empty.warning("No entries yet.")
    
    # Display the hazard map layer.
    # This must come last before saving so that it is immediately seen after any changes are made.
    st.markdown("---\n\n## View Areas")

    if entries_present():
        display_entries_df = st.session_state.entries.loc[:, ["name", "category"]]
        st.dataframe(display_entries_df)
    else:
        st.warning("No entries yet.")

    # Saving and uploading
    st.markdown("---\n\n## Save Layer")

    if entries_present():
        filename = st.text_input(
            "Filename",
            value = "new_layer",
        )

        @st.cache_data(ttl = None)
        def convert_df_for_download(df):
            """Convert a dataframe so that it can be downloaded using st.download_button()"""
            result = df.to_csv(index = False).encode("utf-8")
            return result

        csv = convert_df_for_download(st.session_state.entries)

        st.download_button(
            "Download hazard map layer as CSV",
            data = csv,
            file_name = f"{filename}.csv",
            mime = "text/csv",
        )
    else:
        st.warning("No entries yet.")