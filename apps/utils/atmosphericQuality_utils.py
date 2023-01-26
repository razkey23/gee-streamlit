import os
import json
import calendar
import pandas as pd
import ee 
from datetime import date, timedelta
import datetime
import plotly.tools as tls
import plotly.express as px
import plotly.graph_objects as go
import leafmap

# Config for visualization
#metrics= [    {      "L3_SO2": {        "min": 0.0,        "max": 0.0005,        "band": "SO2_column_number_density"      }    },    {      "L3_CO": {        "min": 0.0,        "max": 0.05,        "band": "CO_column_number_density"      }    },    {      "L3_NO2": {        "min": 0.0,        "max": 0.0002,        "band": "NO2_column_number_density"      }    },    {      "L3_HCHO": {        "min": 0.0,        "max": 0.0003,        "band": "tropospheric_HCHO_column_number_density"      }    },    {      "L3_AER_AI": {        "min": -1,        "max": 2.0,        "band": "absorbing_aerosol_index"      }    },    {      "L3_AER_AI": {        "min": 0.12,        "max": 0.15,        "band": "O3_column_number_density"      }    }  ]
metrics=         { "L3_SO2" : {        "min": 0.0,        "max": 0.0005,        "band": "SO2_column_number_density"          },          "L3_CO": {        "min": 0.0,        "max": 0.05,        "band": "CO_column_number_density"          },          "L3_NO2": {        "min": 0.0,        "max": 0.0002,        "band": "NO2_column_number_density"          },          "L3_HCHO": {        "min": 0.0,        "max": 0.0003,        "band": "tropospheric_HCHO_column_number_density"          },          "L3_AER_AI": {        "min": -1,        "max": 2.0,        "band": "absorbing_aerosol_index"          },          "L3_O3": {        "min": 0.12,        "max": 0.15,        "band": "O3_column_number_density"    }  }




def mapVisualization(eegeom,start_year,start_month,end_year,end_month,frequency='Weekly',metric='L3_NO2'):
    '''
        Returns a folium map 
    '''
    location = eegeom.centroid().coordinates().getInfo()[::-1]
    m = leafmap.foliumap.Map(location=location, zoom_start=12)
    if frequency=='Weekly': freq = 'w'
    elif frequency=='Daily': freq = 'd'
    elif frequency=='Monthly': freq = 'm'
    startDate = str(start_year)+'-'+str(start_month)+"-01"
    endDate = str(end_year)+"-"+str(end_month)+"-01"
    months = pd.period_range(startDate, endDate, freq=freq)
    dates = list(months.strftime("%Y-%m-%d"))
    print(len(dates))
    
    for i in range(len(dates)-1):
        month = int(dates[i].split("-")[1])
        year = int(dates[i].split("-")[0])
        day = int(dates[i].split("-")[2])
        config = metrics[metric]
        medianImage = ee.Image(ee.ImageCollection("COPERNICUS/S5P/OFFL/"+metric).\
                        filterBounds(eegeom).\
                        filterDate(dates[i],dates[i+1]).\
                        reduce(ee.Reducer.median()).\
                        select(config['band']+'_median').\
                        clip(eegeom))
        
        visualization = {
            'min': 	config['min'],
            'max': 	config['max'],
            'palette': ['black', 'blue','purple','cyan','green','yellow','red']
        }
        
        m.add_ee_layer(medianImage,visualization, str(day)+"-"+str(month)+"-"+str(year))
    return m


def getDataFrame(eegeom,start_year,start_month,end_year,end_month,frequency='Weekly',metricsarg=['L3_NO2']):
    location = eegeom.centroid().coordinates().getInfo()[::-1]
    m = leafmap.foliumap.Map(location=location, zoom_start=12)
    if frequency=='Weekly': freq = 'w'
    elif frequency=='Daily': freq = 'd'
    elif frequency=='Monthly': freq = 'm'
    startDate = str(start_year)+'-'+str(start_month)+"-01"
    endDate = str(end_year)+"-"+str(end_month)+"-01"
    months = pd.period_range(startDate, endDate, freq=freq)
    dates = list(months.strftime("%Y-%m-%d"))
    
    if len(metricsarg)*len(dates)>=12:
        dates = dates[0:12]
    #if len(dates)>=30:dates=dates[0:29]
    print(dates)
    for index,metric in enumerate(metricsarg):
        #print(metric)
        df=[]
        config = metrics[metric]
        for i in range(len(dates)-1):
            print(dates[i],metric)
            month = int(dates[i].split("-")[1])
            year = int(dates[i].split("-")[0])
            day = int(dates[i].split("-")[2])
            dic = ee.Image(ee.ImageCollection("COPERNICUS/S5P/OFFL/"+metric).\
                                filterBounds(eegeom).\
                                filterDate(dates[i],dates[i+1]).\
                                reduce(ee.Reducer.median()).\
                                select(config['band']+'_median').\
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
                newDic[metric+"_"+key.split("_")[-1]] = dictionary[key]
            
            # Create the date value to append to the dataframe list
            newDic['date'] = str(year)+"-"+str(month).zfill(2)+"-"+str(day).zfill(2)
            
            df.append(newDic)
        dataframe = pd.DataFrame(df)
        if index==0: df_new = dataframe
        else: df_new = pd.merge(df_new, dataframe, on='date', how='outer')
    return pd.DataFrame(df_new)


def createPlot(df,frequency):
    if frequency=='Weekly': freq = 'w'
    elif frequency=='Daily': freq = 'd'
    elif frequency=='Monthly': freq = 'm'
    import matplotlib.pyplot as plt
    def minMaxScaling(column):
        return (column-column.min())/(column.max()-column.min())
    #df = pd.read_csv('temporary.csv')
    cols = df.columns
    fig = go.Figure()
    for col in cols:
        if 'median' not in col: continue
        df[col+"_scaled"] = minMaxScaling(df[col])
        newDf = df.groupby(pd.PeriodIndex(df['date'],freq='d'))[col+"_scaled"].mean()
        fig.add_trace(go.Scatter(
            x=newDf.index.strftime('%Y-%m-%d'),
            y=newDf,
            name=col,
            marker=dict(
                size=12,
            )
        ))
        
    return fig
    
    



