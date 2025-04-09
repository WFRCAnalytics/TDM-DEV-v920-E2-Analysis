from shiny import App, render, ui
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import os

# Load or define your data here
file_path = os.path.join(os.path.dirname(__file__), "boardings.csv")
data_df = pd.read_csv(file_path)

app_ui = ui.page_fluid(
    ui.h2("OD Boardings/Alightings 2019 -- On-Board Survey vs Automated Passenger Counters"),
    ui.layout_sidebar(
        ui.sidebar(
            ui.input_select("board_alight", "Measure:", choices=['Boardings','Alightings','Board+Alight / 2'], selected='Board'),
            ui.input_selectize("period", "Period:", choices=sorted(data_df['Period'].unique().tolist()), multiple=True, selected=data_df['Period'].unique().tolist()),
            ui.input_selectize("direction", "Direction:", choices=data_df['Direction'].unique().tolist(), multiple=True, selected=data_df['Direction'].unique().tolist()),
        ),
        ui.output_plot("chart_output", height="600px")  
    )
)

def server(input, output, session):
    
    def get_filtered_data():
        _df = data_df[(data_df['Period'   ].isin(input.period())) &
                      (data_df['Direction'].isin(input.direction()))]
        return _df.groupby(['Station_Sequence','Source'], as_index=False).agg(plot_value=(input.board_alight(),'sum'))

    def generate_outputs():
        df_filtered = get_filtered_data().sort_values(['Station_Sequence'])

        if df_filtered.empty:
            return  # Prevents an error if no data matches filters

        # Plot
        fig, ax = plt.subplots(figsize=(10, 6))
        sns.barplot(
            data=df_filtered,
            x="Station_Sequence",
            y="plot_value",
            hue="Source",
            ax=ax
        )

        ax.set_title(input.board_alight() + " Comparison by Source & Station")
        ax.set_xlabel("")
        ax.set_ylabel(input.board_alight())
        ax.tick_params(axis="x", rotation=90)  # Rotate x-axis labels for readability
        ax.legend(title="Source")
        ax.yaxis.grid(True)  # ✅ Add horizontal grid lines
        ax.set_axisbelow(True)
        
        return fig
    
    @output
    @render.plot
    def chart_output():
        return generate_outputs()

app = App(app_ui, server)
