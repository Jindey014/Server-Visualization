# Filter data based on selections
filtered_df = df_merged.copy()

if selected_year != 'All':
    filtered_df = filtered_df[filtered_df['Installation Year'] == selected_year]

if selected_province != 'All':
    province_code = [key for key, value in province_names.items() if value == selected_province]
    if province_code:
        filtered_df = filtered_df[filtered_df['Province Code'] == province_code[0]]

if selected_district != 'All':
    filtered_df = filtered_df[filtered_df['District'] == selected_district]


district_counts = filtered_df['District'].value_counts().reset_index(name='District Count')
district_counts

# Count the occurrences of each district per year
district_counts_by_year = filtered_df.groupby(['DISTRICT_PCODE', 'Installation Year']).size().reset_index(name='Yearly Count')

# Cumulatively sum the district counts across years
district_counts_by_year['Cumulative Count'] = district_counts_by_year.groupby('DISTRICT_PCODE')['Yearly Count'].cumsum()


# Generate the map visualization
def generate_map(df, nepal_districts):
    # Merge district names into the aggregated data
    df = df.merge(df_merged[['DISTRICT_PCODE', 'District']].drop_duplicates(), on='DISTRICT_PCODE', how='left')

    # Define the color scale
    color_scale = "YlGnBu"

    # Create choropleth map
    fig = go.Figure(go.Choroplethmapbox(
        geojson=nepal_districts,
        locations=df['DISTRICT_PCODE'],
        z=df['Cumulative Count'],
        featureidkey="properties.DIST_PCODE",
        colorscale=color_scale,
        marker_opacity=0.5,
        marker_line_width=1,
        marker_line_color='black',
        coloraxis='coloraxis',
        text=df['District'],
        hoverinfo='text+z',
        hovertemplate="<b>%{text}</b><br>%{z} Servers<extra></extra>"
    ))

    # Update layout
    fig.update_layout(
        mapbox_style="carto-positron",
        mapbox_zoom=5.5,
        mapbox_center={"lat": 28.3949, "lon": 84.1240},
        margin={"r": 0, "t": 0, "l": 0, "b": 50},
        coloraxis=dict(colorscale=color_scale)
    )

     # Set dynamic tick values based on the maximum cumulative count for the latest year
    tick_values = [0, 20, 40, 60, 80]

    # Update color bar to be horizontal and positioned below the map
    fig.update_layout(
        coloraxis_colorbar=dict(
            title="Server Count",
            orientation='h',
            x=0.5,
            xanchor='center',
            y=-0.1,
            titleside='bottom',
            tickvals=tick_values,  # Dynamic tick values based on max count
            ticktext=[str(int(val)) for val in tick_values],  # Display the tick values as integers
            tickmode='array',  # Use array mode for better positioning
            lenmode='fraction',
            len=0.5,
            tickfont=dict(size=12),  # Adjust font size for better readability
        )
    )

    return fig

# Plot the map
fig = generate_map(district_counts_by_year, nepal_districts)
st.plotly_chart(fig)