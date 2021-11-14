"""
Migs Germar, 2021
Main script for the Student Mapping Project app.
"""

import pandas as pd
import geopandas as gpd
import streamlit as st

# Custom imports for app features
from app_home import home_feature
from app_hazard_map_layer_creator import hazard_map_feature
from app_location_selector import location_selector_feature
from app_report_generator import report_generator_feature

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

    # Set this to 3 for barangay and 2 for city.
    finest_level = 3

    with st.sidebar:
        feature = st.radio(
            "App Feature",
            options = [
                "Home Page",
                "Location Selector",
                "Hazard Map Layer Creator",
                "Report Generator",
            ]
        )

    if feature == "Home Page":
        home_feature()
    
    elif feature == "Location Selector":
        location_selector_feature(finest_level, gdf)

    elif feature == "Hazard Map Layer Creator":
        hazard_map_feature(finest_level, gdf)
    
    elif feature == "Report Generator":
        report_generator_feature()
