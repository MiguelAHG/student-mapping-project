# Report generator feature of app

import streamlit as st
import pandas as pd
import numpy as np

def report_generator_feature(finest_level, gdf, students_df):
    """Generates a report about the students who live in the hazard-affected areas."""

    st.markdown("## Report Generator")

    if ("entries" not in st.session_state) or (st.session_state.entries.shape[0] == 0):
        st.warning("There are no loaded entries yet in the hazard map layer.")
        st.stop()
    
    if not st.checkbox("Generate report"):
        st.stop()

    @st.cache(suppress_st_warning = True)
    def find_affected_students(finest_level, gdf, students_df):
        """Based on the hazard map layer, obtain a DF of all students in the affected areas."""
    
        # Label of finest level.
        finest_label = f"GID_{finest_level}"

        # Hazard map layer. Drop duplicates.
        hazmap = (
            st.session_state.entries
            .copy()
            .drop_duplicates(subset = "gid")
        )

        # Set of fine-grained GIDs.
        gid_set = set(
            hazmap.loc[
                hazmap.level == finest_level,
                "gid",
            ]
            .to_list()
        )

        # Iterate from 1 to the level BEFORE the finest level.
        for level_num in range(1, finest_level):
            subset = hazmap.loc[hazmap.level == level_num].copy()
            coarse_label = f"GID_{level_num}"

            # For each "coarse" area (e.g., province), obtain its "fine" GIDs (e.g., the GIDs of its barangays).
            # Then, update gid_set with the fine GIDs.
            for index, row in subset.iterrows():
                coarse_gid = row["gid"]
                fine_gid_series = gdf.loc[
                    gdf[coarse_label] == coarse_gid,
                    finest_label
                ]
                gid_set.update(fine_gid_series)

        affected_students_df = (
            students_df
            .loc[
                :, 
                # Columns to take
                [
                    "Student Name",
                    "OBF Email Address",
                    "Strand",
                    "Grade Level",
                    "Section",
                    "Class Number",
                ]
            ]
            # Sort rows
            .sort_values(by = [
                "Strand",
                "Grade Level",
                "Section",
                "Class Number",
            ])
            .reset_index(drop = True)
        )

        affected_students_df["affected"] = False

        affected_students_df.loc[
            # Mask of students affected by hazard
            students_df[finest_label].isin(gid_set),
            "affected"
        ] = True

        return affected_students_df

    affected_students_df = find_affected_students(finest_level, gdf, students_df)

    st.markdown("## Report")

    perc_affected = round(
        affected_students_df["affected"].sum()
        / affected_students_df.shape[0]
        * 100,
        2
    )

    st.metric(
        "Percentage of ASHS Students Affected",
        value = f"{perc_affected}%"
    )

    for strand_name in ["ABM", "GA", "HUMSS", "STEM"]:

        strand_subset = affected_students_df.loc[affected_students_df["Strand"] == strand_name]
        strand_total = strand_subset.shape[0]
        strand_affected = strand_subset["affected"].sum()
        strand_perc = round(
            strand_affected / strand_total * 100,
            2,
        )

        st.metric(
            f"Percentage of {strand_name} Students Affected",
            value = f"{strand_perc}%",
        )

    st.markdown("## Table of Students")

    display_df = (
        affected_students_df
        # Only display affected students
        .loc[affected_students_df["affected"]]
        # Drop bool column
        .drop("affected", axis = "columns")
    )

    st.dataframe(display_df)

    # Let the user save the table.
    st.markdown("## Save Table")

    filename = st.text_input(
        "Filename",
        value = "affected_students",
    )

    @st.cache(suppress_st_warning = True)
    def convert_df_for_download(df):
        """Convert a dataframe so that it can be downloaded using st.download_button()"""
        result = df.to_csv(index = False).encode("utf-8")
        return result

    csv = convert_df_for_download(display_df)

    st.download_button(
        "Download table of affected students as CSV",
        data = csv,
        file_name = f"{filename}.csv",
        mime = "text/csv",
    )