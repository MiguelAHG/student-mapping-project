# Report generator feature of app

import streamlit as st
import pandas as pd
import numpy as np
import altair as alt

def report_generator_feature(finest_level, gdf, students_df):
    """Generates a report about the students who live in the hazard-affected areas."""

    st.markdown("# Report Generator")
    st.markdown("Ensure that the hazard map layer is complete before saving these results.")

    if ("entries" not in st.session_state) or (st.session_state.entries.shape[0] == 0):
        st.warning("There are no entries yet in the hazard map layer.")
        st.stop()

    @st.cache(suppress_st_warning = True)
    def find_affected_students(finest_level, gdf, students_df, hazmap):
        """Based on the hazard map layer, obtain a DF of all students in the affected areas."""
    
        # Label of finest level.
        finest_label = f"GID_{finest_level}"

        # Set of fine-grained GIDs.
        gid_set = set(
            hazmap.loc[
                hazmap.level == finest_level,
                "gid",
            ]
            .to_list()
        )

        # Iterate through all coarse levels.
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

        student_info_cols = [
            "strand",
            "grade_level",
            "section",
            "student_number",
        ]

        affected_df = (
            students_df
            .loc[
                :, 
                student_info_cols
            ]
            # Sort rows
            .sort_values(by = student_info_cols)
            .reset_index(drop = True)
        )

        # Mask of students affected by hazard
        affected_df["affected_bool"] = students_df[finest_label].isin(gid_set)

        # Column of Yes or No strings
        affected_df["affected"] = affected_df["affected_bool"].replace({True: "Yes", False: "No"})

        return affected_df

    # Hazard map layer. Drop duplicates.
    hazmap = (
        st.session_state.entries
        .copy()
        .drop_duplicates(subset = "gid")
    )

    affected_df = find_affected_students(finest_level, gdf, students_df, hazmap)

    st.markdown("## Percentages")

    perc_affected = round(
        affected_df["affected_bool"].sum()
        / affected_df.shape[0]
        * 100,
        2
    )

    st.metric(
        "Percentage of ASHS Students Affected",
        value = f"{perc_affected}%"
    )

    bullet_lst = []
    for strand_name in ["ABM", "GA", "HUMSS", "STEM"]:

        strand_subset = affected_df.loc[affected_df["strand"] == strand_name]
        strand_total = strand_subset.shape[0]
        strand_affected = strand_subset["affected_bool"].sum()
        strand_perc = round(
            strand_affected / strand_total * 100,
            2,
        )
        bullet = f"- Percentage of {strand_name}: {strand_perc}%"
        bullet_lst.append(bullet)

    strand_percs = "\n".join(bullet_lst)
    st.markdown(strand_percs)

    st.markdown("## Table of Affected Students")

    display_df = (
        affected_df
        # Only display affected students
        .loc[affected_df["affected_bool"]]
        .reset_index(drop = True)
        # Drop columns about being affected
        .drop(["affected_bool", "affected"], axis = "columns")
    )

    st.dataframe(display_df)

    # Let the user save the table.
    st.markdown("## Save Table")

    filename = st.text_input(
        "Filename (without extension)",
        value = "hazard_mapping_results",
    )

    @st.cache(suppress_st_warning = True)
    def convert_df_for_download(df):
        """Convert a dataframe so that it can be downloaded using st.download_button()"""
        result = df.to_csv(index = False).encode("utf-8")
        return result

    save_df = affected_df[["strand", "grade_level", "section", "student_number", "affected"]].copy()

    csv = convert_df_for_download(save_df)

    st.download_button(
        "Download complete table as CSV",
        data = csv,
        file_name = f"{filename}.csv",
        mime = "text/csv",
    )