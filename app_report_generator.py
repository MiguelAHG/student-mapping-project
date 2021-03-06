# Report generator feature of app

import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px

def report_generator_feature(finest_level, gdf, students_df):
    """Generates a report about the students who live in the hazard-affected areas."""

    st.markdown("# Report Generator")
    st.markdown("Ensure that the hazard map layer is complete before saving these results.")

    if ("entries" not in st.session_state) or (st.session_state.entries.shape[0] == 0):
        st.warning("There are no entries yet in the hazard map layer.")
        st.stop()

    # Hazard map layer. Drop duplicates.
    hazmap = (
        st.session_state.entries
        .copy()
        .drop_duplicates(subset = "gid", keep = "first")
    )

    name_labels = [f"NAME_{i}" for i in range(1, finest_level + 1)]

    # Label of finest level.
    finest_label = f"GID_{finest_level}"

    finest_name_label = f"NAME_{finest_level}"

    @st.cache(suppress_st_warning = True)
    def identify_affected(finest_level, finest_label, gdf, students_df, hazmap, name_labels):
        """Based on the hazard map layer, obtain a DF of all students in the affected areas."""

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
                student_info_cols + [finest_label]
            ]
            # Sort rows
            .sort_values(by = student_info_cols)
            .reset_index(drop = True)
            # Include location names
            .merge(
                gdf[name_labels + [finest_label]],
                how = "left",
                left_on = finest_label,
                right_on = finest_label
            )
        )

        # Mask of students affected by hazard
        affected_df["affected_bool"] = affected_df[finest_label].isin(gid_set)

        # Column of Yes or No strings
        affected_df["affected"] = affected_df["affected_bool"].replace({True: "Yes", False: "No"})

        return affected_df, gid_set

    affected_df, gid_set = identify_affected(finest_level, finest_label, gdf, students_df, hazmap, name_labels)

    st.markdown("## Main Statistics")

    num_affected = affected_df["affected_bool"].sum()
    perc_affected = round(
        num_affected / affected_df.shape[0] * 100,
        2
    )

    cols = st.columns(2)
    with cols[0]:
        st.metric(
            "Number of ASHS Students Affected",
            value = f"{num_affected}",
        )
    with cols[1]:
        st.metric(
            "Percentage of ASHS Students Affected",
            value = f"{perc_affected}%",
        )

    if num_affected == 0:
        st.warning("No students are affected by this hazard, so a report has not been generated.")
        st.stop()

    # Map feature
    st.markdown("## Map of the Philippines")
    st.markdown("Colored areas indicate areas affected by the hazard. Uncolored areas indicate areas not affected. The hue of each area indicates how many ASHS students are affected; refer to the legend. Not all affected areas have ASHS students.\n\nHover over a city to see its name and the exact number of students affected. Pan by dragging with the left mouse button. Zoom in and out with the scroll wheel. To save a photo, adjust the pan and zoom to the desired area. Then, hover over the top right of the image and click the camera button (Download plot as a png).")
    
    affected_per_city = (
        affected_df
        .loc[affected_df["affected_bool"]]
        .pivot_table(
            index = finest_label,
            values = "affected_bool",
            aggfunc = np.sum,
        )
        .rename(columns = {"affected_bool": "number_affected"})
    )

    map_df = (
        gdf
        .loc[
            gdf[finest_label].isin(gid_set),
            name_labels + ["geometry", finest_label]
        ]
        .merge(
            affected_per_city,
            how = "left",
            left_on = finest_label,
            right_index = True,
        )
    )

    map_df["number_affected"] = map_df["number_affected"].fillna(0)

    # Series of name labels and their corresponding categories
    name_categories = pd.Series(
        {
            "NAME_1": "Province",
            "NAME_2": "City or Municipality",
            "NAME_3": "Barangay",
        }
    )

    name_categories = name_categories.iloc[0:finest_level]

    # Series used to rename columns in the dataframe
    renaming_series = name_categories.copy()
    renaming_series["number_affected"] = "Number of Affected ASHS Students"

    # Rename columns
    map_df = (
        map_df.rename(columns = renaming_series)
        .set_index(finest_label, drop = True)
    )

    # Specify the variable containing the name of each area on the map. This is the variable associated with the finest level.
    hover_name = name_categories.loc[finest_name_label]

    # Specify the list of variables to be shown in the hover tooltip. This includes the variables from the coarsest level down to one level above the finest level.
    coarse_categories = name_categories.iloc[0:(finest_level - 1)].to_list()
    hover_data = coarse_categories + ["Number of Affected ASHS Students"]

    # Make map

    fig = px.choropleth_mapbox(
        map_df,
        geojson = map_df.geometry,
        locations = map_df.index,
        color = "Number of Affected ASHS Students",
        color_continuous_scale = "Viridis",
        range_color = None,
        mapbox_style = "carto-positron",
        zoom = 4.2,
        center = {"lat": 12.879721, "lon": 121.774017},
        opacity = 0.5,
        hover_name = hover_name,
        hover_data = hover_data,
    )
    fig.update_layout(margin={"r":0,"t":0,"l":0,"b":0})
    
    st.plotly_chart(fig)

    st.markdown("## Table of Affected Students")

    display_df = (
        affected_df
        # Only display affected students
        .loc[
            affected_df["affected_bool"],
            [
                "strand",
                "grade_level",
                "section",
                "student_number",
            ],
        ]
        .reset_index(drop = True)
    )

    st.dataframe(display_df)

    # Let the user save the table.
    st.markdown("## Save Table")
    st.markdown("Note that the table shown above includes only affected students. On the other hand, the table that is downloaded will include all ASHS students. A column will indicate whether each student is affected by the hazard or not.\n\nAlso, the CSV file is a text file that can be opened in Excel as a spreadsheet. Use 'Save As' to change its file type.")

    filename = st.text_input(
        "Filename (without extension)",
        value = "hazard_mapping_results",
    )

    save_df = (
        affected_df
        [["strand", "grade_level", "section", "student_number", "affected"]]
        .copy()
    )

    @st.cache(suppress_st_warning = True)
    def convert_df_for_download(df):
        """Convert a dataframe so that it can be downloaded using st.download_button()"""
        result = df.to_csv(index = False).encode("utf-8")
        return result

    csv = convert_df_for_download(save_df)

    st.download_button(
        "Download complete table as CSV",
        data = csv,
        file_name = f"{filename}.csv",
        mime = "text/csv",
    )