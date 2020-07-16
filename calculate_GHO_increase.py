import pandas as pd
import datetime

WHO_COVID_URL='https://docs.google.com/spreadsheets/d/e/2PACX-1vSe-8lf6l_ShJHvd126J-jGti992SUbNLu-kmJfx1IRkvma_r4DHi0bwEW89opArs8ZkSY5G2-Bc1yT/pub?gid=0&single=true&output=csv'
MIN_CUMULATIVE_CASES = 100
JUNE_19=datetime.date(2020, 6, 19)
JULY_17=datetime.date(2020, 7, 17)
H63_iso3=['ABW', 'AFG', 'AGO', 'ARG', 'BDI', 'BEN', 'BFA', 'BGD', 'BOL', 'BRA', 'CAF', 'CHL', 'CMR', 'COD', 'COG', 'COL', 'CRI', 'CUW', 'DJI', 'DOM', 'ECU', 'EGY', 'ETH', 'GUY', 'HTI', 'IRN', 'IRQ', 'JOR', 'KEN', 'LBN', 'LBR', 'LBY', 'MEX', 'MLI', 'MMR', 'MOZ', 'NER', 'NGA', 'PAK', 'PAN', 'PER', 'PHL', 'PRK', 'PRY', 'PSE', 'RWA', 'SDN', 'SLE', 'SOM', 'SSD', 'SYR', 'TCD', 'TGO', 'TTO', 'TUR', 'TZA', 'UGA', 'UKR', 'URY', 'VEN', 'YEM', 'ZMB', 'ZWE']

df_WHO=pd.read_csv(WHO_COVID_URL)
# get only HRP countries
df_WHO = df_WHO.loc[df_WHO['ISO_3_CODE'].isin(H63_iso3),:]
# convert ot datetime
df_WHO['date_epicrv']=pd.to_datetime(df_WHO['date_epicrv']).dt.date
# keep only columns that we need
df_WHO=df_WHO[['date_epicrv','ISO_3_CODE','CumCase','CumDeath']]
# filter date
df_WHO=df_WHO[ (df_WHO['date_epicrv']>=JUNE_19) &\
               (df_WHO['date_epicrv']<=JULY_17) ]

output_fields = [
    'iso3',
    'june_cases',
    'june_deaths',
    'july_cases',
    'july_deaths',
    'increase_cases',
    'pc_increase_cases',
    'increase_deaths',
    'pc_increase_deaths',
    ]
output_df = pd.DataFrame(columns=output_fields)
for name,group in df_WHO.groupby('ISO_3_CODE'):
    group=group.sort_values(by='date_epicrv',ascending=True)
    june_index=group.index[0]
    july_index=group.index[-1]
    data = {
        'iso3':name,
        'june_cases':group.loc[june_index,'CumCase'],
        'june_deaths':group.loc[june_index,'CumDeath'],
        'july_cases':group.loc[july_index,'CumCase'],
        'july_deaths':group.loc[july_index,'CumDeath'],
        'increase_cases':group.loc[july_index,'CumCase']-group.loc[june_index,'CumCase'],
        'pc_increase_cases':(group.loc[july_index,'CumCase']-group.loc[june_index,'CumCase'])/group.loc[june_index,'CumCase']*100,
        'increase_deaths':group.loc[july_index,'CumDeath']-group.loc[june_index,'CumDeath'],
        'pc_increase_deaths':(group.loc[july_index,'CumDeath']-group.loc[june_index,'CumDeath'])/group.loc[june_index,'CumDeath']*100
        }
    output_df = output_df.append(pd.DataFrame([data]), ignore_index=True)

output_df.to_excel('HNO_increase_June-July.xlsx')