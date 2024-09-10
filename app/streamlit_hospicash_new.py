import streamlit as st
import pandas as pd
import plotly.express as px
import base64
import subprocess
import sys
import geopandas as gpd
import plotly.io as pio
import requests
import plotly.graph_objects as go


pio.renderers.default = 'iframe'


############################################# DATA IMPORT ################################################################

df_pop = pd.read_excel('C:/Users/chtam/Documents/Pop_Data_England_Age_Sexe.xlsx')
ukdf=pd.read_csv(r"C:\Users\chtam\OneDrive - SiriusPoint\Life Folders\03 Pricing\1. Benchmarks\7. Hospital Cash\UK\Data\UK_data_for_webapp.csv")
data_admission=pd.read_excel("C:/Users/chtam/Documents/Admissions.xlsx")[['Year', 'Emergency', 'Planned','Waiting list', 'Other Admission  Method']]

ukdf_dic = {}
for year, group in ukdf[ukdf['Region']!='England'].groupby('year'):
    ukdf_dic[year] = {
        'Region': list(group['Region']),
        'Avg. days of stay': list(group['Avg. days of stay']),
        'No. of Discharges': list(group['No. of Discharges']),
        'Pop.': list(group['Pop.']),
        'Discharge Rate': list(group['Discharge Rate']),
    }

# fonction for Mexico demo
def generate_yearly_data(year, num_regions):
    variation = (year - 2016) * 0.1
    return {
        "average_length_of_stay": [4.5 + variation + i * 0.05 for i in range(num_regions)],
        "admission_rate_age_gender": pd.DataFrame({
            "Age": ["0-18", "19-35", "36-50", "51-70", "70+"],
            "Male": [60 + (year - 2016) * 5, 180 + (year - 2016) * 10, 250 + (year - 2016) * 15, 220 + (year - 2016) * 20, 110 + (year - 2016) * 10],
            "Female": [55 + (year - 2016) * 4, 170 + (year - 2016) * 9, 230 + (year - 2016) * 14, 210 + (year - 2016) * 19, 120 + (year - 2016) * 11]
        }),
        "length_of_stay_age_gender": pd.DataFrame({
            "Age": ["0-18", "19-35", "36-50", "51-70", "70+"],
            "Male": [4.0 + variation, 4.5 + variation, 5.0 + variation, 5.5 + variation, 6.0 + variation],
            "Female": [3.9 + variation, 4.4 + variation, 4.9 + variation, 5.4 + variation, 5.8 + variation]
        })
    }

####################################### DATA DICTIONARIES #################################################################################################
country_data_map = {
    "UK": {
        "regions": ["North East", "North West", "Yorkshire and The Humber", "East Midlands", "West Midlands", "Eastern", "London", "South East", "South West"],
        "repo": "https://raw.githubusercontent.com/martinjc/UK-GeoJSON/master/json/electoral/eng/eer.json",
        "lat": 54,
        "lon": 2,
        "data": ukdf_dic
    },
    "Mexico": {
        "regions": ["Aguascalientes", "Baja California", "Baja California Sur", "Campeche", "Coahuila de Zaragoza", "Colima", "Chiapas", "Chihuahua", "Ciudad de México",
                    "Durango", "Guanajuato", "Guerrero", "Hidalgo", "Jalisco", "México", "Michoacán de Ocampo", "Morelos", "Nayarit", "Nuevo León", "Oaxaca",
                    "Puebla", "Querétaro", "Quintana Roo", "San Luis Potosí", "Sinaloa", "Sonora", "Tabasco", "Tamaulipas", "Tlaxcala", "Veracruz de Ignacio de la Llave",
                    "Yucatán", "Zacatecas"],
        "repo": "https://raw.githubusercontent.com/strotgen/mexico-leaflet/master/states.geojson",
        "lat": 23,
        "lon": -102,
        "data": {year: generate_yearly_data(year, 32) for year in range(2016, 2023)}
    }
    
}

country_data_graphes = {
    "UK": {
        "data": {
            year: {
                "admission_rate_age_gender": df_year[['age_range', 'proportion']].rename(columns={'age_range': 'Age', 'proportion': 'Admission Rate'}),
                 "population_and_admissions": df_year[['age_range', 'population', 'admissions']].rename(columns={'age_range': 'Age'})
            }
            for year, df_year in df_pop.groupby('year')
        }
    },
    "Mexico":{
        "data": {
            year:{
                "admission_rate_age_gender": df_year[['age_range', 'proportion']].rename(columns={'age_range': 'Age', 'proportion': 'Admission Rate'}),
                 "population_and_admissions": df_year[['age_range', 'population', 'admissions']].rename(columns={'age_range': 'Age'})
            }
            for year, df_year in df_pop.groupby('year')
            }
        }
    }


age_order = ["Age 0", "Age 1-4", "Age 5-9", "Age 10-14", "Age 15-19", "Age 20-24",
             "Age 25-29", "Age 30-34", "Age 35-39", "Age 40-44", "Age 45-49",
             "Age 50-54", "Age 55-59", "Age 60-64", "Age 65-69", "Age 70-74",
             "Age 75-79", "Age 80-84", "Age 85-89", "Age 90+"]


####################### MAP FUNCTION #################################
def get_country_map(country, selected_year):
    country_df = pd.DataFrame({
        "Region": country_data_map["UK"]["data"][2020]["Region"],
        "Average Length of Stay": country_data_map[country]["data"][selected_year]["Avg. days of stay"],
        "Population": country_data_map[country]["data"][selected_year]["Pop."],
        "No. of Discharges": country_data_map[country]["data"][selected_year]["No. of Discharges"],
        "Discharge Rate": country_data_map[country]["data"][selected_year]["Discharge Rate"]
        
    })
    if country == "UK":
        repo_url = country_data_map[country]["repo"]
        res = requests.get(repo_url)
        fig = px.choropleth_mapbox(country_df, 
                                   locations="Region", 
                                   color="Average Length of Stay",
                                   geojson=res.json(), 
                                   featureidkey="properties.EER13NM",
                                   hover_name="Region",
                                   hover_data=country_df.columns.to_list(),
                                   color_continuous_scale="Blues",
                                   range_color=(0, None),
                                   mapbox_style="carto-positron",
                                   zoom=5, 
                                   center={"lat": country_data_map[country]["lat"], "lon": country_data_map[country]["lon"]},
                                   opacity=0.5
                                  )
        
        # NEWLY ADDED 
        fig.update_layout(
        margin={"r":0, "t":0, "l":0, "b":0},
        height=800,
        width=800,
        hoverlabel=dict(
            font_size=16,            # Font size of the text in the tooltip
            font_family="Arial",     # Font family of the text in the tooltip
        )
        )
    elif country == "Mexico":
        repo_url = country_data_map[country]["repo"]
        res = requests.get(repo_url)
        fig = px.choropleth_mapbox(country_df, locations="Region", color="Average Length of Stay",
                                   geojson=res.json(), featureidkey="properties.state_name", hover_name="Region",
                                   color_continuous_scale="Blues",
                                   range_color=(0, None),
                                   mapbox_style="carto-positron",
                                   zoom=4, center={"lat": country_data_map[country]["lat"], "lon": country_data_map[country]["lon"]},
                                   opacity=0.5
                                  )
    else:
        repo_url = country_data_map[country]["repo"]
        res = requests.get(repo_url)
        fig = px.choropleth_mapbox(country_df, locations="Region", color="Average Length of Stay",
                                   geojson=res.json(), featureidkey="properties.name", hover_name="Region",
                                   color_continuous_scale="Blues",
                                   range_color=(0, None),
                                   mapbox_style="carto-positron",
                                   zoom=3, center={"lat": country_data_map[country]["lat"], "lon": country_data_map[country]["lon"]},
                                   opacity=0.5
                                  )
    fig.update_layout(margin={"r":0,"t":0,"l":0,"b":0}, height=800, width=800)
    return fig

##################################### TITLE APP CONFIG ##############################################################
st.set_page_config(page_title="Hospicash Data Platform", layout="wide")

# Sidebar
st.sidebar.markdown("# Hospicash Data Platform")
selected_country = st.sidebar.selectbox('Select a country', list(country_data_map.keys()) + ["All Countries"])
selected_year = st.sidebar.selectbox('Select a year', list(range(2016, 2023)))

# Title
st.title("SiriusPoint Hospicash Data Platform")

################# DATA VISUALISATION ##############################

# Main Streamlit app logic
if selected_country == "All Countries":
    st.markdown("## Aggregated Data for All Countries")
    
    # For demo, a simple bar chart of average length of stay
    avg_length_all = pd.DataFrame({
        "Country": list(country_data_map.keys()),
        "Average Length of Stay": [
            sum(country_data_map[c]["data"][selected_year]["average_length_of_stay"]) / len(country_data_map[c]["data"][selected_year]["average_length_of_stay"]) 
            for c in country_data_map.keys()
        ]
    })
    fig_all = px.bar(avg_length_all, x="Country", y="Average Length of Stay",
                     color="Country", color_discrete_sequence=px.colors.sequential.Plasma)
    st.plotly_chart(fig_all, use_container_width=True)
else:
    st.markdown(f"## Insights for {selected_country} in {selected_year}")

    # Map section
    st.markdown("### Average Length of Stay by Region")
    map_fig = get_country_map(selected_country, selected_year)
    st.plotly_chart(map_fig, use_container_width=True)

    # Admission Rate by Age
    st.markdown("### Admission Rate by Age")
    admission_rate_df = country_data_graphes[selected_country]["data"][selected_year]["admission_rate_age_gender"]
    admission_rate_df['Age'] = pd.Categorical(admission_rate_df['Age'], categories=age_order, ordered=True)
    admission_rate_df = admission_rate_df.sort_values('Age')
    
    
    fig_admission = px.bar(admission_rate_df, x="Age", y="Admission Rate",
                           labels={"Admission Rate": "Admission Rate", "Age": "Age Range"},
                           text=admission_rate_df["Admission Rate"].apply(lambda x: f'{x*100:.2f}%'),
                           color_discrete_sequence=["#0077b6"])
    
    st.plotly_chart(fig_admission, use_container_width=True)

    # Number of Admissions and population by age
    
    st.markdown("### Number of Admissions and population by age")
    data_df_pop = country_data_graphes[selected_country]["data"][selected_year]["population_and_admissions"]

    # Convert the 'Age' column to a categorical type with the specified order
    data_df_pop['Age'] = pd.Categorical(data_df_pop['Age'], categories=age_order, ordered=True)
    data_df_pop = data_df_pop.sort_values('Age')
    # Reshape the DataFrame for a grouped bar plot
    melted_df = data_df_pop.melt(id_vars=["Age"], value_vars=["population", "admissions"], 
                             var_name="Category", value_name="Count")
    
    fig_grouped_bar = px.bar(melted_df, x="Age", y="Count", color="Category", barmode="group",
                             labels={"Count": "Count", "Age": "Age Range", "Category": "Type"},
                             color_discrete_sequence=["#0077b6", "#ced4da"])
    
    st.plotly_chart(fig_grouped_bar, use_container_width=True)
    
    # Waterfall chart for admission methods
    st.markdown("### Waterfall Chart of Admission Methods")

    # Filter data for the selected year
    filtered_data = data_admission[data_admission['Year'] == selected_year].iloc[0, 1:]  # Exclude the 'Year' column

    # Prepare data for the waterfall chart
    categories = filtered_data.index.tolist()
    values = filtered_data.values.tolist()
    bar_colors = ['#0077b6', '#0077b6', '#0077b6', '#0077b6', '#0077b6']
    waterfall_values = [values[0]] + [values[i] for i in range(1, len(values))] + [sum(values)]
    waterfall_labels = categories + ['Total Admissions']

    # Create the waterfall chart
    fig_waterfall = go.Figure(go.Waterfall(
        x=waterfall_labels,
        measure=['relative'] * len(categories) + ['total'],
        y=waterfall_values,
        text=[f"{value:,.0f}" for value in waterfall_values],
        textposition="outside",
        connector={"line": {"color": "rgb(63, 63, 63)"}},
    increasing={"marker": {"color": '#0077b6'}},
    decreasing={"marker": {"color": '#0077b6'}},
    totals={"marker": {"color": "#ced4da"}},
    ))

    fig_waterfall.update_layout(
        title=f"Waterfall Chart of Admission Methods for {selected_year}",
        width=1000, 
        height=600,
        plot_bgcolor='rgba(0,0,0,0)',  
        paper_bgcolor='rgba(0,0,0,0)', 
        xaxis=dict(
            showgrid=False,  
            zeroline=False,  
        ),
        yaxis=dict(
            showgrid=False, 
            zeroline=False, 
        ),
        showlegend=False
    )

    st.plotly_chart(fig_waterfall, use_container_width=True)

############## Function to be able to print the SiriusPoint logo ###########################################
def get_base64_of_bin_file(bin_file):
    with open(bin_file, 'rb') as f:
        data = f.read()
    return base64.b64encode(data).decode()

################ logo and Background #################
logo_image_path = "C:/Users/chtam/app/siriuspt_logo.jpg"

# Encoding the logo image
logo_base64 = get_base64_of_bin_file(logo_image_path)

#################### LET'S ADD SOME STYLE NOW ########################################
st.markdown(
    f"""
    <style>
    .logo-container {{
        position: fixed;
        top: 65px;
        right: 10px;
        z-index: 1000;
    }}
    </style>
    <div class="logo-container">
        <img src="data:image/png;base64,{logo_base64}" alt="Logo" width="150">
    </div>
    """,
    unsafe_allow_html=True
)
