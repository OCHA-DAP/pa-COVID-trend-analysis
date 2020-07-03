import pandas as pd
import os
import matplotlib.pyplot as plt
import geopandas as gpd


# filename for shapefile and WHO input dataset
DIR_PATH = os.path.dirname(os.path.realpath(__file__))
FILENAME_SHP = 'ne_10m_admin_0_countries/ne_10m_admin_0_countries.shp'

iso_codes=['SDN','SSD','AFG','HTI','COD']

output_df=pd.read_excel('hrp_covid_doubling_rates.xlsx')
world_boundaries=gpd.read_file('{}/{}'.format(DIR_PATH,FILENAME_SHP))

output_df_geo=world_boundaries.merge(output_df.drop_duplicates(keep='first'),
                                        left_on='ADM0_A3',right_on='iso3',how='left')
# plotting map
_, ax_map_gr = plt.subplots(figsize=[15,10],nrows=1,ncols=1)
output_df_geo.plot(column='pc_growth_rate',cmap='OrRd',ax=ax_map_gr, legend=True,legend_kwds={'label': "Daily Growth Rate",'orientation': "horizontal"})
output_df_geo.boundary.plot(ax=ax_map_gr,lw=0.5)

_, ax_map_dt = plt.subplots(figsize=[15,10],nrows=1,ncols=1)
output_df_geo.plot(column='doubling_time',cmap='OrRd_r',scheme='quantiles',ax=ax_map_dt, legend=True)
output_df_geo.boundary.plot(ax=ax_map_dt,lw=0.5)

output_df=output_df[output_df['iso3'].isin(iso_codes)]
output_df['date']=pd.to_datetime(output_df['date']).dt.date
output_df.sort_values(by='date',ascending=True)
output_df=output_df.set_index('date')

_, ax_gr = plt.subplots(figsize=[15,10],nrows=1,ncols=1)
for name, group in output_df.groupby('iso3'):
    group['pc_growth_rate'].plot(ax=ax_gr,label=name)
    color=plt.gca().lines[-1].get_color()
    ax_gr.fill_between(group.index,
                       group['pc_growth_rate'],
                       group['pc_growth_rate_min_window'],
                       alpha=0.1,
                       color=color)
    ax_gr.fill_between(group.index,
                       group['pc_growth_rate'],
                       group['pc_growth_rate_max_window'],
                       alpha=0.1,
                       color=color)

_, ax_dt = plt.subplots(figsize=[15,10],nrows=1,ncols=1)
for name, group in output_df.groupby('iso3'):
    group['doubling_time'].plot(ax=ax_dt,label=name)
    color=plt.gca().lines[-1].get_color()
    ax_dt.fill_between(group.index,
                       group['doubling_time'],
                       group['doubling_time_min_window'],
                       alpha=0.1,
                       color=color)
    ax_dt.fill_between(group.index,
                       group['doubling_time'],
                       group['doubling_time_max_window'],
                       alpha=0.1,
                       color=color)

plt.legend()


plt.show()