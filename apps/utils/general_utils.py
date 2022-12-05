import os
import json
import calendar
import folium
import pandas as pd
import ee 
from datetime import date, timedelta
import datetime
import plotly.tools as tls
import plotly.express as px

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
def add_ee_layer(self, ee_image_object, vis_params, name):
  map_id_dict = ee.Image(ee_image_object).getMapId(vis_params)
  folium.raster_layers.TileLayer(
    tiles = map_id_dict['tile_fetcher'].url_format,
    attr = 'Map Data &copy; <a href="https://earthengine.google.com/">Google Earth Engine</a>',
    name = name,
    overlay = True,
    control = True
  ).add_to(self)