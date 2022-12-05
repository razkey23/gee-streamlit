import os
import json
import calendar
import pandas as pd
import ee 
from datetime import date, timedelta
import datetime
import plotly.tools as tls
import plotly.express as px

def getData(eegeom,start_year,start_month,end_year,end_month):
    startDate = str(start_year)+'-'+str(start_month)+"-01"
    endDate = str(end_year)+"-"+str(end_month)+"-01"
    months = pd.period_range(startDate, endDate, freq='M')
    dates = list(months.strftime("%m-%Y"))
    df=[]
    for date in dates:
        month = int(date.split("-")[0])
        year = int(date.split("-")[1])
        #for month in range(1,13):
        sl=0
        dataset =  ee.ImageCollection("NOAA/VIIRS/DNB/MONTHLY_V1/VCMCFG").\
                    filterBounds(eegeom).\
                    filter(ee.Filter.calendarRange(year, year, 'year')).\
                    filter(ee.Filter.calendarRange(month, month, 'month'))

        
        image = dataset.reduce(ee.Reducer.median()).select('avg_rad_median').clip(eegeom)

        
        meanDictionary = image.reduceRegion(
                        reducer= ee.Reducer.median().combine(reducer2=ee.Reducer.minMax(),sharedInputs=True).combine(reducer2=ee.Reducer.variance(),sharedInputs=True)  ,
                        geometry= eegeom,
                        bestEffort=True,
                        scale=2)

        dictionary = meanDictionary.getInfo()
    
        
        if dictionary['avg_rad_median_median']==0:
            sl=1
            dataset =  ee.ImageCollection("NOAA/VIIRS/DNB/MONTHLY_V1/VCMSLCFG").\
                        filterBounds(eegeom).\
                        filter(ee.Filter.calendarRange(year, year, 'year')).\
                        filter(ee.Filter.calendarRange(month, month, 'month'))

            print(dataset.reduce(ee.Reducer.median()).bandNames().getInfo())
            image = dataset.reduce(ee.Reducer.median()).select('avg_rad_median').clip(eegeom)
         
            meanDictionary = image.reduceRegion(
                            reducer= ee.Reducer.median().combine(reducer2=ee.Reducer.minMax(),sharedInputs=True).combine(reducer2=ee.Reducer.variance(),sharedInputs=True)  ,
                            geometry= eegeom,
                            bestEffort=True,
                            scale=2)

            print("Date is: ",month,"-",year," SL-Corrected")
        else: 
            print("Date is: ",month,"-",year)
        dictionary = meanDictionary.getInfo()

        # Change the keys that look like this : 'LST_Day_1km_median_max' to -> max in order to append to the dataframe
        newDic={}
        for key in dictionary.keys():
            newDic["avg_rad_"+key.split("_")[-1]] = dictionary[key]
        
        # Create the date value to append to the dataframe list
        newDic['date'] = str(month).zfill(2)+"-"+str(year)
        if sl==1:
            newDic['source'] = 'sl'
        else:
            newDic['source'] = 'og'
        df.append(newDic)
    return pd.DataFrame(df)

def createPlot(df):
    import matplotlib.pyplot as plt
    def minMaxScaling(column):
        return (column-column.min())/(column.max()-column.min())
    df['avg_rad_median_scaled'] = minMaxScaling(df['avg_rad_median'])
    newDf = df.groupby(pd.PeriodIndex(df['date'], freq="M"))['avg_rad_median_scaled'].mean()
    newFig = px.line(newDf, 
        x=newDf.index.strftime('%Y-%m'), 
        y=newDf, title="Average Night Radiance",
        markers=True  ,
        labels={
                     "x": "",
                     "y": "Normalized Value"
                 },
        template='ggplot2')
    
    newFig.update_traces(marker_size=15)

    return newFig