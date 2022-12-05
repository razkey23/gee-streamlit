import streamlit as st
from datetime import date, timedelta
import datetime
import ee
import geemap
import leafmap
import folium
import os
import json
import calendar
import pandas as pd
from apps.utils import general_utils, nightlights_utils,download_button
import plotly.tools as tls

def add_ee_layer(self, ee_image_object, vis_params, name):
  map_id_dict = ee.Image(ee_image_object).getMapId(vis_params)
  folium.raster_layers.TileLayer(
    tiles = map_id_dict['tile_fetcher'].url_format,
    attr = 'Map Data &copy; <a href="https://earthengine.google.com/">Google Earth Engine</a>',
    name = name,
    overlay = True,
    control = True
  ).add_to(self)
# Add EE drawing method to folium.
leafmap.foliumap.Map.add_ee_layer = add_ee_layer



@st.experimental_memo
def convert_df(df):
   return df.to_csv(index=False).encode('utf-8')
    




def app():
    st.title("Nightlight Activity")
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

    
    visualization = {
            'min': 	0.5, # -15degress Celsius
            'max': 	60.0, # 47degrees Celsius
            'palette':['black','white']
    }
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
            functionality = st.selectbox(label='Analysis',options=['Map Visualization','Raw data & Plot'])
            #newButton = st.form_submit_button(label="Testbutton")
            submitted = st.form_submit_button("Submit")

        if submitted:
            print(start_year,end_year)
            print(start_month,end_month)

            # Create date_range
            
            if data:
                file_path = general_utils.save_uploaded_file(data, data.name)
                layer_name = os.path.splitext(data.name)[0]
            
                print(file_path)
                # Do the nightlights logic
                with open(file_path,'r') as f:
                    geom = json.load(f)
                    eegeom = general_utils.getGeometry(geom)
                print(geom)
                location = eegeom.centroid().coordinates().getInfo()[::-1]
                

                m = leafmap.foliumap.Map(location=location, zoom_start=12)
                

                # Disable Temporarily
                
                startDate = str(start_year)+'-'+str(start_month)+"-01"
                endDate = str(end_year)+"-"+str(end_month)+"-01"
                months = pd.period_range(startDate, endDate, freq='M')
                dates = list(months.strftime("%m-%Y"))
                if functionality=='Map Visualization':
                    for date in dates:
                        # split date
                        month = int(date.split("-")[0])
                        year = int(date.split("-")[1])
                        dataset =  ee.ImageCollection("NOAA/VIIRS/DNB/MONTHLY_V1/VCMCFG").\
                                    filterBounds(eegeom).\
                                    filter(ee.Filter.calendarRange(year,year, 'year')).\
                                    filter(ee.Filter.calendarRange(month, month, 'month'))
                
                        image = dataset.reduce(ee.Reducer.median()).select('avg_rad_median').clip(eegeom)
                        m.add_ee_layer(image,visualization, str(month)+"-"+str(year))
                    with row1_col1:
                        m.add_child(folium.LayerControl())
                        m.to_streamlit(height=700)
                else:
                    
                    dataFrame = nightlights_utils.getData(eegeom,start_year,start_month,end_year,end_month)
                    #dataFrame = pd.read_csv('out.csv')
                    plot = nightlights_utils.createPlot(dataFrame)
                    
                    
                    first_column = dataFrame.pop('date')
                    #print(first_column)
                    dataFrame.insert(0,'date',first_column)
                    dataFrame = dataFrame.reset_index(drop=True)
                    #dataFrame = dataFrame.set_index('date')
                    csv = convert_df(dataFrame)

                    with row1_col1:
                        
                        st.plotly_chart(plot)
                        st.dataframe(dataFrame, use_container_width=True)
                        download_button_str = download_button.download_button(csv,"file.csv","Press To Download")
                        st.markdown(download_button_str, unsafe_allow_html=True)
                        #download_button.download_button(csv,"file.csv","Press To Download - No Streamlit")
                    
                
            
            
        else:
            with row1_col1:
                m = leafmap.foliumap.Map(zoom_start=2,draw_export=True)
                m.to_streamlit(height=700)
