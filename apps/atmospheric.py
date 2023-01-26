import streamlit as st
import ee
from datetime import date, timedelta
import datetime
import folium
import leafmap
import os
import json
import calendar
from apps.utils import download_button,general_utils,atmosphericQuality_utils
import pandas as pd
import plotly.tools as tls
import time

# Add EE drawing method to folium.
leafmap.foliumap.Map.add_ee_layer = general_utils.add_ee_layer


@st.experimental_memo
def convert_df(df):
   return df.to_csv(index=False).encode('utf-8')

def app():
    st.title("Atmospheric Quality")

    st.markdown(
    """
    Upload or Export a geojson for an area of interest (keep the size of the area reasonable) and see the nightlight
    activity for that particular area in the selected timeframe
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
            #starting_date = st.date_input(label="Starting Date", value=None, min_value=None, max_value=None, key=None, help=None, on_change=None)
            #ending_date = st.date_input(label="Ending Date", value=None, min_value=None, max_value=None, key=None, help=None, on_change=None, args=None, kwargs=None)
            data = st.file_uploader(
                "Upload a vector dataset", type=["geojson", "kml", "zip", "tab"]
            )
            function = st.selectbox(label='Analysis',options=['Map Visualization','Raw data & Plot'])
            frequency = st.selectbox(label='Frequency',options=['Daily','Weekly','Monthly'])
            metrics = st.multiselect('Choose Atmospheric Indices',['L3_SO2','L3_CO','L3_NO2','L3_HCHO','L3_AER_AI','L3_O3'])

            
            #newButton = st.form_submit_button(label="Testbutton")
            submitted = st.form_submit_button("Submit")
            if submitted:
                if data: #Check if .geojson file was given
                    file_path = general_utils.save_uploaded_file(data, data.name)
                    layer_name = os.path.splitext(data.name)[0]
                    # Save the uploaded file
                    with open(file_path,'r') as f:
                        geom = json.load(f)
                        eegeom = general_utils.getGeometry(geom)
                    #location = eegeom.centroid().coordinates().getInfo()[::-1]
                
                    # Visualization
                    if function == 'Map Visualization':
                        #Visualize only first metric
                        m = atmosphericQuality_utils.mapVisualization(eegeom,start_year,start_month,end_year,end_month,frequency,metrics[0])
                    
                        with row1_col1:
                            m.add_child(folium.LayerControl())
                            m.to_streamlit(height=700)
                    else:
                        dataframe = atmosphericQuality_utils.getDataFrame(eegeom,start_year,start_month,end_year,end_month,frequency,metrics)
                        #dataframe = pd.read_csv('temporary.csv')
                        dataframe.to_csv('temporary.csv')
                        plot = atmosphericQuality_utils.createPlot(dataframe,frequency)
                        first_column = dataframe.pop('date')
                        #print(first_column)
                        dataframe.insert(0,'date',first_column)
                        dataframe = dataframe.reset_index(drop=True)
                        #dataFrame = dataFrame.set_index('date')
                        csv = convert_df(dataframe)
                        #download_button_str = download_button.download_button(csv,"file.csv","Press To Download")
                        #st.markdown(download_button_str, unsafe_allow_html=True)
                        
                        with row1_col1:
                            st.plotly_chart(plot)
                            st.dataframe(dataframe)
                            download_button_str = download_button.download_button(csv,"file.csv","Press To Download")
                            st.markdown(download_button_str, unsafe_allow_html=True)

            else:
                with row1_col1:
                    m = leafmap.foliumap.Map(zoom_start=2,draw_export=True)
                    m.to_streamlit(height=700)
    
