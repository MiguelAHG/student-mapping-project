# Report generator feature of app

import streamlit as st
import pandas as pd
import numpy as np
import altair as alt

def report_generator_feature(finest_level, gdf, students_df):
    """Generates a report about the students who live in the hazard-affected areas."""

    st.markdown("# Report Generator")

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

        affected_students_df["Affected"] = False

        affected_students_df.loc[
            # Mask of students affected by hazard
            students_df[finest_label].isin(gid_set),
            "Affected"
        ] = True

        return affected_students_df

    affected_students_df = find_affected_students(finest_level, gdf, students_df)

    st.markdown("## Percentages")

    perc_affected = round(
        affected_students_df["Affected"].sum()
        / affected_students_df.shape[0]
        * 100,
        2
    )

    st.metric(
        "Percentage of ASHS Students Affected",
        value = f"{perc_affected}%"
    )

    bullet_lst = []
    for strand_name in ["ABM", "GA", "HUMSS", "STEM"]:

        strand_subset = affected_students_df.loc[affected_students_df["Strand"] == strand_name]
        strand_total = strand_subset.shape[0]
        strand_affected = strand_subset["Affected"].sum()
        strand_perc = round(
            strand_affected / strand_total * 100,
            2,
        )
        bullet = f"- Percentage of {strand_name}: {strand_perc}%"
        bullet_lst.append(bullet)

    strand_percs = "\n".join(bullet_lst)
    st.markdown(strand_percs)

    # Chart
    st.markdown("## Bar Chart")

    chart_df = affected_students_df.copy()
    chart_df["Affected"] = chart_df["Affected"].replace({
        False: "No",
        True: "Yes",
    })
    
    chart = (
        alt.Chart(chart_df)
        .mark_bar()
        .encode(
            x = alt.X("Strand:N"),
            y = alt.Y("count():Q", title = "Number of Students"),
            color = alt.Color("Affected:N", scale = alt.Scale(scheme = "paired")),
            tooltip = [
                alt.Tooltip("Strand:N"),
                alt.Tooltip("Affected:N"),
                alt.Tooltip("count():Q", title = "Number of Students"),
            ]
        )
        .properties(
            title = "Number of Affected Students by Strand",
            height = 400,
        )
        .configure_axis(
            labelFontSize = 18,
            labelAngle = 0,
        )
        .interactive()
    )

    st.altair_chart(chart, use_container_width = True)

    st.markdown("## Table of Affected Students")

    display_df = (
        affected_students_df
        # Only display affected students
        .loc[affected_students_df["Affected"]]
        # Drop bool column
        .drop("Affected", axis = "columns")
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