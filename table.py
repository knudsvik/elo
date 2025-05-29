from collections import defaultdict

import pandas as pd


def build_league_table(results_df):

    # 1. Filter only completed matches
    results_df = results_df.dropna(subset=["home_goals", "away_goals"])

    table = defaultdict(
        lambda: {
            "Games": 0,
            "Wins": 0,
            "Draws": 0,
            "Losses": 0,
            "GF": 0,
            "GA": 0,
            "GD": 0,
            "Points": 0,
        }
    )

    for _, row in results_df.iterrows():
        home, away = row["home"], row["away"]
        hg, ag = row["home_goals"], row["away_goals"]

        # Update games played
        table[home]["Games"] += 1
        table[away]["Games"] += 1

        # Update goals
        table[home]["GF"] += hg
        table[home]["GA"] += ag
        table[home]["GD"] += hg - ag

        table[away]["GF"] += ag
        table[away]["GA"] += hg
        table[away]["GD"] += ag - hg

        # Update results
        if hg > ag:  # Home win
            table[home]["Wins"] += 1
            table[home]["Points"] += 3
            table[away]["Losses"] += 1
        elif hg < ag:  # Away win
            table[away]["Wins"] += 1
            table[away]["Points"] += 3
            table[home]["Losses"] += 1
        else:  # Draw
            table[home]["Draws"] += 1
            table[away]["Draws"] += 1
            table[home]["Points"] += 1
            table[away]["Points"] += 1

    # Convert to DataFrame
    df_table = pd.DataFrame.from_dict(table, orient="index")
    df_table.index.name = "Team"
    df_table = df_table.sort_values(
        ["Points", "GD", "GF"], ascending=False
    ).reset_index()
    df_table["Goals"] = df_table["GF"].astype(str) + "-" + df_table["GA"].astype(str)
    df_table.insert(0, "Position", range(1, len(df_table) + 1))

    int_columns = ["Games", "Wins", "Draws", "Losses", "GD", "Points"]
    df_table[int_columns] = df_table[int_columns].astype(int)

    df_table["GD"] = df_table["GD"].apply(lambda x: f"+{x}" if x > 0 else str(x))

    df_table = df_table[
        [
            "Position",
            "Team",
            "Games",
            "Wins",
            "Draws",
            "Losses",
            "Goals",
            "GD",
            "Points",
            "GF",
            "GA",
        ]
    ]

    return df_table
