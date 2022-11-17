import streamlit as st
import leafmap.foliumap as leafmap


def app():

    st.title("Land Surface Temperature")
    
    row1_col1, row1_col2 = st.columns([3, 1]) 


    filepath = "https://raw.githubusercontent.com/giswqs/leafmap/master/examples/data/us_cities.csv"
    m = leafmap.Map(tiles="stamentoner")
    m.add_heatmap(
        filepath,
        latitude="latitude",
        longitude="longitude",
        value="pop_max",
        name="Heat map",
        radius=20,
    )
    m.to_streamlit(height=700)
