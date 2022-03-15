# Home page of app

import streamlit as st

def home_feature():
    st.markdown("""# Home Page

Welcome to the ASHS Student-Hazard App. Start by visiting the Hazard Map Layer Creator. When you are done making a layer, go to the Report Generator. You may go back to change the layer if needed. Also remember to save your layer and the report outputs. If you close or refresh this tab, your progress will be lost.""")

    with st.expander("Credits", expanded = False):
        st.markdown("""The Student Mapping Project is a collaboration between the Programming Varsity, the Kanlaon committee, and the school administration. The app itself was developed by Miguel Antonio H. Germar, ASHS Batch '22.

The app uses geospatial data from the GADM database to generate hazard maps of the Philippines. This data may be used for non-commercial purposes. The complete reference is provided below.

University of Berkeley, Museum of Vertebrate Zoology and the International Rice Research Institute. (2018, April). Global Administrative Areas (GADM) Version 3.4. GADM. https://gadm.org""")