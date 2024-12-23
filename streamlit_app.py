import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
import json

# Load data into session state
if 'df_merged' not in st.session_state:
    # Open the file and read it into a DataFrame
    with open("data/merged_cleaned.csv", "r", encoding="utf-8", errors="replace") as f:
        st.session_state.df_merged = (
            pd.read_csv(f)
            .loc[:, lambda df: ~df.columns.str.contains('^Unnamed')]
            .assign(District=lambda x: x['District'].replace('-', pd.NA))  # Drop unnamed columns directly
        )

# Access the DataFrame
df_merged = st.session_state.df_merged

# Convert 'Installation Date' to datetime and extract the year as string
df_merged['Installation Date'] = pd.to_datetime(df_merged['Installation Date'], errors='coerce')
df_merged['Installation Year'] = df_merged['Installation Date'].dt.year.astype(str)
df_merged['Installation Year'] = pd.to_numeric(df_merged['Installation Year'], errors='coerce')
  # Convert to string

# Load the simplified GeoJSON for Nepal's districts
with open('data/nepal-districts-new-reduced.json') as geo:
    nepal_districts = json.load(geo)

# Extract province code and add it to the dataframe
province_mapping = {feature['properties']['DIST_PCODE']: feature['properties']['ADM1_PCODE']
                    for feature in nepal_districts['features']}
df_merged['Province Code'] = df_merged['DISTRICT_PCODE'].map(province_mapping)

# Convert 'DIST_PCODE' to string and handle NaN values
df_merged['DISTRICT_PCODE'] = df_merged['DISTRICT_PCODE'].fillna('Unknown').astype(str)

# Province names mapped to their codes
province_names = {
    'NP01': 'Koshi', 'NP02': 'Madhesh', 'NP03': 'Bagmati', 'NP04': 'Gandaki',
    'NP05': 'Lumbini', 'NP06': 'Karnali', 'NP07': 'Sudurpashchim'
}

# Prepare province options with names
province_options = ['All'] + [province_names.get(province, 'Unknown') for province in sorted(df_merged['Province Code'].dropna().unique())]

# Prepare year options
year_options = ['All'] +  sorted(
    [int(year) for year in df_merged['Installation Year'].dropna().unique() if isinstance(year, (int, float)) and year.is_integer()],
    reverse=True
)

district_options = ['All'] + sorted(df_merged.drop_duplicates(subset=['DISTRICT_PCODE'])['District'].dropna().loc[lambda x: x != '-'].tolist())

with st.sidebar:
    selected_province = st.selectbox("Select Province" ,province_options , index = 0)
    selected_year = st.selectbox("Select Installation Year" ,year_options , index = 0)
    selected_district = st.selectbox("Select  District" ,district_options , index = 0)


    # Group by 'Installation Year' and 'District', then count occurrences
district_counts = df_merged.groupby(['Installation Year', 'District']).size().reset_index(name='District Count')


df_merged['District Count'] = 1  # Assign 1 for counting occurrences
df_merged = df_merged.sort_values(by=['District', 'Installation Year']).reset_index(drop=True)

# Group by district and calculate cumulative counts
df_merged['Cumulative District Count'] = (
    df_merged.groupby('District')['District Count']
    .cumsum()
)

  # Group by 'District' to calculate the total occurrences across all years
total_district_counts = df_merged.groupby('District').size().reset_index(name='Total District')

# Merge the total_district_counts DataFrame back with df_merged
df_merged = df_merged.merge(total_district_counts, on='District', how='left')

st.write("Column Names:", df_merged.columns.tolist() )

# Now df_merged has the 'Total District' column, which contains the total occurrences for each district across all years

# Check the result
st.write(df_merged[['District', 'Total District_x','Total District_y']])


# Filter data based on selections
filtered_df = df_merged.copy()

if selected_year != 'All':
    # Filter to include all records up to the selected year
    filtered_df = filtered_df[filtered_df['Installation Year'] <= int(selected_year)]

if selected_province != 'All':
    province_code = [key for key, value in province_names.items() if value == selected_province]
    if province_code:
        filtered_df = filtered_df[filtered_df['Province Code'] == province_code[0]]

if selected_district != 'All':
    filtered_df = filtered_df[filtered_df['District'] == selected_district]

# Generate the map visualization with integrated functionality
def generate_map(df_merged, filtered_df, nepal_districts, selected_year, selected_province, selected_district):
    # Select the color column based on filters
    if selected_year == 'All' and selected_province == 'All' and selected_district == 'All':
        color_column = 'Total District'
        df_to_plot = df_merged.groupby('DISTRICT_PCODE').agg({
            'Total District': 'max',
            'District': 'first'
        }).reset_index()
    else:
        color_column = 'Cumulative District Count'
        df_to_plot = filtered_df.groupby('DISTRICT_PCODE').agg({
            'Cumulative District Count': 'max',
            'District': 'first'
        }).reset_index()

    # Define the color scale
    color_scale = "YlGnBu"

    # Create the choropleth map
    fig = go.Figure(go.Choroplethmapbox(
        geojson=nepal_districts,
        locations=df_to_plot['DISTRICT_PCODE'],
        z=df_to_plot[color_column],
        featureidkey="properties.DIST_PCODE",
        colorscale=color_scale,
        marker_opacity=0.8,
        marker_line_width=1,
        marker_line_color='black',
        coloraxis='coloraxis',
        text=df_to_plot['District'],
        hoverinfo='text+z',
        hovertemplate="<b>%{text}</b><br>%{z} Servers<extra></extra>"
    ))

    # Set dynamic tick values based on the maximum count
    max_count = df_to_plot[color_column].max()
    tick_values = np.linspace(0, max_count, num=5).astype(int).tolist()

    # Update layout
    fig.update_layout(
        mapbox_style="carto-positron",
        mapbox_zoom=5.5,
        mapbox_center={"lat": 28.3949, "lon": 84.1240},
        margin={"r": 0, "t": 0, "l": 0, "b": 50},
        coloraxis=dict(colorscale=color_scale),
        coloraxis_colorbar=dict(
            title="Server Count",
            orientation='h',
            x=0.5,
            xanchor='center',
            y=-0.1,
            titleside='bottom',
            tickvals=tick_values,  # Dynamic tick values
            ticktext=[str(val) for val in tick_values],  # Display the tick values as integers
            tickmode='array',
            lenmode='fraction',
            len=0.5,
            tickfont=dict(size=12),  # Adjust font size for readability
        )
    )

    return fig


# Plot the map
fig = generate_map(df_merged, filtered_df, nepal_districts, selected_year, selected_province, selected_district)
st.plotly_chart(fig, use_container_width=True)


#ADD RECORD FORM
with st.expander('Add Record'):
    #Necessary options for input
    district_options_for_input =["Select District Name"] + sorted(df_merged.drop_duplicates(subset=['DISTRICT_PCODE'])['District'].dropna().tolist())
    district_pcode_options =["Select District Code"] + sorted(df_merged['DISTRICT_PCODE'].dropna().unique().tolist())
    province_name_for_input = ["Select Province Name"] + [province_names.get(province, 'Unknown') for province in sorted(df_merged['Province Code'].dropna().unique())]
    province_pcode_options =["Select Province Code"] + sorted(df_merged['Province Code'].dropna().unique().tolist())

    #Actual form fields starts here
    st.header('Insert Record Here')
    detail_form = st.form(key="add_record_form")  # Added unique key
    detail_form.subheader('Server Version')
    server_version = detail_form.text_input("Server Model")
    installation_date = detail_form.date_input(
        "Installation Date",
        format="DD/MM/YYYY"  # This will show dates like "4 Oct 2010"
    )
    
    update_date = detail_form.date_input(
        "Server Update / Repair Date",
        format="DD/MM/YYYY"
    )

    detail_form.subheader("School Information")
    school_name = detail_form.text_input("School Name")
    emis_code = detail_form.text_input("Emis Code")
    detail_form.subheader("Local Government")
    adm2_en = detail_form.text_input("ADM2_EN")
    adm2_pcode = detail_form.text_input("ADM2_PCODE")
    detail_form.subheader("Address")
    district_name = detail_form.selectbox("District",district_options_for_input, index = 0)
    district_code = detail_form.selectbox("District Code", district_pcode_options, index = 0)
    province_name = detail_form.selectbox("Province Name", province_name_for_input,index=0)
    province_code = detail_form.selectbox("Province Code", province_pcode_options, index = 0)
    adm1_en = detail_form.number_input("ADM1_EN", min_value=0, step=1, format="%d")
    detail_form.subheader("Additional Information")
    teacher_name = detail_form.text_input("Teacher's Name")
    contact = detail_form.text_input("School Contact No.")
    desktop_no = detail_form.number_input("No. of Desktops", min_value=0, step=1, format="%d")
    laptop_no = detail_form.number_input("No. of Laptops", min_value=0, step=1, format="%d")
    mediator = detail_form.text_input("Mediator", value ="self")
    add_record = detail_form.form_submit_button(label="Add new record")

    if add_record:

        # Generate a new Serial Number (S.N)
        if 'S.N.' in df_merged.columns:
            new_sn = df_merged['S.N.'].max() + 1  # Get the max S.N and increment it
        else:
            new_sn = 1  # Start from 1 if S.N doesn't exist
        #Create a new record
        new_record = pd.DataFrame.from_records([{
            "S.N.": new_sn,
            "Server Model":server_version,
            "Installation Date":installation_date,
            "Server Update / Repair Date":update_date,
            "School Name":school_name,
            "EMIS Code":emis_code,
            "ADM2_EN":adm2_en,
            "ADM2_PCODE":adm2_pcode,
            "District":district_name,
            "DISTRICT_PCODE":district_code,
            "Province Name":province_name,
            "ADM1_PCODE":province_code,
            "ADM1_EN":adm1_en,
            "H/Teacher's Name":teacher_name,
            "School Contact":contact,
            "No. of Desktops":desktop_no,
            "No. of Laptops":laptop_no,
            "Mediator":mediator


        }])
                    # Update session state DataFrame
        st.session_state.df_merged = pd.concat([df_merged, new_record], ignore_index=True)

        #     # Debug: Show updated DataFrame
        # st.write("Updated DataFrame:", st.session_state.df_merged.tail())

            # Save to CSV
        try:
            st.session_state.df_merged.to_csv('data/merged_cleaned.csv', index=False)
            st.success(f"Record for {school_name} added successfully!")

                # Reload the page immediately
            st.rerun()  

        except Exception as e:
            st.error(f"Error saving file: {e}")




