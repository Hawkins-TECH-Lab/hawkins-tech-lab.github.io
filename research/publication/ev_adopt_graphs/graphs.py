import pandas as pd
import geopandas as gpd
import pandas as pd
import numpy as np
import geopandas as gpd

import plotly.graph_objects as go
import plotly.express as px


def check(row):
    return (row.filter(regex="^rp_code_")!=row.filter(regex="^sp.*adj$").min()).all()

def filter_edf(edf):
    # Update vehicle ownership to re-code "other" to "large car" and "other powertrain" to "ICE"
    # Also, add a new column with the SP code for each vehicle
    df = pd.DataFrame(data={"veh_type" : [1,2,3,1,2,3,1,2,3,1,2,3], "veh_pt" : [1,1,1,2,2,2,3,3,3,4,4,4], 
                    "rp_code" : [1,3,5,2,4,6,2,4,6,2,4,6]})

    for i in range(1,7):
        edf.loc[edf["veh_pt_{0}".format(i)]==5,"veh_pt_{0}".format(i)] = 1
        edf.loc[edf["veh_type_{0}".format(i)]==4,"veh_type_{0}".format(i)] = 2
        edf = edf.merge(df, how="left", left_on=["veh_type_{0}".format(i),"veh_pt_{0}".format(i)], right_on=["veh_type","veh_pt"], suffixes=[None,"_{0}".format(i)])
    edf.rename(columns={"rp_code": "rp_code_1"}, inplace=True)

    edf.veh_type_1.head(25)
    # Check condition that min SP response = max SP response - i.e., that all responses are the same
    colmin = edf.loc[:,edf.filter(regex="^sp.*adj$").columns].min(axis=1)
    colmax = edf.loc[:,edf.filter(regex="^sp.*adj$").columns].max(axis=1)
    cond1 = (colmin==colmax)
    # Check that none of the current HH vehicles are the same as the min SP choice, conditional on only one SP choice


    cond2 = edf.apply(check, axis=1)

    return edf[~(cond1*cond2)]

edf = pd.read_csv("data/ev_survey_data.csv")
# filter out records where the respondent gave the same answer to all SP experiments AND they also don't own that vehicle type
# print("edf rows before filter:", edf.shape[0])

filt_edf = filter_edf(edf)
# print("edf rows after filter:", filt_edf.shape[0])

geo_edf = gpd.GeoDataFrame(filt_edf, 
    geometry = gpd.points_from_xy(filt_edf['longitude'], filt_edf['latitude']), 
    crs = 'EPSG:3857')

ctydf = gpd.read_file("data/county_shp/county_L48_only.shp")
# ctydf = ctydf.to_crs(3857)
# filter states to include only survey region
survey_states = ["19","20","27","29","31","38","46"]
ctydf = ctydf.loc[ctydf.STATEFP.isin(survey_states)]

hh_size_dict = {
    16.0: "1",
    17.0: "2",
    18.0: "3",
    19.0: "4",
    20.0: "5",
    21.0: "6 or more"
}

next_veh_dict = {
    1: "Small car",
    2: "Large car",
    3: "Pickup truck",
    4: "Other vehicles"
}

color_map_veh_choice = {
    1: 'black',   # Dark Blue
    2: '#ff7f0e',   # Dark Orange
    3: '#2ca02c',   # Dark Green
    4: '#d62728',   # Dark Red
}


occupation_dict = {
    1.0: "Management, professional, and related",
    2.0: "Service",
    3.0: "Sales and office",
    4.0: "Farming, fishing, and forestry",
    5.0: "Construction, extraction, and maintenance",
    6.0: "Production, transportation, and material moving",
    7.0: "Government",
    8.0: "Retired",
    9.0: "Unemployed"
}


off_road_freq_dict = {
    1.0: "Rarely \n (1-3 times per year)",
    2.0: "Sometimes \n (1-3 times per month)",
    3.0: "Seasonally \n (1 or more times per week \n for one season)",
    4.0: "Frequently \n (1 or more times per week \n throughout the year)"
}

# make this dict more hex
color_map_off_road_freq = {
    1.0: '#1f77b4',
    2.0: '#2ca02c',
    3.0: '#d62728',
    4.0: '#ff7f0e',
}

parking_dict = {
    "bev_dwell_1": "Private enclosed garage",
    "bev_dwell_2": "Private non-enclosed garage",
    "bev_dwell_3": "Dedicated parking in shared facility (accommodate)",
    "bev_dwell_4": "Dedicated parking in shared facility (not accommodate)",
    "bev_dwell_5": "Street parking (accommodate)",
    "bev_dwell_6": "Street parking (not accommodate)",
    "bev_dwell_7": "No dedicated parking facility"
}


def get_next_veh_by_hh_size_graph():
    """
    returns graph for Next vehicle choice by household size
    """
    df_hh_size = geo_edf[['next_veh_type_1', 'hh_size']].copy()
    df_hh_size.loc[:, 'hh_size'] = df_hh_size['hh_size'].map(hh_size_dict)
    df_hh_size.loc[:, 'next_veh_type_1'] = df_hh_size['next_veh_type_1'].map(next_veh_dict)

    result = df_hh_size.groupby('hh_size')['next_veh_type_1'].value_counts().reset_index(name='count_each_veh_type')

    result['percentage'] = (result['count_each_veh_type'] / result.groupby('hh_size')['count_each_veh_type'].transform('sum'))

    # result['percentage'] = result['percentage'].apply(lambda x: round(x, 2))

    # convert result next_veh_type_1 to string
    result['next_veh_type_1'] = result['next_veh_type_1'].astype(str)

    fig = px.bar(result, x="hh_size", y="percentage", color="next_veh_type_1", barmode="stack")
    fig.update_layout(yaxis=dict(tickformat=".2%"))

    fig.update_layout(
        xaxis=dict(
            tickmode='linear',
            dtick=1,
            tickangle=0,
            title_text=None
        ),
        yaxis=dict(
            title_text=None
        ),
        height=500,
        title_text="Off-road driving frequency by expected next vehicle type",
        legend=dict(
            title_text=None  # Remove legend title
        ),
    )

    return fig