import pandas as pd
import geopandas as gpd
import matplotlib.pyplot as plt
from scipy.optimize import curve_fit
import numpy as np
import datetime
import os

# filename for shapefile and WHO input dataset
DIR_PATH = os.path.dirname(os.path.realpath(__file__))
WHO_COVID_FILENAME='WHO_data/Data_ WHO Coronavirus Covid-19 Cases and Deaths - WHO-COVID-19-global-data.csv'
FILENAME_SHP = 'ne_10m_admin_0_countries/ne_10m_admin_0_countries.shp'
HRP_iso3 = ['AFG','BFA','BDI','CMR','CAF','TCD','COD','ETH','HTI','IRQ','LBY','MLI','MMR','NER','NGA','PSE','SOM','SSD','SDN','SYR','UKR','VEN','YEM']
# number of days to be selected for the analysis
TIME_RANGE=15

def main():
    # get WHO data and calculate sum as 'HRP'
    df_WHO=get_WHO_data()
    # create canvas
    # TODO adjust rows and columns depending on the number of countries
    fig,axs=plt.subplots(figsize=[15,10],nrows=4,ncols=6)
    # create output df
    # TODO do we need a dictionary for the columns names?
    output_df=pd.DataFrame(columns=['iso3','pc_growth_rate','doubling_time'])
    for ifig,iso3 in enumerate(HRP_iso3):
        axis=axs[ifig // 6][ifig % 6]
        df_country=get_country_df(df_WHO,iso3)
        # start fit
        x = df_country['day_fit']
        initial_caseload=df_country['CumCase'].iloc[0]
        initial_parameters=[initial_caseload,0.3]
        popt, pcov = curve_fit(func,x,df_country['CumCase'],p0=initial_parameters)
        # TODO check quality of the fit
        # calculate growth rate and doubling time
        growth_rate=np.exp(popt[1])-1
        doubling_time_fit=np.log(2)/growth_rate
        axis.plot(x, df_country['CumCase'], 'ko', label=f"{iso3} - Original Data")
        axis.plot(x, func(x, *popt), 'r-', label=f"{iso3} - Fitted Curve")
        # altertnative way of calculating doubling time form observations
        # This is using the first and the last observations and not the exponentinal fit
        initial_val=df_country['CumCase'].iloc[0]
        final_val=df_country['CumCase'].iloc[-1]
        ndays=df_country['day_fit'].iloc[-1]
        doubling_time_val=ndays*np.log(2)/np.log(final_val/initial_val)
        # TODO quality check: the two emasurements sohuld agree within 20%
        # print values
        print(f'{iso3} Doubling time (fit): ',doubling_time_fit)
        print(f'{iso3} Doubling time (values): ',doubling_time_val)
        output_df=output_df.append({'iso3':iso3,'pc_growth_rate':growth_rate*100,'doubling_time':doubling_time_fit},ignore_index=True)
        axis.legend()
   
    world_boundaries=gpd.read_file('{}/{}'.format(DIR_PATH,FILENAME_SHP))
    output_df_geo=world_boundaries.merge(output_df,left_on='ADM0_A3',right_on='iso3',how='left')
    # plotting map
    print(output_df_geo)
    fig_map, ax_map = plt.subplots(1, 1)
    output_df_geo.plot(column='pc_growth_rate',cmap='OrRd',ax=ax_map, legend=True)
    output_df_geo.boundary.plot(ax=ax_map,lw=0.5)

    # print(df_WHO)
    plt.show()

def get_country_df(input_df,iso3):
    df=input_df[input_df['ISO_3_CODE']==iso3].copy()
    df.loc[:,'day_fit']=df['date_epicrv']-datetime.date.today()+datetime.timedelta(days=TIME_RANGE)
    df.loc[:,'day_fit']=df['day_fit'].dt.days
    df=df[df['day_fit']>0]
    return df


def func(x, p0, growth):
    return p0 * np.exp(x*growth)

def get_WHO_data():
    df=pd.read_csv(f'{DIR_PATH}/{WHO_COVID_FILENAME}')
    # get only HRP countries
    df = df.loc[df['ISO_3_CODE'].isin(HRP_iso3),:]
    df['date_epicrv']=pd.to_datetime(df['date_epicrv']).dt.date
    df=df[['date_epicrv','ISO_3_CODE','CumCase']]

    # adding global by date
    df_all=df.groupby('date_epicrv').sum()
    df_all['ISO_3_CODE']='HRP'
    df_all=df_all.reset_index()
    HRP_iso3.insert(0,'HRP')
    df=df.append(df_all)
    return df

if __name__ == '__main__':
    main()