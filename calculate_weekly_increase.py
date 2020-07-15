import argparse
import pandas as pd
import requests
import matplotlib.pyplot as plt
import os
import yaml
import math

# filename for shapefile and WHO input dataset
DIR_PATH = os.path.dirname(os.path.realpath(__file__))
WHO_COVID_FILENAME='WHO_data/Data_ WHO Coronavirus Covid-19 Cases and Deaths - WHO-COVID-19-global-data.csv'
WHO_COVID_URL='https://docs.google.com/spreadsheets/d/e/2PACX-1vSe-8lf6l_ShJHvd126J-jGti992SUbNLu-kmJfx1IRkvma_r4DHi0bwEW89opArs8ZkSY5G2-Bc1yT/pub?gid=0&single=true&output=csv'
POPULATION_FILENAME='Population_data/API_SP.POP.TOTL_DS2_en_excel_v2_1121005.xls'
H25_iso3=['AFG','BDI','BFA','CAF','CMR','COD','COL','ETH','HTI','IRQ','LBY','MLI','MMR','NER','NGA','PSE','SDN','SOM','SSD','SYR','TCD','UKR','VEN','YEM','ZWE']

MIN_CUMULATIVE_CASES = 100

def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument('-d', '--download-covid', action='store_true',
                        help='Download the COVID-19 data')
    return parser.parse_args()

def download_url(url, save_path, chunk_size=128):
    r = requests.get(url, stream=True)
    with open(save_path, 'wb') as fd:
        for chunk in r.iter_content(chunk_size=chunk_size):
            fd.write(chunk)
    print(f'Downloaded "{url}" to "{save_path}"')

def get_covid_data(url, save_path):
    # download covid data from HDX
    print(f'Getting upadated COVID data from WHO')
    try:
        download_url(url, save_path)
    except Exception:
        print(f'Cannot download COVID file from from HDX')

def main(download_covid=False):
    # Read in list of countries
    with open('countries/admins.yaml', 'r') as stream:
        country_list = yaml.safe_load(stream)['admin_info']
    H63_iso3 = sorted(list(set([country.get('alpha_3', None) for country in country_list])))
    
    # Download latest covid file tiles and read them in
    if download_covid:
        get_covid_data(WHO_COVID_URL,f'{DIR_PATH}/{WHO_COVID_FILENAME}')
    
    # get WHO data and calculate sum as 'H63'
    df_WHO=get_WHO_data(H63_iso3)
    
    # get weekly new cases
    new_w=df_WHO.groupby(['ISO_3_CODE']).resample('W', on='date_epicrv').sum()[['NewCase','NewDeath']]
    cumulative_w=df_WHO.groupby(['ISO_3_CODE']).resample('W', on='date_epicrv').min()[['CumCase','CumDeath']]
    ndays_w=df_WHO.groupby(['ISO_3_CODE']).resample('W', on='date_epicrv').count()['NewCase']
    ndays_w=ndays_w.rename('ndays')

    output_df=pd.merge(left=new_w,right=cumulative_w,left_index=True,right_index=True,how='inner')
    output_df=pd.merge(left=output_df,right=ndays_w,left_index=True,right_index=True,how='inner')
    output_df=output_df[output_df['ndays']==7]
    output_df=output_df.reset_index()

    output_df['NewCase_PercentChange'] = output_df.groupby('ISO_3_CODE')['NewCase'].pct_change()
    output_df['NewDeath_PercentChange'] = output_df.groupby('ISO_3_CODE')['NewDeath'].pct_change()
    # For percent change, if the diff is actually 0, change nan to 0
    output_df['diff_cases'] = output_df.groupby('ISO_3_CODE')['NewCase'].diff()
    output_df.loc[(output_df['NewCase_PercentChange'].isna()) & (output_df['diff_cases']==0), 'NewCase_PercentChange'] = 0.0
    output_df['diff_deaths'] = output_df.groupby('ISO_3_CODE')['NewDeath'].diff()
    output_df.loc[(output_df['NewDeath_PercentChange'].isna()) & (output_df['diff_deaths']==0), 'NewDeath_PercentChange'] = 0.0

    output_df=output_df[output_df['CumCase']>MIN_CUMULATIVE_CASES]

    df_pop=get_pop_data(H63_iso3)

    # Add pop to output df
    output_df = output_df.merge(df_pop, left_on='ISO_3_CODE', right_on='Country Code', how='left').drop(
        columns=['Country Code'])
    # Get cases per hundred thousand
    output_df=output_df.rename(columns={'NewCase':'weekly_new_cases','NewDeath':'weekly_new_deaths',\
                                        'CumCase':'cumulative_cases','CumDeath':'cumulative_deaths'})
    output_df['weekly_new_cases_per_ht'] = output_df['weekly_new_cases'] / output_df['population'] * 1E5
    output_df['weekly_new_deaths_per_ht'] = output_df['weekly_new_deaths'] / output_df['population'] * 1E5
    output_df['weekly_new_cases_pc_change'] = output_df['NewCase_PercentChange'] * 100
    output_df['weekly_new_deaths_pc_change'] = output_df['NewDeath_PercentChange'] * 100

    # Show plots
    pd.plotting.register_matplotlib_converters()
    nplots=math.sqrt(len(set(df_WHO['ISO_3_CODE'])))
    nplots=math.ceil(nplots)
    
    for q in ['weekly_new_cases_per_ht', 'weekly_new_cases_pc_change','weekly_new_deaths_per_ht', 'weekly_new_deaths_pc_change']:
        fig,axs=plt.subplots(figsize=[15,10],nrows=nplots,ncols=nplots)
        fig.suptitle(q)
        ifig = 0
        for iso3, group in output_df.groupby('ISO_3_CODE'):
            axis = axs[ifig // nplots][ifig % nplots]
            if q in ['weekly_new_cases_pc_change','weekly_new_deaths_pc_change']:
                idx = group[q] > 0
                axis.bar(x=group['date_epicrv'][idx], height=group[q][idx], color='r')
                idx = group[q] < 0
                axis.bar(x=group['date_epicrv'][idx], height=group[q][idx], color='b')
                axis.set_ylim(-100, 100)
                axis.axhline(y=0, c='k')
            else:
                axis.plot(group['date_epicrv'], group[q])
                #axis.set_ylim(0, output_df[q].max())
            axis.set_title(iso3)
            axis.set_xticks([])
            ifig += 1

    # Save as JSON
    output_df['date_epicrv'] = output_df['date_epicrv'].apply(lambda x: x.strftime('%Y-%m-%d'))
    output_df = output_df.drop(['NewCase_PercentChange','NewDeath_PercentChange', 'ndays', 'diff_cases','diff_deaths'], axis=1)
    output_df.groupby('ISO_3_CODE').apply(lambda x: x.to_dict('r')).to_json(
        'hrp_covid_weekly_trend.json', orient='index', indent=2)
    output_df.to_excel('hrp_covid_weekly_trend.xlsx')
    plt.show()


def get_WHO_data(H63_iso3):
    df=pd.read_csv(f'{DIR_PATH}/{WHO_COVID_FILENAME}')
    # get only HRP countries
    df = df.loc[df['ISO_3_CODE'].isin(H63_iso3),:]
    df['date_epicrv']=pd.to_datetime(df['date_epicrv'])
    df=df[['date_epicrv','ISO_3_CODE','CumCase','NewCase','NewDeath','CumDeath']]

    # adding global by date
    df_H63=df.groupby('date_epicrv').sum()
    df_H63['ISO_3_CODE']='H63'
    df_H63=df_H63.reset_index()

    # adding global by date
    df_H25=df.loc[df['ISO_3_CODE'].isin(H25_iso3),:]
    df_H25=df.groupby('date_epicrv').sum()
    df_H25['ISO_3_CODE']='H25'
    df_H25=df_H25.reset_index()

    # adding regional by date
    dict_regions=get_dict_regions(H63_iso3)
    df=pd.merge(left=df,right=dict_regions,left_on='ISO_3_CODE',right_on='ISO3',how='left')
    df=df.drop(labels='ISO3',axis='columns')
    df_regional=df.groupby(['date_epicrv','Regional_office']).sum().reset_index()
    df_regional=df_regional.rename(columns={'Regional_office':'ISO_3_CODE'})    

    df=df.append(df_H63)
    df=df.append(df_H25)
    df=df.append(df_regional)
    return df

def get_dict_regions(H63_iso3):
    dict_regions=pd.read_csv('countries/tbl_regcov_2020_ocha.csv')
    dict_regions=dict_regions[['ISO3','Regional_office']]
    dict_regions=dict_regions[dict_regions['ISO3'].isin(H63_iso3)]
    return dict_regions


def get_pop_data(H63_iso3):
    # Read in pop
    df_pop=pd.read_excel(POPULATION_FILENAME,sheet_name='Data',header=1,skiprows=[0,1],usecols='B,BK').rename(
        columns={'2018': 'population'})
    # Add H63
    df_pop = df_pop.append({'Country Code': 'H63',
                            'population':  df_pop.loc[df_pop['Country Code'].isin(H63_iso3), 'population'].sum()},
                           ignore_index=True)
    # Add H25
    df_pop = df_pop.append({'Country Code': 'H25',
                            'population':  df_pop.loc[df_pop['Country Code'].isin(H25_iso3), 'population'].sum()},
                           ignore_index=True)
    # add regions
    dict_regions=get_dict_regions(H63_iso3)
    df=pd.merge(left=df_pop,right=dict_regions,left_on='Country Code',right_on='ISO3',how='left')
    df=df.drop(labels='ISO3',axis='columns')
    df_regional=df.groupby(['Regional_office']).sum().reset_index()
    df_regional=df_regional.rename(columns={'Regional_office':'Country Code'})
    df_pop=df_pop.append(df_regional)

    return df_pop

if __name__ == '__main__':
    args = parse_args()
    main(download_covid=args.download_covid)
