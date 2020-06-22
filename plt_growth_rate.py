import pandas as pd
import os
import matplotlib.pyplot as plt
import geopandas as gpd


# filename for shapefile and WHO input dataset
DIR_PATH = os.path.dirname(os.path.realpath(__file__))
FILENAME_SHP = 'ne_10m_admin_0_countries/ne_10m_admin_0_countries.shp'

iso_codes=['H63','SDN','SSD']

output_df=pd.read_excel('hrp_covid_doubling_rates.xlsx')

# world_boundaries=gpd.read_file('{}/{}'.format(DIR_PATH,FILENAME_SHP))
# output_df_geo=world_boundaries.merge(output_df.drop_duplicates(keep='first'),
#                                         left_on='ADM0_A3',right_on='iso3',how='left')
# # plotting map
# fig_map, ax_map = plt.subplots(figsize=[15,10],nrows=1,ncols=1)
# output_df_geo.plot(column='pc_growth_rate',cmap='OrRd',ax=ax_map, legend=True)
# output_df_geo.boundary.plot(ax=ax_map,lw=0.5)

fig_gr, ax_gr = plt.subplots(figsize=[15,10],nrows=1,ncols=1)
output_df=output_df[output_df['iso3'].isin(iso_codes)]
output_df['date']=pd.to_datetime(output_df['date']).dt.date
output_df.sort_values(by='date',ascending=True)
output_df=output_df.set_index('date')
for name, group in output_df.groupby('iso3'):
    group['pc_growth_rate'].plot(ax=ax_gr,label=name)
    color=plt.gca().lines[-1].get_color()
    ax_gr.fill_between(group.index,
                       group['pc_growth_rate'],
                       group['pc_growth_rate_min_window'],
                       alpha=0.3,
                       color=color)
    ax_gr.fill_between(group.index,
                       group['pc_growth_rate'],
                       group['pc_growth_rate_max_window'],
                       alpha=0.3,
                       color=color)



plt.legend()


plt.show()