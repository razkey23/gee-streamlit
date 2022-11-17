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


def getGeometry(data):
  oldcoords = data['features'][0]['geometry']['coordinates']
  coords = [[[coord[0],coord[1]] for coord in oldcoords[0]]]
  shapeType = data['features'][0]['geometry']['type']
  if shapeType == 'Polygon':
    try:
      eegeometry = ee.Geometry.Polygon(coords)
    except:
      return None
  elif shapeType =='MultiPolygon':
    try:
      eegeometry = ee.Geometry.MultiPolygon(coords)
    except:
      return None
  return eegeometry


def save_uploaded_file(file_content, file_name):
    """
    Save the uploaded file to a temporary directory
    """
    import tempfile
    import os
    import uuid

    _, file_extension = os.path.splitext(file_name)
    file_id = str(uuid.uuid4())
    file_path = os.path.join(tempfile.gettempdir(), f"{file_id}{file_extension}")

    with open(file_path, "wb") as file:
        file.write(file_content.getbuffer())

    return file_path

def inBetween(startDate,endDate):
  res =[]
  start_date = date(int(startDate[0:4]),int(startDate[4:6]),int(startDate[6:8]))
  end_date = date(int(endDate[0:4]),int(endDate[4:6]),int(endDate[6:8]))
  #start_date = date(2019, 6, 1) 
  #end_date = date(2021, 6, 2)    # perhaps date.now()
  delta = end_date - start_date   # returns timedelta
  for i in range(delta.days+1):
    res.append((start_date+ timedelta(days=i)).strftime("%Y-%m-%d"))
  return res

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




def app():
    st.title("Nightlights")
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
            submitted = st.form_submit_button("Submit")

        if submitted:
            print(start_year,end_year)
            print(start_month,end_month)

            # Create date_range
            startDate = str(start_year)+'-'+str(start_month)+"-01"
            endDate = str(end_year)+"-"+str(end_month)+"-01"
            months = pd.period_range(startDate, endDate, freq='M')
            dates = list(months.strftime("%m-%Y"))
            
            if data:
                file_path = save_uploaded_file(data, data.name)
                layer_name = os.path.splitext(data.name)[0]
                


                print(file_path)
                # Do the nightlights logic
                with open(file_path,'r') as f:
                    geom = json.load(f)
                    eegeom = getGeometry(geom)
                print(geom)
                location = eegeom.centroid().coordinates().getInfo()[::-1]
                m = leafmap.foliumap.Map(location=location, zoom_start=12)
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
            container = st.container()
        else:
            with row1_col1:
                m = leafmap.foliumap.Map(zoom_start=2,draw_export=True)
                m.to_streamlit(height=700)



    '''
    with row1_col2:
        #Init map
        location = rethymno_geom.centroid().coordinates().getInfo()[::-1]
        m = leafmap.foliumap.Map(location=location, zoom_start=12)
        visualization = {
            'min': 	0.5, # -15degress Celsius
            'max': 	60.0, # 47degrees Celsius
            'palette':['black','white']
        }
        vmin = visualization['min']
        vmax = visualization['max']
        
        for month in range(1,13):
            dataset =  ee.ImageCollection("NOAA/VIIRS/DNB/MONTHLY_V1/VCMCFG").\
                        filterBounds(rethymno_geom).\
                        filter(ee.Filter.calendarRange(2019, 2019, 'year')).\
                        filter(ee.Filter.calendarRange(month, month, 'month'))

            
            image = dataset.reduce(ee.Reducer.median()).select('avg_rad_median').clip(rethymno_geom)
            m.add_ee_layer(image,visualization, str(month)+"-2019")
            #medianImageCollection.append(image) 

        m.add_child(folium.LayerControl())
        #ImageCollectionVis = ee.ImageCollection(medianImageCollection)
        monthDict= {	'01':'January',		'02':'February',		'03':'March',		'04':'April',		'05':'May',		'06':'June',		'07':'July',		'08':'August',		'09':'September',		'10':'October',		'11':'November',		'12':'December'		}
        

        m.to_streamlit(height=700)
    
    with row1_col1:
        m = leafmap.deck.Map()
        st.pydeck_chart(m)
    '''