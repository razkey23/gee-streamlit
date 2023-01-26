import os
import json
import calendar
import pandas as pd
import ee 
from datetime import date, timedelta
import datetime
import plotly.tools as tls
import plotly.express as px
import leafmap
import plotly.graph_objects as go


def getModisDates(eegeom,startDate,endDate):
    # Returns MODIS-2 Capture Dates as a list
    modis =  ee.ImageCollection('MODIS/061/MOD11A1').\
              filterBounds(eegeom).\
              filterDate(startDate,endDate)

  # We reduce the image collection to a single image using "median" 
  # and we select the band we are interested in "LST_Day_1km_median"
    # Auxiliary mapping function
    def getDate(image):
        return ee.Feature(None, {'date': image.date().format('YYYY-MM-dd')})
    dates = modis.map(getDate).distinct('date').aggregate_array('date')
    
    return dates.getInfo()


def convertToCelsius(column):
  return round(column*0.02-273,5)

def mapVisualization(eegeom,start_year,start_month,end_year,end_month,frequency='Weekly'):
    '''
        Returns a folium map 
    '''

    visualization = {
        'min': 	14000.0, # -15degress Celsius
        'max': 	15650.0, # 47degrees Celsius
        'palette': [
            '040274', '040281', '0502a3', '0502b8', '0502ce', '0502e6',
            '0602ff', '235cb1', '307ef3', '269db1', '30c8e2', '32d3ef',
            '3be285', '3ff38f', '86e26f', '3ae237', 'b5e22e', 'd6e21f',
            'fff705', 'ffd611', 'ffb613', 'ff8b13', 'ff6e08', 'ff500d',
            'ff0000', 'de0101', 'c21301', 'a71001', '911003'
        ],
    }
    startDate = str(start_year)+'-'+str(start_month)+"-01"
    endDate = str(end_year)+"-"+str(end_month)+"-01"
    if frequency=='Weekly': freq = 'w'
    elif frequency=='Daily': freq = 'd'
    elif frequency=='Monthly': freq = 'm'
    months = pd.period_range(startDate, endDate, freq=freq)
    dates = list(months.strftime("%Y-%m-%d"))
    location = eegeom.centroid().coordinates().getInfo()[::-1]
    m = leafmap.foliumap.Map(location=location, zoom_start=12)
    print(dates)
    for i in range(len(dates)-1):
        month = int(dates[i].split("-")[1])
        year = int(dates[i].split("-")[0])
        day = int(dates[i].split("-")[2])
        monthEnd = int(dates[i+1].split("-")[1])
        yearEnd = int(dates[i+1].split("-")[0])
        dayEnd = int(dates[i+1].split("-")[2])
        
        medianImage = ee.Image(ee.ImageCollection('MODIS/061/MOD11A1').\
                        filterBounds(eegeom).\
                        filterDate(dates[i],dates[i+1]).\
                        reduce(ee.Reducer.median()).\
                        select('LST_Day_1km_median').\
                        clip(eegeom))
        
        m.add_ee_layer(medianImage,visualization, str("From ")+str(day)+"-"+str(month)+"-"+str(year)+str(" To ")+str(dayEnd)+"-"+str(monthEnd)+"-"+str(yearEnd))
    return m


def getDataFrame(eegeom,start_year,start_month,end_year,end_month,frequency='Weekly'):
    location = eegeom.centroid().coordinates().getInfo()[::-1]
    m = leafmap.foliumap.Map(location=location, zoom_start=12)
    if frequency=='Weekly': freq = 'w'
    elif frequency=='Daily': freq = 'd'
    elif frequency=='Monthly': freq = 'm'
    startDate = str(start_year)+'-'+str(start_month)+"-01"
    endDate = str(end_year)+"-"+str(end_month)+"-01"
    months = pd.period_range(startDate, endDate, freq=freq)
    dates = list(months.strftime("%Y-%m-%d"))
    
    #if len(dates)>=30:dates=dates[0:29]
    print(dates)
    #print(metric)
    df=[]
    #config = metrics[metric]
    for i in range(len(dates)-1):
        #print(dates[i],metric)
        month = int(dates[i].split("-")[1])
        year = int(dates[i].split("-")[0])
        day = int(dates[i].split("-")[2])
        dic = ee.Image(ee.ImageCollection('MODIS/061/MOD11A1').\
                            filterBounds(eegeom).\
                            filterDate(dates[i],dates[i+1]).\
                            reduce(ee.Reducer.median()).\
                            select('LST_Day_1km_median').\
                            clip(eegeom)).\
                            reduceRegion(
                                reducer= ee.Reducer.median().combine(reducer2=ee.Reducer.minMax(),sharedInputs=True).combine(reducer2=ee.Reducer.variance(),sharedInputs=True)  ,
                                geometry= eegeom,
                                bestEffort=True,
                                scale=2
                            )
        dictionary = dic.getInfo()
        newDic={}

        for key in dictionary.keys():
            newDic["LST_"+key.split("_")[-1]] = dictionary[key]
        
        # Create the date value to append to the dataframe list
        newDic['date'] = str(year)+"-"+str(month).zfill(2)+"-"+str(day).zfill(2)
        
        df.append(newDic)
    return pd.DataFrame(df)



def createPlot(df,frequency):
    if frequency=='Weekly': freq = 'w'
    elif frequency=='Daily': freq = 'd'
    elif frequency=='Monthly': freq = 'm'
    import matplotlib.pyplot as plt
    def minMaxScaling(column):
        return (column-column.min())/(column.max()-column.min())
    def convertToCelsius(column):
        return round(column*0.02-273,5)
    #df = pd.read_csv('temporary.csv')
    cols = df.columns
    fig = go.Figure()
    for col in cols:
        if 'median' not in col: continue
        df[col+"_Celsius"] = convertToCelsius(df[col])
        #df[col+"_scaled"] = minMaxScaling(df[col])

        newDf = df.groupby(pd.PeriodIndex(df['date'],freq='d'))[col+"_Celsius"].mean()
        fig.add_trace(go.Scatter(
            x=newDf.index.strftime('%Y-%m-%d'),
            y=newDf,
            name=col,
            marker=dict(
                size=12,
            )
        ))
        
    return fig