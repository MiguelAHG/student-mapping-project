"""
Migs Germar, 2021
Main script for the Student Mapping Project app.
"""

import pandas as pd
import streamlit as st

# Cache the function that gets the data.
@st.cache(suppress_st_warning = True, allow_output_mutation = True)
def get_data():
    pass

if __name__ == "__main__":

    emoji = ":earth_asia:"

    st.set_page_config(
        page_title = "ASHS Student Map",
        page_icon = emoji,
        initial_sidebar_state = "expanded",
    )

    st.title(f"Student Map {emoji}")
    st.caption("Ateneo de Manila Senior High School")