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

# Cloud Masking for Sentinel-2 Images
def maskS2clouds(image):
  qa = image.select('QA60');

  # Bits 10 and 11 are clouds and cirrus, respectively.
  cloudBitMask = 1 << 10;
  cirrusBitMask = 1 << 11;

  #Both flags should be set to zero, indicating clear conditions.
  mask = qa.bitwiseAnd(cloudBitMask).eq(0)
  mask = mask.bitwiseAnd(cirrusBitMask).eq(0)

  return image.updateMask(mask).divide(10000)


def getSentinelDates(eegeom,startDate,endDate):
    # Returns Sentinel-2 Capture Dates as a list
    sentinel = ee.ImageCollection("COPERNICUS/S2").\
                            filterBounds(eegeom).\
                            filterDate(startDate,endDate).\
                            filterMetadata('CLOUDY_PIXEL_PERCENTAGE','less_than',20)
    # Auxiliary mapping function
    def getDate(image):
        return ee.Feature(None, {'date': image.date().format('YYYY-MM-dd')})
    dates = sentinel.map(getDate).distinct('date').aggregate_array('date')
    return dates.getInfo()




def getDataFrame(eegeom,start_year,start_month,end_year,end_month,metricsarg=['Chlorophyl-A']):
    location = eegeom.centroid().coordinates().getInfo()[::-1]

    startDate = str(start_year)+'-'+str(start_month)+"-01"
    endDate = str(end_year)+"-"+str(end_month)+"-01"
    datetime_object = datetime.datetime.strptime(endDate,"%Y-%m-%d")
    nextEndDate = (datetime_object+ datetime.timedelta(days=1)).strftime("%Y-%m-%d")
    
    dates = getSentinelDates(eegeom,startDate,endDate)
    dates.append(nextEndDate)
    df=[]

    for i in range(len(dates)-1):
        sentinel = ee.ImageCollection("COPERNICUS/S2").\
                            filterBounds(eegeom).\
                            filterDate(dates[i],dates[i+1]).\
                            filterMetadata('CLOUDY_PIXEL_PERCENTAGE','less_than',20).\
                            map(maskS2clouds).\
                            mean()
        if not sentinel.bandNames().getInfo():
            continue
        
        # Mask Non-Water areas
        ndwi = sentinel.normalizedDifference(['B3', 'B8']).rename('NDWI')
        ndwiThreshold = ndwi.gte(0.0);
        sentinel = sentinel.updateMask(ndwiThreshold);

        # Calculate Chlorophyl-A value
        # Create new band with Chl-a based on formula-> Chl_a = 4.26 * Math.pow(B03/B01, 3.94);
        newDic={}
        if 'Chlorophyl-A' in metricsarg:
            ndci = sentinel.normalizedDifference(['B5','B4']).rename('ndci')
            
            pow3 = ndci.pow(3)
            pow2 = ndci.pow(2)
            first = pow3.multiply(826.57)
            second = pow2.multiply(176.43)
            third = ndci.multiply(19)
            fin1 = first.subtract(second)
            fin2 = fin1.add(third)
            newDiv = fin2.add(ee.Image.constant(4.071))
            #chl = 826.57 * NDCIv ^3 - 176.43 * NDCIv^2 + 19 * NDCIv + 4.071; #// NDCIv = (B5-B4)/(B5+B4)
            print(newDiv.bandNames().getInfo())
            latlon = newDiv.reduceRegion( 
            reducer = ee.Reducer.percentile(ee.List([20,40,50,60,80,100])),
                    geometry=eegeom,
                    bestEffort = True,
                    scale=1
            )
            
            dic=latlon.getInfo()
            if None in dic.values():
                continue
            #print(dic['ndci'].shape)
            #newDic={}
            for key in dic.keys():
                newDic["Chl_"+key.split("_")[-1]] = dic[key]
            
            # Create the date value to append to the dataframe list
            newDic['date'] = dates[i]
            print(dates[i])
            #dfs.append(newDic)

        if 'Turbidity' in metricsarg:
            ndwi = sentinel.normalizedDifference(['B4', 'B3']).rename('NDTI')
            print(ndwi.bandNames().getInfo())
            latlon=ndwi
            latlon = latlon.reduceRegion( 
                reducer = ee.Reducer.percentile(ee.List([20,40,50,60,80,100])),
                geometry=eegeom,
                bestEffort = True,
                scale=1
                )
            
            dic=latlon.getInfo()
            if None in dic.values():
                continue
            for key in dic.keys():
                newDic["Turbidity_"+key.split("_")[-1]] = dic[key]
            newDic['date'] = dates[i]
            # Create the date value to append to the dataframe list
            
            print(dates[i])
            
        #'Chlorophyl-A','Turbidity','Suspended Matter','Color Dissolved Organic Matter'
        df.append(newDic)
    return pd.DataFrame(df)
    if len(dfs)==1:
        return pd.dataframe(dfs[0])
    df_new = dfs[0] 
    #df_new = pd.merge(df_new, dataframe, on='date', how='outer')
    for df in dfs[1:]:
        df_new = pd.merge(df_new, df, on='date', how='outer')
    return df_new


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
        if 'p50' not in col: continue
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