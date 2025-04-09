from shiny import App, render, ui
import pandas as pd


# Load or define your data here
import os
file_path = os.path.join(os.path.dirname(__file__), "station-pairs-data.csv")
data_df = pd.read_csv(file_path)
data_df.replace({"dCRT": "drive", "wCRT": "walk"}, inplace=True)
data_df.replace({"PK": "peak", "OK": "off-peak"}, inplace=True)

app_ui = ui.page_fluid(
    ui.head_content(
        ui.tags.style("""
            h2 {
                font-weight: bold !important;
                margin-top: 10pt;  /* Add 10pt space above */
            }
            /* Right-align all table cells by default */
            td {
                text-align: right !important;
            }
            /* Left-align only the first column (leftmost column) */
            td:first-child, th:first-child {
                text-align: left !important;
                width: min-content;  /* Reduce to fit the content */
                white-space: nowrap; /* Prevent text from wrapping */
            }
            /* Alternating row colors */
            tr:nth-child(even) {
                background-color: #f2f2f2;
            }
            tr:nth-child(odd) {
                background-color: #ffffff;
            }
            th:not(:first-child), td:not(:first-child) {
                text-align: center; /* Optional: Center text inside columns */
            }
        """)
    ),
    ui.h2("Commuter Rail Trips by Station-Pairs - 2019 Models and On-Board Survey"),
    ui.span("The following were removed from the analysis due to matching CRT distances: Clearfield to Woods Cross, Clearfield to SL Central, Woods Cross to Draper, SL Central to Draper"),
    ui.layout_sidebar(
        ui.sidebar(
            ui.input_select("model1", "Select Model:", choices=data_df['model'].unique().tolist()),
            ui.input_select("model2", "Compare to:", choices=["None"] + data_df['model'].unique().tolist(), selected="On-Board Survey"),
            ui.input_selectize("purpose", "Purpose:", choices=data_df['purpose'].unique().tolist(), multiple=True, selected=data_df['purpose'].unique().tolist()),
            ui.input_selectize("period", "Period:", choices=data_df['period'].unique().tolist(), multiple=True, selected=data_df['period'].unique().tolist()),
            ui.input_selectize("mode", "Initial Access Mode:", choices=data_df['mode'].unique().tolist(), multiple=True, selected="drive"),
            ui.input_checkbox("show_percent", "Percent Difference", value=False),
            ui.input_checkbox("show_share", "Share of Total", value=False)
        ),
        ui.layout_columns(
            ui.output_data_frame("crosstab_output"),
            ui.output_data_frame("total_output"),
            col_widths=[9, 2, 2]  # Adjust the ratio (e.g., 8:4 means Crosstab gets 2x more space)
        )
    )
)

def server(input, output, session):
    
    def get_model1_filtered_data():
        return data_df[(data_df['purpose'].isin(input.purpose())) &
                       (data_df['period' ].isin(input.period())) &
                       (data_df['mode'   ].isin(input.mode())) &
                       (data_df['model'  ]==input.model1())]

    def get_model1_all_data():
        return data_df[(data_df['model'  ]==input.model1())]

    def get_model2_filtered_data():
        return data_df[(data_df['purpose'].isin(input.purpose())) &
                       (data_df['period'].isin(input.period())) &
                       (data_df['mode'].isin(input.mode())) &
                       (data_df['model']==input.model2())]

    def get_model2_all_data():
        return data_df[(data_df['model'  ]==input.model1())]
        
    def generate_outputs():
        # Fetch user inputs
        show_share = input.show_share()

        filtered_data_1 = get_model1_filtered_data().groupby(['STATION_ID_1','STATION_ID_2'],as_index=False).agg(trips_total=('trips_total','sum'))

        # Aggregate totals for all unique STATION_IDs appearing in STATION_ID_1 or STATION_ID_2
        total_stations_1 = pd.concat([
            filtered_data_1.groupby('STATION_ID_1', as_index=False).agg(trips_total=('trips_total', 'sum')).rename(columns={'STATION_ID_1': 'STATION_ID'}),
            filtered_data_1.groupby('STATION_ID_2', as_index=False).agg(trips_total=('trips_total', 'sum')).rename(columns={'STATION_ID_2': 'STATION_ID'})
        ])

        # Sum total trips for each unique STATION_ID (handling cases where it appears in both columns)
        total_stations_1 = total_stations_1.groupby('STATION_ID', as_index=False).agg(trips_total=('trips_total', 'sum'))

        # Add a total row summing up all trips
        total_sum = filtered_data_1['trips_total'].sum()
        total_row = pd.DataFrame({'STATION_ID': ['16-ALL'], 'trips_total': [total_sum]})

        # Append the total row to the dataframe
        total_stations_1 = pd.concat([total_stations_1, total_row], ignore_index=True)

        if show_share:
            filtered_data_to_divide_by_1 = get_model1_all_data()
            filtered_data_to_divide_by_1 = filtered_data_to_divide_by_1.groupby(['STATION_ID_1','STATION_ID_2'], as_index=False).agg(trips_total_divide=('trips_total','sum')) 
            filtered_data_1 = pd.merge(filtered_data_1, filtered_data_to_divide_by_1, on=['STATION_ID_1','STATION_ID_2'])
            filtered_data_1['trips_total'] = filtered_data_1['trips_total'] / filtered_data_1['trips_total_divide'] * 100
            filtered_data_1 = filtered_data_1[['STATION_ID_1','STATION_ID_2','trips_total']]

            # Aggregate totals for all unique STATION_IDs appearing in STATION_ID_1 or STATION_ID_2
            total_stations_two_divide_by_1 = pd.concat([
                filtered_data_to_divide_by_1.groupby('STATION_ID_1', as_index=False).agg(trips_total_divide=('trips_total_divide', 'sum')).rename(columns={'STATION_ID_1': 'STATION_ID'}),
                filtered_data_to_divide_by_1.groupby('STATION_ID_2', as_index=False).agg(trips_total_divide=('trips_total_divide', 'sum')).rename(columns={'STATION_ID_2': 'STATION_ID'})
            ])
            total_stations_two_divide_by_1 = total_stations_two_divide_by_1.groupby('STATION_ID', as_index=False).agg(trips_total_divide=('trips_total_divide', 'sum'))

            # Add a total row summing up all trips
            total_sum = filtered_data_to_divide_by_1['trips_total_divide'].sum()
            total_row = pd.DataFrame({'STATION_ID': ['16-ALL'], 'trips_total_divide': [total_sum]})

            # Append the total row to the dataframe
            total_stations_two_divide_by_1 = pd.concat([total_stations_two_divide_by_1, total_row], ignore_index=True)

            total_stations_1 = pd.merge(total_stations_1, total_stations_two_divide_by_1, on=['STATION_ID'])
            total_stations_1['trips_total'] = total_stations_1['trips_total'] / total_stations_1['trips_total_divide'] * 100
            total_stations_1 = total_stations_1[['STATION_ID','trips_total']]
            
        if input.model2() != 'None': 

            filtered_data_2 = get_model2_filtered_data()

            filtered_data_2 = filtered_data_2.groupby(['STATION_ID_1','STATION_ID_2'],as_index=False).agg(trips_total=('trips_total','sum'))
            
            # Aggregate totals for all unique STATION_IDs appearing in STATION_ID_1 or STATION_ID_2
            total_stations_2 = pd.concat([
                filtered_data_2.groupby('STATION_ID_1', as_index=False).agg(trips_total=('trips_total', 'sum')).rename(columns={'STATION_ID_1': 'STATION_ID'}),
                filtered_data_2.groupby('STATION_ID_2', as_index=False).agg(trips_total=('trips_total', 'sum')).rename(columns={'STATION_ID_2': 'STATION_ID'})
            ])

            # Sum total trips for each unique STATION_ID (handling cases where it appears in both columns)
            total_stations_2 = total_stations_2.groupby('STATION_ID', as_index=False).agg(trips_total=('trips_total', 'sum'))

            # Add a total row summing up all trips
            total_sum = filtered_data_2['trips_total'].sum()
            total_row = pd.DataFrame({'STATION_ID': ['16-ALL'], 'trips_total': [total_sum]})

            # Append the total row to the dataframe
            total_stations_2 = pd.concat([total_stations_2, total_row], ignore_index=True)

            if show_share:
                filtered_data_to_divide_by_2 = get_model2_all_data()
                filtered_data_to_divide_by_2 = filtered_data_to_divide_by_2.groupby(['STATION_ID_1','STATION_ID_2'], as_index=False).agg(trips_total_divide=('trips_total','sum'))
                filtered_data_2 = pd.merge(filtered_data_2, filtered_data_to_divide_by_2, on=['STATION_ID_1','STATION_ID_2'])
                filtered_data_2['trips_total'] = filtered_data_2['trips_total'] / filtered_data_2['trips_total_divide'] * 100
                filtered_data_2 = filtered_data_2[['STATION_ID_1','STATION_ID_2','trips_total']]

                # Aggregate totals for all unique STATION_IDs appearing in STATION_ID_1 or STATION_ID_2
                total_stations_two_divide_by_2 = pd.concat([
                    filtered_data_to_divide_by_2.groupby('STATION_ID_1', as_index=False).agg(trips_total_divide=('trips_total_divide', 'sum')).rename(columns={'STATION_ID_1': 'STATION_ID'}),
                    filtered_data_to_divide_by_2.groupby('STATION_ID_2', as_index=False).agg(trips_total_divide=('trips_total_divide', 'sum')).rename(columns={'STATION_ID_2': 'STATION_ID'})
                ])
                total_stations_two_divide_by_2 = total_stations_two_divide_by_2.groupby('STATION_ID', as_index=False).agg(trips_total_divide=('trips_total_divide', 'sum'))

                # Add a total row summing up all trips
                total_sum = filtered_data_to_divide_by_2['trips_total_divide'].sum()
                total_row = pd.DataFrame({'STATION_ID': ['16-ALL'], 'trips_total_divide': [total_sum]})

                # Append the total row to the dataframe
                total_stations_two_divide_by_2 = pd.concat([total_stations_two_divide_by_2, total_row], ignore_index=True)

                total_stations_2 = pd.merge(total_stations_2, total_stations_two_divide_by_2, on=['STATION_ID'])
                total_stations_2['trips_total'] = total_stations_2['trips_total'] / total_stations_2['trips_total_divide'] * 100
                total_stations_2 = total_stations_2[['STATION_ID','trips_total']]

            # Merge data on common keys to align before subtraction
            merged_data = pd.merge(
                filtered_data_1, 
                filtered_data_2, 
                on=['STATION_ID_1', 'STATION_ID_2'], 
                suffixes=('_m1', '_m2'), 
                how='outer'
            ).fillna(0)  # Fill missing values with 0 for subtraction

            # Merge data on common keys to align before subtraction
            merged_data_side = pd.merge(
                total_stations_1, 
                total_stations_2, 
                on=['STATION_ID'], 
                suffixes=('_m1', '_m2'), 
                how='outer'
            ).fillna(0)  # Fill missing values with 0 for subtraction
                    
            
            if input.show_percent():

                if not show_share:

                    # Compute percentage difference safely, setting to 0 when denominator is zero
                    merged_data['trips_diff'] = merged_data.apply(
                        lambda row: ((row['trips_total_m1'] - row['trips_total_m2']) / row['trips_total_m2'] * 100)
                        if row['trips_total_m2'] != 0 else 0,  # Set to 0 if denominator is zero
                        axis=1
                    )

                    # Compute percentage difference safely, setting to 0 when denominator is zero
                    merged_data_side['trips_diff'] = merged_data_side.apply(
                        lambda row: ((row['trips_total_m1'] - row['trips_total_m2']) / row['trips_total_m2'] * 100)
                        if row['trips_total_m2'] != 0 else 0,  # Set to 0 if denominator is zero
                        axis=1
                    )

                    merged_data_side = merged_data_side[['STATION_ID','trips_diff']]
                    merged_data_side['trips_diff'] = merged_data_side['trips_diff'].fillna(0).astype(int).astype(str).map(lambda x: f"{x}%")

                    # Create pivot table and format percentages properly
                    pivot = merged_data.pivot(
                        index='STATION_ID_1', 
                        columns='STATION_ID_2', 
                        values='trips_diff'
                    ).fillna(0).astype(int).astype(str).applymap(lambda x: f"{x}%" if x != "0" else "")  # Convert to string with percentage

                else:
                    pivot = pd.DataFrame()
                    merged_data_side = pd.DataFrame()

            else:
                
                # Compute absolute difference
                merged_data['trips_diff'] = merged_data['trips_total_m1'].fillna(0) - merged_data['trips_total_m2'].fillna(0)

                merged_data_side['trips_diff'] = merged_data_side['trips_total_m1'].fillna(0) - merged_data_side['trips_total_m2'].fillna(0)
                merged_data_side = merged_data_side[['STATION_ID','trips_diff']]


                if show_share:
                    # Create pivot table with formatted numbers
                    pivot = merged_data.pivot(
                        index='STATION_ID_1', 
                        columns='STATION_ID_2', 
                        values='trips_diff'
                    ).fillna(0).astype(int).applymap(lambda x: f"{x}%" if x != "0" else "").replace("0%","")  # Format with comma separator 
                    merged_data_side['trips_diff'] = merged_data_side['trips_diff'].fillna(0).astype(int).map(lambda x: f"{x}%" if x != "0" else "")
                else:
                    # Create pivot table with formatted numbers
                    pivot = merged_data.pivot(
                        index='STATION_ID_1', 
                        columns='STATION_ID_2', 
                        values='trips_diff'
                    ).fillna(0).astype(int).applymap(lambda x: f"{x:,}").replace("0","")  # Format with comma separator
                    merged_data_side['trips_diff'] = merged_data_side['trips_diff'].fillna(0).astype(int).map(lambda x: f"{x:,}")



            # Apply conditional formatting
            pivot_table = pivot#.style.applymap(color_ramp)
            #styled_df = pivot.style.applymap(color_ramp)
            side_table = merged_data_side#.style.applymap(color_ramp)#.hide(axis="index")
        else:
            if show_share:
                # Create pivot table
                pivot_table = filtered_data_1.pivot(
                    index='STATION_ID_1', 
                    columns='STATION_ID_2', 
                    values='trips_total'
                ).fillna(0).astype(int).applymap(lambda x: f"{x}%" if x != "0" else "").replace("0%","")
                total_stations_1['trips_total'] = total_stations_1['trips_total'].astype(int).map(lambda x: f"{x}%" if x != "0" else "")
            else:
                # Create pivot table
                pivot_table = filtered_data_1.pivot(
                    index='STATION_ID_1', 
                    columns='STATION_ID_2', 
                    values='trips_total'
                ).fillna(0).astype(int).applymap(lambda x: f"{x:,}" if x != "0" else "").replace("0","")
                total_stations_1['trips_total'] = total_stations_1['trips_total'].astype(int).map(lambda x: f"{x:,}" if x != 0 else "")
            side_table = total_stations_1#.style.hide(axis="index")


        # Reset index to ensure STATION_ID_1 is included
        pivot_table = pivot_table.reset_index()
        pivot_table.columns.name = None  # Remove extra column group name if exists

        # Function to generate color mapping as a dictionary
        def color_ramp_styles(df):
            """Generate styles in df_styles format based on color ramp."""
            styles = [
                {  # General table style
                    "location": "body",
                    "style": {
                        "background-color": "white",
                        "border": "0px"
                    },
                },
                {
                    "location": "body",
                    "style": {
                        "padding": "2px",  # ✅ Reduce cell padding
                    },
                }
            ]

            max_val = 1000
            #max_val = df.fillna(0).select_dtypes(include=["number"]).abs().astype(int).max().max()


            for i, row in df.iterrows():
                for col_idx, col_name in enumerate(df.columns):
                    try:
                        num_val = int(str(row[col_name]).replace('%', '').replace(',', ''))
                    except ValueError:
                        continue  # Skip non-numeric values

                    # Normalize value range (cap at ±1000 for consistent scaling)
                    norm_val = max(min(num_val, max_val), -max_val)
                    scale_factor = (abs(norm_val) / max_val) ** 0.7  

                    if norm_val < 0:
                        blue_intensity = int((1 - scale_factor) * 255)
                        color = f'rgba({blue_intensity}, {blue_intensity}, 255, 0.9)'
                        text_color = "white" if blue_intensity < 128 else "black"  # White text for dark blue

                    elif norm_val > 0:
                        red_intensity = int((1 - scale_factor) * 255)
                        color = f'rgba(255, {red_intensity}, {red_intensity}, 0.9)'
                        text_color = "white" if red_intensity < 128 else "black"  # White text for dark red

                    else:
                        color = "white"
                        text_color = "black"  # Default text color for white background

                    # Append styling rule for this specific row/col
                    styles.append({
                        "location": "body",
                        "rows": [i],  # Row index
                        "cols": [col_idx],  # Column index
                        "style": {
                            "color": text_color,
                            "background-color": color
                        },
                    })

            return styles
        
        return render.DataTable(pivot_table, styles=color_ramp_styles(pivot_table)), render.DataTable(side_table, styles=color_ramp_styles(side_table))


    @output
    @render.data_frame
    def crosstab_output():
        return generate_outputs()[0]  # Crosstab Data

    @output
    @render.data_frame
    def total_output():
        return generate_outputs()[1]  # Total Data
    
app = App(app_ui, server)
