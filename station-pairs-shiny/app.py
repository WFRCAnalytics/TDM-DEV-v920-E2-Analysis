from shiny import App, render, ui
import pandas as pd

# Load or define your data here
import os
file_path = os.path.join(os.path.dirname(__file__), "station-pairs-data.csv")
data_df = pd.read_csv(file_path)

app_ui = ui.page_fluid(
    ui.h2("Commuter Rail Trips by Station-Pairs -- 2019 Model and On-Board Survey"),
    ui.layout_sidebar(
        ui.sidebar(
            ui.input_select("model1", "Select Model:", choices=data_df['model'].unique().tolist()),
            ui.input_select("model2", "Compare to:", choices=["None"] + data_df['model'].unique().tolist()),
            ui.input_selectize("purpose", "Purpose:", choices=data_df['purpose'].unique().tolist(), multiple=True, selected=data_df['purpose'].unique().tolist()),
            ui.input_selectize("period", "Period:", choices=data_df['period'].unique().tolist(), multiple=True, selected=data_df['period'].unique().tolist()),
            ui.input_selectize("mode", "Mode:", choices=data_df['mode'].unique().tolist(), multiple=True, selected=data_df['mode'].unique().tolist()),
            ui.input_checkbox("show_percent", "Show Percent Difference", value=False),
            ui.input_checkbox("show_share", "Show Share of Total", value=False)
        ),
        ui.layout_columns(
            ui.output_data_frame("crosstab_output"),
            ui.output_data_frame("total_output"),
            col_widths=[9, 3]  # Adjust the ratio (e.g., 8:4 means Crosstab gets 2x more space)
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
        total_row = pd.DataFrame({'STATION_ID': ['ALL'], 'trips_total': [total_sum]})

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
            total_row = pd.DataFrame({'STATION_ID': ['ALL'], 'trips_total_divide': [total_sum]})

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
            total_row = pd.DataFrame({'STATION_ID': ['ALL'], 'trips_total': [total_sum]})

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
                total_row = pd.DataFrame({'STATION_ID': ['ALL'], 'trips_total_divide': [total_sum]})

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
        
        
        filtered_data_1.rename(columns={'trips_total':'display_value'}, inplace=True)
        total_table = total_stations_1.rename(columns={'trips_total':'display_value'})

        total_table['display_value'] = total_table['display_value'].apply(
            lambda x: f"{x:,.2f}%" if input.show_share() and x != 0 
            else "--" if input.show_share() and x == 0 
            else f"{int(x):,}" if x != 0 
            else "--"
        )

        # Create a crosstab view with STATION_ID_1 as rows and STATION_ID_2 as columns
        crosstab_table = filtered_data_1.pivot(index='STATION_ID_1', columns='STATION_ID_2', values='display_value').fillna(0)
        crosstab_table = crosstab_table.applymap(lambda x: f"{x:,.2f}%" if input.show_share() and x != 0 else "--" if input.show_share() and x == 0 else f"{int(x):,}" if x != 0 else "--")
        crosstab_table = crosstab_table.reset_index()  # Move index to a proper column
        crosstab_table.columns.name = None  # Remove extra column group name if exists
        return crosstab_table, total_table



    @output
    @render.data_frame
    def crosstab_output():
        return generate_outputs()[0]  # Crosstab Data

    @output
    @render.data_frame
    def total_output():
        return generate_outputs()[1]  # Total Data
    
app = App(app_ui, server)
