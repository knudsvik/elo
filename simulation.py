import copy
from table import build_league_table
from elo import Match
from collections import defaultdict
import pandas as pd
from datetime import datetime
from tqdm.notebook import tqdm

tqdm.pandas()

position_counts = defaultdict(lambda: defaultdict(int))

def simulate_season(fixtures_df, n_simulations=1000, cutoff_date=None, season=2025):
    if cutoff_date is None:
        cutoff_date = datetime.max

    fixtures_df = fixtures_df.loc[fixtures_df.season == season]

    # Split played and unplayed fixtures
    played = fixtures_df[~fixtures_df["home_goals"].isna()]
    upcoming = fixtures_df[
        (fixtures_df["home_goals"].isna()) &
        (fixtures_df["date"].notna()) &
        (fixtures_df["date"] <= cutoff_date)
    ]

    team_points_tracker = defaultdict(list)

    print(f'{len(played)} games have been played. Starting {n_simulations} simulations of {len(upcoming)} games.')

    for sim in tqdm(range(n_simulations), desc="Simulating seasons", leave=True):
        simulated_fixtures = played.copy()

        for _, row in upcoming.iterrows():
            match = Match(row["home"], row["away"])
            match.simulate_result()

            if match.result == "home":
                home_goals, away_goals = 2, 1
            elif match.result == "away":
                home_goals, away_goals = 1, 2
            else:
                home_goals = away_goals = 1

            sim_row = row.copy()
            sim_row["home_goals"] = home_goals
            sim_row["away_goals"] = away_goals

            simulated_fixtures = pd.concat([simulated_fixtures, sim_row.to_frame().T], ignore_index=True)

        # Build table
        league_table = build_league_table(simulated_fixtures)

        for _, row in league_table.iterrows():
            team_points_tracker[row["Team"]].append(row["Points"])
            team = row["Team"]
            pos = row["Position"]
            position_counts[team][pos] += 1

    # Compute expected points per team
    expected_points = {
        team: sum(points_list) / len(points_list)
        for team, points_list in team_points_tracker.items()
    }

    # Format output
    expected_points_df = pd.DataFrame.from_dict(expected_points, orient='index', columns=['Expected Points'])
    expected_points_df = expected_points_df.sort_values("Expected Points", ascending=False)
    expected_points_df["Expected Points"] = expected_points_df["Expected Points"].round(2)
    expected_points_df = expected_points_df.reset_index().rename(columns={"index": "Team"})

    position_df = pd.DataFrame(position_counts).T.fillna(0)
    position_df = position_df.apply(lambda row: (row / row.sum()) * 100, axis=1)

    expected_points_df = expected_points_df.set_index("Team")
    position_df = position_df.loc[expected_points_df.index]

    # Sort the columns numerically, and then by 1st place
    #position_df = position_df[sorted(position_df.columns, key=lambda x: int(x))]
    #position_df = position_df.sort_values(by=1, ascending=False)
    #position_df = position_df.round(2)

    return expected_points_df, position_df
