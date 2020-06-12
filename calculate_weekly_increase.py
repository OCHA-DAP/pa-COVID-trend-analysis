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

    output_df=pd.merge(left=new_cases_w,right=cumulative_w,left_index=True,right_index=True,how='inner').reset_index()
    output_df['NewCase_Rel']=output_df['NewCase']/output_df['CumCase']

    # Read in pop
    df_pop=pd.read_excel(POPULATION_FILENAME,sheet_name='Data',header=1,skiprows=[0,1],usecols='B,BK').rename(
        columns={'2018': 'population'})
    # Add HRP
    df_pop = df_pop.append({'Country Code': 'HRP',
                            'population':  df_pop.loc[df_pop['Country Code'].isin(HRP_iso3), 'population'].sum()},
                           ignore_index=True)

    # Add pop to output df
    output_df = output_df.merge(df_pop, left_on='ISO_3_CODE', right_on='Country Code', how='left').drop(
        columns=['Country Code'])
    # Get cases per hundred thousand
    output_df['weekly_new_cases_per_ht'] = output_df['NewCase'] / output_df['population'] * 1E5
    output_df['weekly_pc_increase'] = output_df['NewCase_Rel'] * 100

    # Show plots
    pd.plotting.register_matplotlib_converters()
    for q in ['weekly_new_cases_per_ht', 'weekly_pc_increase']:
        fig,axs=plt.subplots(figsize=[15,10],nrows=8,ncols=8)
        fig.suptitle(q)
        ifig = 0
        for iso3, group in output_df.groupby('ISO_3_CODE'):
            axis = axs[ifig // 8][ifig % 8]
            axis.plot(group['date_epicrv'], group[q])
            axis.set_title(iso3)
            axis.set_xticks([])
            #axis.set_ylim(0, output_df[q].max())
            ifig += 1
    plt.show()

    # Save as JSON
    output_df['date_epicrv'] = output_df['date_epicrv'].apply(lambda x: x.strftime('%Y-%m-%d'))
    output_df.groupby('ISO_3_CODE').apply(lambda x: x.to_dict('r')).to_json(
        'hrp_covid_cases.json', orient='index', indent=2)


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
