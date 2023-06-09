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

    # Check condition that min SP response = max SP response - i.e., that all responses are the same
    colmin = edf.loc[:,edf.filter(regex="^sp\d+$").columns].min(axis=1)
    colmax = edf.loc[:,edf.filter(regex="^sp\d+$").columns].max(axis=1)
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

geo_edf["x"] = geo_edf.geometry.x
geo_edf["y"] = geo_edf.geometry.y

ctydf = gpd.read_file("data/county_shp/county_L48_only.shp")
# filter states to include only survey region
survey_states = ["19","20","27","29","31","38","46"]
ctydf = ctydf.loc[ctydf.STATEFP.isin(survey_states)]
stdf = pd.read_csv("data/us-state-fips.csv")
stdict = dict(stdf.values)
ctydf["state_name"] = ctydf.STATEFP.astype(int).map(stdict)
ctydf["county_state"] = ctydf.NAME+", "+ctydf.state_name

sp_dict = {1: "Small ICE", 2: "Small BEV", 3: "Large ICE", 4: "Large BEV", 5:"Pickup truck ICE", 6: "Pickup truck BEV"}
geo_edf["Choice 1"] = geo_edf["sp1"].map(sp_dict)
geo_edf["Choice 2"] = geo_edf["sp2"].map(sp_dict)
geo_edf["Choice 3"] = geo_edf["sp3"].map(sp_dict)
geo_edf["Choice 4"] = geo_edf["sp4"].map(sp_dict)
geo_edf["Choice 5"] = geo_edf["sp5"].map(sp_dict)
geo_edf["Choice 6"] = geo_edf["sp6"].map(sp_dict)


unl_colors = [
    # '#001226',  # Midnight Blue
    '#d00000',  # Scarlet
    '#249ab5',  # Light Blue
    '#bccb2a',  # Lime Green
    '#f58a1f',  # Orange
    '#005d84',  # Dark Cerulean
    '#ffd74f',  # Mustard
    '#a5228d',  # Electric Purple
    '#ff2851',  # Coral Red
    '#008080',  # Teal
    '#f9a602',  # Goldenrod
    '#4c516d',  # Charcoal
    '#eb6101',  # Bright Orange
    '#5dbb63',  # Moss Green
    '#6930c3',  # Deep Purple
    '#e83f6f',  # Razzmatazz
    '#2e7d32',  # Medium Green
    '#ffc400',  # Selective Yellow
    '#1a237e',  # Indigo
    '#c51162',  # Fuchsia Pink
    '#006064',  # Dark Cyan
    '#ff4081',  # Pink Flamingo
    '#546e7a',  # Slate Gray
    '#ffa000',  # Amber
    '#1b5e20',  # Forest Green
    '#4a148c',  # Purple
    '#00acc1',  # Robin Egg Blue
    '#e65100',  # Persimmon
    '#7e57c2',  # Medium Purple
    '#3e2723',  # Bistre
    '#ef6c00',  # Pumpkin
    '#00695c',  # Dark Green
]



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

next_pt_dict = {
    1: "ICE",
    2: "BEV",
    3: "HEV",
    4: "PHEV",
    5: "Other"
}

next_veh_time_dict = {
    1: "Within 1 year",
    2: "In 1-3 years",
    3: "In 4-7 years",
    4: "In 8-10 years",
    5: "In 11 or more years"
}

veh_pt_dict = {1: "ICE", 2: "BEV", 3: "HEV", 4: "PHEV"}
veh_type_dict = {1: "Small car - ", 2: "Large car - ", 3: "Pickup truck - "}
sp1_dict = {1: "Small car - ICE", 2: "Small car - BEV", 3: "Large car - ICE", 4: "Large car - BEV", 5:"Pickup truck - ICE", 6: "Pickup truck - BEV"}

color_map_next_veh_choice = ['#bccb2a', '#f58a1f', '#005d84', '#ffd74f']


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
    1.0: 'black',
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

def get_fig_survey_locations():
    df_survey_locations = geo_edf.copy()
    df_cty = ctydf.copy()
    df_cty['state_name'] = pd.Categorical(df_cty['state_name'], ordered=True)
    df_cty.sort_values("state_name", inplace=True)
    fig1 = px.scatter_geo(df_survey_locations,
                        color_discrete_sequence=['black'],
                        lon=geo_edf["x"],
                        lat=geo_edf["y"],
                        hover_data={"Choice 1":True,
                                    "Choice 2":True,
                                    "Choice 3":True,
                                    "Choice 4":True,
                                    "Choice 5":True,
                                    "Choice 6":True,
                                    "x":False, 
                                    "y":False,
                                        },
                        hover_name="CUID")
    
    fig1.update_traces(marker=dict(size=8,
                              line=dict(width=1,
                                        color='white')),
                  selector=dict(mode='markers'))
    
    fig2 = px.choropleth(df_cty,
                        locations=df_cty.index,
                        color="state_name",
                        color_discrete_sequence=unl_colors,
                        geojson=df_cty.geometry,
                        hover_data={"state_name":False},
                        hover_name="county_state").add_traces(fig1.data)

    fig2.update_geos(fitbounds="locations")
    fig2.update_layout(
            geo_scope='usa',
            legend_title_text='State'
        )
    return fig2

def get_fig_next_veh_by_hh_size_graph():
    """
    returns graph for Next vehicle choice by household size
    """
    df_hh_size = geo_edf[['next_veh_type_1', 'hh_size']].copy()
    # combine other vehicle to large car
    df_hh_size['next_veh_type_1'] = df_hh_size['next_veh_type_1'].copy().apply(lambda x: 2 if x == 4 else x)
    df_hh_size.loc[:, 'hh_size'] = df_hh_size['hh_size'].map(hh_size_dict)
    df_hh_size.loc[:, 'next_veh_type_1'] = df_hh_size['next_veh_type_1'].map(next_veh_dict)

    result = df_hh_size.groupby('hh_size')['next_veh_type_1'].value_counts().reset_index(name='count_each_veh_type')

    result['percentage'] = (result['count_each_veh_type'] / result.groupby('hh_size')['count_each_veh_type'].transform('sum'))

    # result['percentage'] = result['percentage'].apply(lambda x: round(x, 2))

    # convert result next_veh_type_1 to string
    result['next_veh_type_1'] = result['next_veh_type_1'].astype(str)

    fig = px.bar(result, x="hh_size", y="percentage", color="next_veh_type_1", barmode="stack", color_discrete_sequence=unl_colors)

    fig.update_layout(yaxis=dict(tickformat=".0%"))

    fig.update_layout(
        xaxis=dict(
            tickmode='linear',
            dtick=1,
            tickangle=0,
            title_text='Household size',
        ),
        yaxis=dict(
            title_text="Percent of sub-population",

        ),
        # height=500,
        legend=dict(
            title_text="Next vehicle choice"
        ),
    )

    return fig

def get_fig_off_freq_by_occ():
    df_off_freq_by_occ = geo_edf[['occupation', 'veh_off_road', 'off_road_freq']].copy()
    df_off_freq_by_occ[df_off_freq_by_occ['veh_off_road']==1.0]

    df_off_freq_by_occ = df_off_freq_by_occ.sort_values(by=['off_road_freq'])
    df_off_freq_by_occ.loc[:, 'occupation_legend'] = df_off_freq_by_occ['occupation'].map(occupation_dict)
    df_off_freq_by_occ.loc[:, 'off_road_freq'] = df_off_freq_by_occ['off_road_freq'].map(off_road_freq_dict)

    # count the number of each off road frequency by occupation
    result = df_off_freq_by_occ.groupby('occupation_legend')['off_road_freq'].value_counts().reset_index(name='count_each_off_road_freq')

    # calulate the percentage of each off road frequency
    result['percentage'] = result['count_each_off_road_freq'] / result.groupby('occupation_legend')['count_each_off_road_freq'].transform('sum')

    # convert off_road_freq to string as it is categorical (We need to change this to proper categorical variable later)
    result['off_road_freq'] = result['off_road_freq'].astype(str)


    # plot it in stacked bar chart
    fig = px.bar(result, x="occupation_legend", y="percentage", color="off_road_freq", barmode="stack", color_discrete_sequence=unl_colors)

    fig.update_layout(
        xaxis=dict(
            tickmode='linear',
            dtick=1,
            tickangle=50,
            title_text="Occupation"
        ),
        yaxis=dict(
            title_text="Percent of sub-population"
        ),
        height=650,
        title_text=None,
        legend=dict(
            title_text="Off-road driving frequency by occupation"
        ),


    )
    fig.for_each_trace(lambda t: t.update(name=t.name.replace("\n", "<br>")))
    fig.update_layout(yaxis=dict(tickformat=".0%"))

    #manually reorder the legend based on frequency
    data_reordered = [fig.data[0], fig.data[1], fig.data[3], fig.data[2]]
    fig.data = data_reordered

    return fig

def get_fig_off_road_by_next_veh():
    df_off_road_next_veh = geo_edf[['next_veh_type_1', 'veh_off_road','off_road_freq']].copy()
    df_off_road_next_veh[df_off_road_next_veh['veh_off_road']==1.0]

    # combine other vehicle to large car
    df_off_road_next_veh['next_veh_type_1'] = df_off_road_next_veh['next_veh_type_1'].copy().apply(lambda x: 2 if x == 4 else x)

    df_off_road_next_veh.loc[:, 'next_veh_type_1'] = df_off_road_next_veh['next_veh_type_1'].map(next_veh_dict)

    df_off_road_next_veh.loc[:, 'off_road_freq'] = df_off_road_next_veh['off_road_freq'].map(off_road_freq_dict)

    # Define the vehicle order
    vehicle_order = ["Small car", "Large car", "Pickup truck"]

    # sort the graph in order
    df_off_road_next_veh_copy = df_off_road_next_veh.copy()
    df_off_road_next_veh_copy['next_veh_type_1'] = pd.Categorical(df_off_road_next_veh_copy['next_veh_type_1'], categories=vehicle_order, ordered=True)
    df_off_road_next_veh = df_off_road_next_veh_copy


    # count the number of each off road frequency by next vehicle type
    result = df_off_road_next_veh.groupby('next_veh_type_1')['off_road_freq'].value_counts().reset_index(name='count_each_off_road_freq')

    # calulate the percentage of each off road frequency make it out of 100
    result['percentage'] = result['count_each_off_road_freq'] / result.groupby('next_veh_type_1')['count_each_off_road_freq'].transform('sum')

    # convert off_road_freq to string as it is categorical (We need to change this to proper categorical variable later)
    result['off_road_freq'] = result['off_road_freq'].astype(str)

    # result['off_road_freq'] = result['off_road_freq'].map(color_map_off_road_freq)

    # plot it in stacked bar chart
    fig = px.bar(result, x="next_veh_type_1", y="percentage", color="off_road_freq", barmode="stack", color_discrete_sequence=unl_colors)

    # change the percentage to 2 decimal places
    fig.for_each_trace(lambda t: t.update(name=t.name.replace("\n", "<br>")))
    fig.update_layout(yaxis=dict(tickformat=".0%"))


    fig.update_layout(
        xaxis=dict(
            tickmode='linear',
            dtick=1,
            tickangle=0,
            title_text=None
        ),
        yaxis=dict(
            title_text="Percent of sub-population"
        ),
        height=500,
        legend=dict(
            title_text="Off-road driving frequency by next vehicle type"
        ),
    )
    #manually reorder the legend based on frequency
    data_reordered = [fig.data[0], fig.data[1], fig.data[3], fig.data[2]]
    fig.data = data_reordered

    return fig


def get_fig_time_fuel_type():
    df_time_fuel_type = geo_edf[['next_veh', 'next_veh_pt_1']].copy()

    df_time_fuel_type.loc[:, 'next_veh_pt_1'] = df_time_fuel_type['next_veh_pt_1'].map(next_pt_dict)
    df_time_fuel_type = df_time_fuel_type.sort_values(by=['next_veh'])
    df_time_fuel_type.loc[:, 'next_veh'] = df_time_fuel_type['next_veh'].map(next_veh_time_dict)
    df_time_fuel_type.columns = ['next_veh_purchase_time', 'next_veh_pt']

    # reorder the next_veh_purchase_time based on the order of next_veh_time_dict not the alphabetical order
    veh_buying_time_order = next_veh_time_dict.values()
    df_time_fuel_type_copy = df_time_fuel_type.copy()
    df_time_fuel_type_copy['next_veh_purchase_time'] = pd.Categorical(df_time_fuel_type_copy['next_veh_purchase_time'], categories=veh_buying_time_order, ordered=True)
    df_time_fuel_type = df_time_fuel_type_copy

    result = df_time_fuel_type.groupby('next_veh_purchase_time')['next_veh_pt'].value_counts().reset_index(name='count_each_fuel_type')

    # convert count to percentage
    result['percentage'] = result['count_each_fuel_type'] / result.groupby('next_veh_purchase_time')['count_each_fuel_type'].transform('sum')

    # convert next_veh_pt to string as it is categorical (We need to change this to proper categorical variable later)
    result['next_veh_pt'] = result['next_veh_pt'].astype(str)
    result['next_veh_purchase_time'] = result['next_veh_purchase_time'].astype(str)

    #show points on line chart
    fig = px.line(result, x="next_veh_purchase_time", y="percentage", color="next_veh_pt", markers=True, color_discrete_sequence=unl_colors)

    fig.update_layout(
    xaxis=dict(
        tickmode='linear',
        dtick=1,
        tickangle=50,
        title_text = 'Purchase time',
    ),
    yaxis=dict(
        title_text="Percent of sub-population"
    ),
    height=500,
    legend=dict(
        title_text="Next vehicle by powertrain and purchase year"
    ),
    )
    fig.update_layout(yaxis=dict(tickformat=".0%"))


    return fig

def get_fig_parking():
    df_charging_loc = geo_edf[parking_dict.keys()].copy()
    df_charging_loc.rename(columns=parking_dict, inplace=True)

    # df_charging_loc.astype(int)

    result = pd.DataFrame(df_charging_loc.sum().reset_index(name='count'))

    # change the column name
    result.columns = ['charging_loc', 'count']

    # make a pie chart
    fig = px.pie(result, values='count', names='charging_loc', color_discrete_sequence=unl_colors)

    fig.update_layout(
    xaxis=dict(
        tickmode='linear',
        dtick=1,
        tickangle=0
    ),
    height=600,
    legend=dict(
        title_text=None  # Remove legend title
    ),
    )
    
    return fig


def prepare_df_sankey(df, source, target):
    label_list = df[source].unique().tolist() + df[target].unique().tolist()

    df['source_index'] = df[source].copy().apply(lambda x: label_list.index(x))
    df['target_index'] = df[target].copy().apply(lambda x: label_list.index(x))

    return df, label_list

def apply_legend_curr_sp1(df):

    veh_pt_dict = {1: "ICE", 2: "BEV", 3: "HEV", 4: "PHEV"}
    veh_type_dict = {1: "Small car - ", 2: "Large car - ", 3: "Pickup truck - "}
    sp1_dict = {1: "Small car - ICE", 2: "Small car - BEV", 3: "Large car - ICE", 4: "Large car - BEV", 5:"Pickup truck - ICE", 6: "Pickup truck - BEV"}

    next_dict = {}
    for i in sp1_dict.keys():
            next_dict[i] = f"{sp1_dict[i]}"

    curr_dict = {}
    for i in veh_type_dict.keys():
        for j in veh_pt_dict.keys():
            # print(f"C_{i}_C_{j} = {veh_pt_dict[i]}__{veh_type_dict[j]}")
            curr_dict[f"C_{i}_C_{j}"] = f"{veh_type_dict[i]} {veh_pt_dict[j]}"

    df.loc[:, 'source_label'] = df['source'].map(curr_dict)
    df.loc[:, 'target_label'] = df['target'].map(next_dict)

    return df


def get_fig_sankey_curr_sp_veh():
   # getting data
    df_for_sankey = geo_edf[
        ['veh_pt_1', 'veh_type_1', 'sp1', 'comb_weight']
    ].copy()

    #data cleaning
    df_for_sankey.fillna(-1, inplace=True)
    df_for_sankey = df_for_sankey[(df_for_sankey['veh_pt_1'] != -1)&(df_for_sankey['veh_type_1'] != -1)&(df_for_sankey['sp1'] != -1)].copy()
    df_for_sankey [['veh_pt_1', 'veh_type_1', 'sp1',]] = df_for_sankey[['veh_pt_1', 'veh_type_1', 'sp1']].astype(int)

    # data processing
    result = df_for_sankey.groupby(['veh_type_1', 'veh_pt_1', 'sp1']).sum('comb_weight').reset_index()
    result.sort_values(by=['veh_pt_1', 'veh_type_1', 'sp1'], inplace=True)

    result['source'] = result['veh_pt_1'].astype(str) +"_" + result['veh_type_1'].astype(str)
    result['target'] = result['sp1'].astype(str)
    result['veh_pt_1'] = result['veh_pt_1'].map(veh_pt_dict)
    result['veh_type_1'] = result['veh_type_1'].map(veh_type_dict)
    result['sp1'] = result['sp1'].map(sp_dict)

    #preparing for sankey
    result['source_label'] = result['veh_type_1'] + result['veh_pt_1']
    result['target_label'] = result['sp1']
    result = result[['source', 'target', 'comb_weight', 'source_label', 'target_label']].copy()

    diff = 15

    fig = go.Figure()

    for i in range(0, int(result['comb_weight'].max()) + diff, diff):
        df_x = result[result['comb_weight'] > i].copy()
        df, tmp_label_list = prepare_df_sankey(df_x, 'source', 'target')


        label_list = df['source_label'].unique().tolist() + df['target_label'].unique().tolist()


        fig.add_trace(
            go.Sankey(
                node=dict(
                    pad=15,
                    thickness=20,
                    line=dict(color="black", width=0.5),
                    label=label_list,
                    color = unl_colors,
                    x=[0, 0, 0, 1, 1, 1, 1]  # Adjust x-axis position for each node
                ),
                link=dict(
                    source=df['source_index'].to_list(),
                    target=df['target_index'].to_list(),
                    value=df['comb_weight'].to_list(),
                ),
                visible=False  # Set the visibility of the trace to False initially
            )
        )



    # Create and add slider
    steps = []
    for i in range(len(fig.data)-1):
        step = dict(
            method="update",
            args=[{"visible": [False] * len(fig.data)},
                #   {"title": f"Slider switched to comb weight > {str(i * diff)}"}],  # layout attribute
            ],
            label=f" "  # Set custom label for each step
        )
        step["args"][0]["visible"][i] = True  # Toggle i'th trace to "visible"
        steps.append(step)

    n = 2 # slider default value
    sliders = [dict(
    active=n,  # Set the default step index
    currentvalue={"prefix": ""},
    # pad={"t": 50},
    steps=steps
    )]

    fig.update_layout(
    sliders=sliders
    )

    fig.data[n].visible = True  # Toggle first trace to "visible"



    return fig


def apply_legend_curr_next(df):
    curr_veh_pt_dict = {1: "ICE", 2: "BEV", 3: "HEV", 4: "PHEV", 5: "Other"}
    curr_veh_type_dict = {1: "Small car - ", 2: "Large car - ", 3: "Pickup truck - "}

    next_veh_pt_dict = {1: "ICE", 2: "BEV", 3: "HEV", 4: "PHEV", 5: "Other"}
    next_veh_type_dict = {1: "Small car - ", 2: "Large car - ", 3: "Pickup truck - "}

    curr_dict = {}
    for i in curr_veh_type_dict.keys():
        for j in curr_veh_pt_dict.keys():
            curr_dict[f"C_{i}_C_{j}"] = f"{curr_veh_type_dict[i]} {curr_veh_pt_dict[j]}"

    next_dict = {}
    for i in next_veh_type_dict.keys():
        for j in next_veh_pt_dict.keys():
            # print(f"C_{i}_C_{j} = {next_veh_pt_dict[i]}__{next_veh_type_dict[j]}")
            next_dict[f"N_{i}_N_{j}"] = f"{next_veh_type_dict[i]} {next_veh_pt_dict[j]}"

    df.loc[:, 'source_label'] = df['source'].map(curr_dict)
    df.loc[:, 'target_label'] = df['target'].map(next_dict)

    return df


def get_fig_sankey_curr_next():

    df_for_sankey = geo_edf[
        ['veh_type_1',  'veh_pt_1', 'next_veh_type_1', 'next_veh_pt_1', 'comb_weight']
    ].copy()

    # update codes to replace other codes
    df_for_sankey['veh_type_1'] = df_for_sankey['veh_type_1'].copy().apply(lambda x: 2 if x == 4 else x)
    df_for_sankey['next_veh_type_1'] = df_for_sankey['next_veh_type_1'].copy().apply(lambda x: 2 if x == 4 else x)

    # filter out the rows that is not -1
    df_for_sankey.fillna(-1, inplace=True)
    df_for_sankey = df_for_sankey[
        (df_for_sankey['veh_type_1'] != -1) & (df_for_sankey['next_veh_type_1'] != -1) & (df_for_sankey['next_veh_pt_1'] != -1) & (df_for_sankey['veh_pt_1'] != -1)
        ].copy()

    df_for_sankey[['veh_type_1',  'veh_pt_1', 'next_veh_type_1', 'next_veh_pt_1',]] = df_for_sankey[['veh_type_1',  'veh_pt_1', 'next_veh_type_1', 'next_veh_pt_1',]].copy().astype(int)

    df_for_sankey['veh_type_1'] = "C_"+df_for_sankey['veh_type_1'].copy().astype(str) 
    df_for_sankey['veh_pt_1'] = "C_"+df_for_sankey['veh_pt_1'].copy().astype(str) 
    df_for_sankey['next_veh_type_1'] = "N_"+df_for_sankey['next_veh_type_1'].copy().astype(str)
    df_for_sankey['next_veh_pt_1'] = "N_"+df_for_sankey['next_veh_pt_1'].copy().astype(str)

    df_for_sankey['source'] = df_for_sankey['veh_pt_1'] + "_" + df_for_sankey['veh_type_1']
    df_for_sankey['target'] = df_for_sankey['next_veh_pt_1'] + "_" + df_for_sankey['next_veh_type_1']
    df_x = df_for_sankey.groupby(['source', 'target']).sum('comb_weight').reset_index()



    df, label_list = prepare_df_sankey(df_x, 'source', 'target')


    diff = 15

    fig = go.Figure()

    for i in range(0, int(df['comb_weight'].max()) + diff, diff):
        df_x = df[df['comb_weight'] > i].copy()
        df, label_list = prepare_df_sankey(df_x, 'source', 'target')
        apply_legend_curr_next(df)

        # values = df['comb_weight'].to_list()

        label_list = df['source_label'].unique().tolist() + df['target_label'].unique().tolist()

        fig.add_trace(
            go.Sankey(
                node=dict(
                    pad=15,
                    thickness=20,
                    line=dict(color="black", width=0.5),
                    label=label_list,
                    color = unl_colors,
                    x=[0, 0, 0, 1, 1, 1, 1]  # Adjust x-axis position for each node
                ),
                link=dict(
                    source=df['source_index'].to_list(),
                    target=df['target_index'].to_list(),
                    value=df['comb_weight'].to_list(),
                ),
                visible=False  # Set the visibility of the trace to False initially
            )
        )



    # Create and add slider
    steps = []
    for i in range(len(fig.data)-1):
        step = dict(
            method="update",
            args=[{"visible": [False] * len(fig.data)},
                #   {"title": f"Slider switched to comb weight > {str(i * diff)}"}],  # layout attribute
            ],
            label=f" "  # Set custom label for each step
        )
        step["args"][0]["visible"][i] = True  # Toggle i'th trace to "visible"
        steps.append(step)

    n = 2 # slider default value
    sliders = [dict(
    active=n,  # Set the default step index
    currentvalue={"prefix": ""},
    # pad={"t": 50},
    steps=steps
    )]

    fig.update_layout(
    sliders=sliders
    )

    fig.data[n].visible = True  # Toggle first trace to "visible"
    # fig.update_layout(title_text=f"Sankey Diagram: comb weight > {n*diff}", font_size=10)

    return fig
