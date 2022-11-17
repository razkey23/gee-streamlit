import streamlit as st
import leafmap.foliumap as leafmap
import ee

def app():
    st.title("Atmospheric Quality")

    st.markdown(
    """
    An interactive web app to see visualized data for several Earth Observation parameters 
    """
    )
    m = leafmap.Map(locate_control=True)
    m.add_basemap("ROADMAP")
    m.to_streamlit(height=700)
