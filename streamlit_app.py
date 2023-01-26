import streamlit as st
from streamlit_option_menu import option_menu
from apps import home, landSurfaceTemperature, upload,nightlights,atmospheric,waterQuality  # import your app modules here
import json

st.set_page_config(page_title="Streamlit Geospatial", layout="wide")
st.markdown(
            f'''
            <style>
                .reportview-container .sidebar-content {{
                    padding-top: {1}rem;
                }}
                .reportview-container .main .block-container {{
                    padding-top: {1}rem;
                }}
            </style>
            ''',unsafe_allow_html=True)
#st.components.v1.html('<link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/bootstrap-icons@1.9.1/font/bootstrap-icons.css">')

# A dictionary of apps in the format of {"App title": "App icon"}
# More icons can be found here: https://icons.getbootstrap.com
#{"func": upload.app, "title": "Ship Detection", "icon": "tsunami"},
#{"func": upload.app, "title": "Plane Detection", "icon":"gear"},

apps = [
    {"func": home.app, "title": "Home", "icon": "house"},
    {"func": landSurfaceTemperature.app, "title": "Land Surface Temperature", "icon": "map"},
    {"func": nightlights.app, "title": "Nightlight Activity", "icon": "lamp-fill"},
    {"func": atmospheric.app, "title": "Atmospheric Quality", "icon": "globe2"},
    {"func": waterQuality.app, "title": "Water Quality", "icon": "water"},
]

newDic={}
for key in st.secrets['eecredentials']:
    newDic[key.replace("eecredentials_","")] = st.secrets['eecredentials'][key]
#json_object = json.dumps(newDic, indent = 4)   
with open('credentials.json', 'w') as outfile:
    json.dump(newDic, outfile)

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
    st.markdown( 
        """
            <link rel="stylesheet" href="cdn.jsdelivr.net/npm/bootstrap-icons@1.10.2/font/…">
        """
    ,unsafe_allow_html=True)
    selected = option_menu(
        "Main Menu",
        options=titles,
        icons=icons,
        menu_icon="cast",
        default_index=default_index,
    )

    
    
     
    st.markdown( 
        """
            <link rel="stylesheet" href="cdn.jsdelivr.net/npm/bootstrap-icons@1.10.2/font/…">
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
