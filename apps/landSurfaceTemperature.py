import streamlit as st
import ee
from datetime import date, timedelta
import datetime
import folium
import leafmap
import os
import json
import calendar
from apps.utils import download_button,general_utils,landSurfaceTemperature_utils
import pandas as pd
import plotly.tools as tls
import time



@st.experimental_memo
def convert_df(df):
   return df.to_csv(index=False).encode('utf-8')


def app():
    st.title("Land Surface Temperature")
    st.markdown(
    """
    Upload or Export a geojson for an area of interest (keep the size of the area reasonable) and retrieve Land Surface Temperature data 
    for that particular area in the selected timeframe
    """
    )
    serviceAccount = "earthenginealma@earth-engine-project-368208.iam.gserviceaccount.com"

    credentials = ee.ServiceAccountCredentials(serviceAccount,'credentials.json')
    #credentials = ee.ServiceAccountCredentials(serviceAccount, 'earth-engine-project-368208-162407f3fd49.json')
    ee.Initialize(credentials)


    row1_col1, row1_col2 = st.columns([4, 1])

    with row1_col2:
        with st.form("my_form"):
            with st.expander(label='Starting month'):
                this_year = datetime.date.today().year
                this_month = datetime.date.today().month
                start_year = st.selectbox('startYear', range(this_year, this_year - 8, -1),label_visibility="hidden")
                month_abbr = calendar.month_abbr[1:]
                start_month_str = st.radio('startMonth', month_abbr, index=this_month - 1, horizontal=True,label_visibility="hidden")
                start_month = month_abbr.index(start_month_str) + 1
            with st.expander(label='Ending month'):
                this_year = datetime.date.today().year
                this_month = datetime.date.today().month
                end_year = st.selectbox('endYear', range(this_year, this_year - 8, -1),label_visibility="hidden")
                month_abbr = calendar.month_abbr[1:]
                end_month_str = st.radio('endMonth', month_abbr, index=this_month - 1, horizontal=True,label_visibility="hidden")
                end_month = month_abbr.index(end_month_str) + 1
            data = st.file_uploader(
                "Upload a vector dataset", type=["geojson", "kml", "zip", "tab"]
            )
            frequency = st.selectbox(label='Frequency',options=['Daily','Weekly','Monthly'])
            functionality = st.selectbox(label='Analysis',options=['Map Visualization','Raw data & Plot'])
            

            
            submitted = st.form_submit_button("Submit")
            if submitted:
                if data: #Check if .geojson file was given
                    file_path = general_utils.save_uploaded_file(data, data.name)
                    layer_name = os.path.splitext(data.name)[0]
                    # Save the uploaded file
                    with open(file_path,'r') as f:
                        geom = json.load(f)
                        eegeom = general_utils.getGeometry(geom)
                    #frequency = 'Daily'

                    if functionality == 'Map Visualization':
                        #Visualize only first metric
                        m = landSurfaceTemperature_utils.mapVisualization(eegeom,start_year,start_month,end_year,end_month,frequency)
                    
                        with row1_col1:
                            m.add_child(folium.LayerControl())
                            m.to_streamlit(height=700)
                    else:
                        dataframe = landSurfaceTemperature_utils.getDataFrame(eegeom,start_year,start_month,end_year,end_month)
                        dataframe.to_csv('temporary.csv')
                        plot = landSurfaceTemperature_utils.createPlot(dataframe,frequency)
                        first_column = dataframe.pop('date')
                        dataframe.insert(0,'date',first_column)
                        dataframe = dataframe.reset_index(drop=True)
                        csv = convert_df(dataframe)
                    
                        with row1_col1:
                            st.plotly_chart(plot)
                            st.dataframe(dataframe)
                            download_button_str = download_button.download_button(csv,"file.csv","Press To Download")
                            st.markdown(download_button_str, unsafe_allow_html=True)

            else:
                with row1_col1:
                    m = leafmap.foliumap.Map(zoom_start=2,draw_export=True)
                    m.to_streamlit(height=700)