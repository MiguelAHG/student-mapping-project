# A feature that shows the list of areas where at least one student lives.

import pandas as pd
import geopandas as gpd
import streamlit as st
import plotly.express as px

def student_areas_feature(finest_level, gdf, students_df):
    st.markdown("# Student-populated Areas")
    st.markdown("This page shows the list of areas where at least one student lives. Refer to this list while researching about areas affected by a hazard. It will help you avoid spending time adding unnecessary items to the Hazard Map Layer.")

    finest_gid_label = f"GID_{finest_level}"

    finest_name_label = f"NAME_{finest_level}"

    name_categories = pd.Series(
        {
            "NAME_1": "Province",
            "NAME_2": "City or Municipality",
            "NAME_3": "Barangay",
        }
    )

    name_categories = name_categories.iloc[0:finest_level]

    name_cols = name_categories.index.tolist()
    display_cols = name_categories.to_list()

    # Set of GIDs of areas populated by students
    populated_gids = set(
        students_df[finest_gid_label]
        .drop_duplicates(keep = "first")
        .to_list()
    )

    # List of columns to keep in gdf_populated. geometry column contains geospatial data.
    keep_cols = name_cols + [finest_gid_label, "geometry"]

    # GADM entries of populated areas
    gdf_populated = (
        gdf
        .loc[
            gdf[finest_gid_label].isin(populated_gids),
            keep_cols
        ]
        .rename(columns = name_categories)
        .set_index(finest_gid_label)
    )

    # Display the table of areas

    st.markdown("## Table")

    display_df = gdf_populated.loc[:, display_cols].reset_index(drop = True)

    st.dataframe(display_df)

    # Let the user download the table
    @st.cache(suppress_st_warning = True)
    def convert_df_for_download(df):
        """Convert a dataframe so that it can be downloaded using st.download_button()"""
        result = df.to_csv(index = False).encode("utf-8")
        return result

    csv = convert_df_for_download(display_df)

    st.download_button(
        "Download table as CSV",
        data = csv,
        file_name = f"student_populated_areas.csv",
        mime = "text/csv",
    )

    # Display map

    st.markdown("## Map")

    # Specify the variable containing the name of each area on the map. This is the variable associated with the finest level.
    hover_name = name_categories.loc[finest_name_label]

    # Specify the list of variables to be shown in the hover tooltip. This includes the variables from the coarsest level down to one level above the finest level.
    hover_data = name_categories.iloc[0:(finest_level - 1)]

    fig = px.choropleth_mapbox(
        gdf_populated,
        geojson = gdf_populated.geometry,
        locations = gdf_populated.index,
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