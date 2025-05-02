import pandas as pd

obs_df = pd.read_csv(r"C:\Users\bhereth\Documents\2019 Final Weighted UTA OD Data - 2022-04-05 - processed.csv", low_memory=False)

purposes = ['HBW','HBC','NHB','HBO']
periods = ['PK','OK']
accesses = ['dCRT','wCRT']

# station input variable
df_stations = pd.DataFrame([
    ["15-PROVO CENTRAL STATION"    , 50024, 40.22544 , -111.660632,  850, 'Utah'      ],
    ["14-OREM CENTRAL STATION"     , 50029, 40.28014 , -111.725489,  500, 'Utah'      ],
    ["13-AMERICAN FORK STATION"    , 50035, 40.374774, -111.820649,  550, 'Utah'      ],
    ["12-LEHI STATION"             , 50040, 40.425196, -111.896354,  735, 'Utah'      ],
    ["11-DRAPER STATION"           , 10008, 40.515484, -111.904407,  600, 'Salt Lake' ],
    ["10-SOUTH JORDAN STATION"     , 10010, 40.563155, -111.900753,  575, 'Salt Lake' ],
    ["09-MURRAY CENTRAL STATION"   , 10016, 40.659758, -111.896432, 1100, 'Salt Lake' ],
    ["08-SALT LAKE CENTRAL STATION", 10019, 40.76234 , -111.909052,  150, 'Salt Lake' ],
    ["07-NORTH TEMPLE STATION"     , 10021, 40.772532, -111.905124,  375, 'Salt Lake' ],
    ["06-WOODS CROSS STATION"      , 10025, 40.880457, -111.903151,  230, 'Davis'     ],
    ["05-FARMINGTON STATION"       , 10031, 40.987266, -111.903667,  870, 'Davis'     ],
    ["04-LAYTON STATION"           , 10035, 41.056903, -111.964955,  380, 'Davis'     ],
    ["03-CLEARFIELD STATION"       , 10036, 41.094769, -112.013807,  560, 'Davis'     ],
    ["02-ROY STATION"              , 10042, 41.188757, -112.039378,  500, 'Weber'     ],
    ["01-OGDEN STATION"            , 10046, 41.224285, -111.980631,  475, 'Weber'     ]
], columns=["station", "N", 'Lat', 'Lon', 'PNR_Spaces', 'County'])

# function to summarize tdm values
def summarize_tdm_stats(path_brdings, path_riders, df_stations1, source_name, pa_od):
    # read in csvs
    df_brding_summary = pd.read_csv(path_brdings, low_memory=False)
    df_rider_summary = pd.read_csv(path_riders, low_memory=False)
    
    
    # -------------------------------------------------------------------------------------------#
    # Boarding Summary Node 
    # -------------------------------------------------------------------------------------------#
    # Left join `df_brding_summary` with `df_stations` on column `N`
    df_brdsum_1 = pd.merge(df_brding_summary, df_stations1, on="N", how="left")
    
    # Filter to CRT line where station is not NaN and Name is "RCRT_OGPN"
    df_brdsum_2 = df_brdsum_1[df_brdsum_1["station"].notna() & (df_brdsum_1["Name"] == "RCRT_OGPN")]
    
    # Summarize total PA level boardings/alightings for each station
    df_brdsum_totals = (df_brdsum_2.groupby(["Purpose", "Period", "AccessMode", "station"], as_index=False).agg(Brd_PA=("Board", "sum"), Alt_PA=("Alight", "sum")))
    
    
    # -------------------------------------------------------------------------------------------#
    # Rider Summary Link 
    # -------------------------------------------------------------------------------------------#
    # perform the two left joins and rename columns
    df_ridsum_1 = (
        pd.merge(df_rider_summary, df_stations1, left_on="B", right_on="N", how="left")
        .rename(columns={"station": "brd_station"})
        .merge(df_stations1, left_on="A", right_on="N", how="left")
        .rename(columns={"station": "alt_station"})
        .drop(columns={'N_x','N_y'})
    )
    
    # filter out data that doesn't make sense and filter for specific access links
    df_ridsum_2 = df_ridsum_1[
        ((df_ridsum_1["brd_station"].notna()) & (df_ridsum_1["A"] < 10000)) |
        ((df_ridsum_1["alt_station"].notna()) & (df_ridsum_1["B"] < 10000))
    ]
    df_ridsum_2 = df_ridsum_2[df_ridsum_2["Mode"].isin([80, 11])]
    df_ridsum_2["FromSkim_CRT"] = pd.to_numeric(df_ridsum_2["FromSkim_CRT"], errors="coerce")
    
    # group by and sum up at the brd_station level
    df_ridsum_brd = (
        df_ridsum_2
        .dropna(subset=["brd_station"])
        .groupby(["Purpose", "Period", "AccessMode", "Mode", "brd_station"], as_index=False)
        .agg(direct_acc_egg=("FromSkim_CRT", "sum"))
        .assign(direction="access", brd_alt="Brd_Direct_PA")
    )
    
    # group by and sum up at the alt_station level
    df_ridsum_alt = (
        df_ridsum_2
        .dropna(subset=["alt_station"])  # Drop rows where alt_station is NaN
        .groupby(["Purpose", "Period", "AccessMode", "Mode", "alt_station"], as_index=False)
        .agg(direct_acc_egg=("FromSkim_CRT", "sum"))
        .assign(direction="egress", brd_alt="Alt_Direct_PA")
    )
    
    # concat brding and alting tables
    df_ridsum_3 = pd.concat([df_ridsum_brd, df_ridsum_alt], ignore_index=True).drop(columns={'brd_alt'})
    
    # reorganize
    df_ridsum_3_long = (
        df_ridsum_3
        .melt(
            id_vars=["Purpose", "Period", "AccessMode", "Mode", "direct_acc_egg"],
            value_vars=["brd_station", "alt_station"],
            var_name="brd_alt",
            value_name="station"
        )
    )
    
    # rename columns, get rid of na, and reset index
    df_ridsum_3_long = df_ridsum_3_long[df_ridsum_3_long["station"].notna()]
    df_ridsum_3_long["brd_alt"] = df_ridsum_3_long["brd_alt"].map({
        "brd_station": "Brd_Direct_PA",
        "alt_station": "Alt_Direct_PA"
    })
    df_ridsum_3_long = df_ridsum_3_long.reset_index(drop=True)
    
    # further cleanup and reorganization of df
    df_ridsum_4 = (
        df_ridsum_3_long
        .drop(columns=["Mode", "direction"], errors="ignore")
        .pivot_table(
            index=["Purpose", "Period", "AccessMode", "station"],
            columns="brd_alt",
            values="direct_acc_egg",
            aggfunc="sum"
        )
        .reset_index()
    )
    
    # remove the multiindex on columns
    df_ridsum_4.columns.name = None 
    df_ridsum_4 = df_ridsum_4.rename_axis(None, axis=1)
    

    # -------------------------------------------------------------------------------------------#
    # Join Node and Link Data
    # -------------------------------------------------------------------------------------------#
    # join node and link data together into one table
    df_ridsum_summary = df_brdsum_totals.merge(df_ridsum_4,on=["Purpose", "Period", "AccessMode", "station"],how="left")
    
    # calculate transfer columns
    df_ridsum_summary["Brd_Transfer_PA"] = (df_ridsum_summary["Brd_PA"] - df_ridsum_summary["Brd_Direct_PA"])
    df_ridsum_summary["Alt_Transfer_PA"] = (df_ridsum_summary["Alt_PA"] - df_ridsum_summary["Alt_Direct_PA"])
    
    # select columns
    df_ridsum_summary = df_ridsum_summary[["station", "Purpose", "Period", "AccessMode","Brd_PA", "Brd_Direct_PA", "Brd_Transfer_PA","Alt_PA", "Alt_Direct_PA", "Alt_Transfer_PA"]]
    

    # -------------------------------------------------------------------------------------------#
    # Finalize PA Dataframe
    # -------------------------------------------------------------------------------------------#
    # group by Purpose, AccessMode, and station, then calculate aggregated values
    df_ridsum_pa = (
        df_ridsum_summary
        .groupby(["Purpose", "AccessMode", "station"], as_index=False)
        .agg(
            Brd_PA=("Brd_PA", "sum"),
            Brd_Direct_PA=("Brd_Direct_PA", "sum"),
            Brd_Transfer_PA=("Brd_Transfer_PA", "sum"),
            Alt_PA=("Alt_PA", "sum"),
            Alt_Direct_PA=("Alt_Direct_PA", "sum"),
            Alt_Transfer_PA=("Alt_Transfer_PA", "sum")
        )
    )
    
    df_ridsum_pa['Source'] = source_name
    df_ridsum_pa = df_ridsum_pa[['Source','station','AccessMode','Brd_PA','Brd_Direct_PA','Brd_Transfer_PA']]  #,'Alt_PA','Alt_Direct_PA','Alt_Transfer_PA']]
    
    
    # -------------------------------------------------------------------------------------------#
    # Convert to OD Format (if wanted)
    # -------------------------------------------------------------------------------------------#
    # group by Purpose, AccessMode, and station, then calculate aggregated values
    df_brdsum_od = (
        df_ridsum_summary
        .groupby(["Purpose", "AccessMode", "station"], as_index=False)
        .agg(
            BrdDy=("Brd_PA", "sum"),
            BrdDyDirect=("Brd_Direct_PA", "sum"),
            BrdDyTransfer=("Brd_Transfer_PA", "sum"),
            AltDy=("Alt_PA", "sum"),
            AltDyDirect=("Alt_Direct_PA", "sum"),
            AltDyTransfer=("Alt_Transfer_PA", "sum")
        )
    )
    
    # add calculated columns for OD metrics
    df_brdsum_od["Brd_OD"] = (df_brdsum_od["BrdDy"] + df_brdsum_od["AltDy"]) / 2
    df_brdsum_od["Brd_Direct_OD"] = (df_brdsum_od["BrdDyDirect"] + df_brdsum_od["AltDyDirect"]) / 2
    df_brdsum_od["Brd_Transfer_OD"] = (df_brdsum_od["BrdDyTransfer"] + df_brdsum_od["AltDyTransfer"]) / 2
    
    # drop intermediate columns that are no longer needed
    df_brdsum_od = df_brdsum_od.drop(
        columns=["BrdDy", "AltDy", "BrdDyDirect", "AltDyDirect", "BrdDyTransfer", "AltDyTransfer"]
    )
    
    # add source and drop purpose
    df_brdsum_od['Source'] = source_name
    df_brdsum_od = df_brdsum_od[['Source','station','AccessMode','Brd_OD','Brd_Direct_OD','Brd_Transfer_OD']]
    

    # -------------------------------------------------------------------------------------------#
    # Return Final Dataframe
    # -------------------------------------------------------------------------------------------#
    if (pa_od=='od'):
        return df_brdsum_od
    else:
        return df_ridsum_pa

