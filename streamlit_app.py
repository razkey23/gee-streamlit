import streamlit as st
from streamlit_option_menu import option_menu
from apps import home, landSurfaceTemperature, upload,nightlights,atmospheric,waterQuality  # import your app modules here

st.set_page_config(page_title="Streamlit Geospatial", layout="wide")

# A dictionary of apps in the format of {"App title": "App icon"}
# More icons can be found here: https://icons.getbootstrap.com

apps = [
    {"func": home.app, "title": "Home", "icon": "house"},
    {"func": landSurfaceTemperature.app, "title": "Land Surface Temperature", "icon": "map"},
    {"func": nightlights.app, "title": "Nightlight Activity", "icon": "lamp-fill"},
    {"func": atmospheric.app, "title": "Atmospheric Quality", "icon": "globe2"},
    {"func": waterQuality.app, "title": "Water Quality", "icon": "water"},
]

titles = [app["title"] for app in apps]
titles_lower = [title.lower() for title in titles]
icons = [app["icon"] for app in apps]

params = st.experimental_get_query_params()

if "page" in params:
    default_index = int(titles_lower.index(params["page"][0].lower()))
else:
    default_index = 0









# Used to hide hamburger Menu
hide_streamlit_style = """
            <style>
            #MainMenu {visibility: hidden;}
            footer {visibility: hidden;}
            </style>
            """
st.markdown(hide_streamlit_style, unsafe_allow_html=True) 

with st.sidebar:
    selected = option_menu(
        "Main Menu",
        options=titles,
        icons=icons,
        menu_icon="cast",
        default_index=default_index,
    )

    
    
     
    st.markdown( 
        """
            <div style="bottom:-500px; position:absolute;">
                <h3 style="margin-top:0; text-align:center;">Economy bY spacE (EYE)<h3>
                <img src="https://i.imgur.com/x9fJelE.png" width="100%" style="margin-top:0; position:absolute;"/>
                <p style="margin-top:120px; font-size:70%">
                Marie Skłodowska-Curie Actions (MSCA)  Research and Innovation Staff Exchange (RISE) H2020-MSCA-RISE-2020 G.A. 101007638
                </p>
                <!-- 
                <img src="https://i.imgur.com/yEF6GB3.png" width="100%" style="bottom:0px; position:relative;"/>
                -->
                
            </div>
        """
    ,unsafe_allow_html=True)
   


for app in apps:
    if app["title"] == selected:
        app["func"]()
        break
