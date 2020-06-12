import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
import datetime
import os
import yaml

# filename for shapefile and WHO input dataset
DIR_PATH = os.path.dirname(os.path.realpath(__file__))
WHO_COVID_FILENAME='WHO_data/Data_ WHO Coronavirus Covid-19 Cases and Deaths - WHO-COVID-19-global-data.csv'
POPULATION_FILENAME='Population_data/API_SP.POP.TOTL_DS2_en_excel_v2_1121005.xls'

def main():
    # Read in list of countries
    with open('countries/admins.yaml', 'r') as stream:
        country_list = yaml.safe_load(stream)['admin_info']
    HRP_iso3 = sorted(list(set([country.get('alpha_3', None) for country in country_list])))
    # get WHO data and calculate sum as 'HRP'
    df_WHO=get_WHO_data(HRP_iso3)
    
    # get weekly new cases
    new_cases_w=df_WHO.groupby(['ISO_3_CODE']).resample('W-Mon', on='date_epicrv').sum()['NewCase']
    cumulative_w=df_WHO.groupby(['ISO_3_CODE']).resample('W-Mon', on='date_epicrv').min()['CumCase']

    output_df=pd.merge(left=new_cases_w,right=cumulative_w,left_index=True,right_index=True,how='inner')
    output_df['NewCase_Rel']=output_df['NewCase']/output_df['CumCase']

    df_pop=pd.read_excel(POPULATION_FILENAME,sheet_name='Data',header=1,skiprows=[0,1],usecols='B,BK')
    
    print(df_pop)

def get_WHO_data(HRP_iso3):
    df=pd.read_csv(f'{DIR_PATH}/{WHO_COVID_FILENAME}')
    # get only HRP countries
    df = df.loc[df['ISO_3_CODE'].isin(HRP_iso3),:]
    df['date_epicrv']=pd.to_datetime(df['date_epicrv'])
    df=df[['date_epicrv','ISO_3_CODE','CumCase','NewCase']]

    # adding global by date
    df_all=df.groupby('date_epicrv').sum()
    df_all['ISO_3_CODE']='HRP'
    df_all=df_all.reset_index()
    HRP_iso3.insert(0,'HRP')
    df=df.append(df_all)
    return df

if __name__ == '__main__':
    main()