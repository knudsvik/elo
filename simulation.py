from collections import defaultdict
from datetime import datetime, timezone

import numpy as np
import pandas as pd
from tqdm.notebook import tqdm

from const import HFA
from elo import Match
from table import build_league_table

tqdm.pandas()

position_counts = defaultdict(lambda: defaultdict(int))

def simulate_match(home, away, n=1000, hfa=HFA, simulate_goals=True):
    results = {"home": 0, "draw": 0, "away": 0}
    scores = defaultdict(int)

    for _ in range(n):
        match = Match(home, away, home_advantage=hfa)
        if simulate_goals:
            match.simulate_goals()
            result = (match.home_goals, match.away_goals)
            scores[result] += 1
        else:
            match.simulate_result()
        results[match.result] += 1

    print(f"\nSimulated {n} matches between {home} and {away}:")
    for result, count in results.items():
        percentage = round(100 * count / n, 1)
        print(f"{result.capitalize():<5}: {count} ({percentage}%)")

    if simulate_goals:
        # Get top 10 most common results
        top_scores = sorted(scores.items(), key=lambda x: (-x[1], x[0]))[:10]

        # Print the top 10 with percentages
        for score, count in top_scores:
            percentage = (count / n) * 100
            print(f"{score[0]} - {score[1]}: {percentage:.2f}%")

    return results

def simulate_season(fixtures_df, n_simulations=1000, cutoff_date=None, season=2025, simulate_goals=True, elo_updates=True):
    if cutoff_date is None:
        cutoff_date = datetime.max.replace(tzinfo=timezone.utc)

    fixtures_df = fixtures_df.loc[fixtures_df.season == season]

    # Split played and unplayed fixtures
    played = fixtures_df[~fixtures_df["home_goals"].isna()]
    to_simulate = fixtures_df[
        (fixtures_df["home_goals"].isna()) &
        (fixtures_df["date"].notna()) &
        (fixtures_df["date"] <= cutoff_date)
    ]

    stats_tracker = defaultdict(lambda: {
        "Wins": [],
        "Draws": [],
        "Losses": [],
        "GF": [],
        "GA": [],
        "Points": [],
    })

    position_counts = defaultdict(lambda: defaultdict(int))

    print(f'{len(played)} games have been played. Starting {n_simulations} simulations of {len(to_simulate)} games.')

    for _ in tqdm(range(n_simulations), desc="Simulating seasons", leave=True):
        simulated_fixtures = played.copy()

        for _, row in to_simulate.iterrows():
            match = Match(row["home"], row["away"])
            if simulate_goals:
                match.simulate_goals()
                home_goals = match.home_goals
                away_goals = match.away_goals
            else:
                match.simulate_result()
                if match.result == "home":
                    home_goals, away_goals = 2, 1
                elif match.result == "away":
                    home_goals, away_goals = 1, 2
                else:
                    home_goals = away_goals = 1
            
            if elo_updates:
                match.apply_elo_exchange()

            sim_row = row.copy()
            sim_row["home_goals"] = home_goals
            sim_row["away_goals"] = away_goals

            simulated_fixtures = pd.concat([simulated_fixtures, sim_row.to_frame().T], ignore_index=True)

        # Build table
        league_table = build_league_table(simulated_fixtures)

        for _, row in league_table.iterrows():
            team = row["Team"]
            stats_tracker[team]["Wins"].append(row["Wins"])
            stats_tracker[team]["Draws"].append(row["Draws"])
            stats_tracker[team]["Losses"].append(row["Losses"])
            stats_tracker[team]["GF"].append(row["GF"])
            stats_tracker[team]["GA"].append(row["GA"])
            stats_tracker[team]["Points"].append(row["Points"])

            position = row["Position"]
            position_counts[team][position] += 1

    return stats_tracker, position_counts

def build_season_summary(stats_tracker, position_counts, use_median=False):
    
    def summarize(values):
        if use_median:
            return int(np.median(values))
        else:
            return round(np.mean(values), 2)

    final_stats = []
    for team, stats in stats_tracker.items():
        total_games_per_sim = [w + d + l for w, d, l in zip(stats["Wins"], stats["Draws"], stats["Losses"])]
        final_stats.append({
            "Team": team,
            "Games": summarize(total_games_per_sim),
            "Exp Wins": summarize(stats["Wins"]),
            "Exp Draws": summarize(stats["Draws"]),
            "Exp Losses": summarize(stats["Losses"]),
            "Exp GF": summarize(stats["GF"]),
            "Exp GA": summarize(stats["GA"]),
            "Exp Points": summarize(stats["Points"]),
        })

    df_summary = pd.DataFrame(final_stats)
    df_summary = df_summary.sort_values("Exp Points", ascending=False).reset_index(drop=True)
    df_summary.insert(0, "Position", range(1, len(df_summary) + 1))
    df_summary = df_summary.sort_values(
        ["Exp Points", "Exp GF", "Exp GA"],
        ascending=[False, False, True]
        ).reset_index(drop=True)
    
    df_summary["Goals"] = df_summary["Exp GF"].astype(str) + "-" + df_summary["Exp GA"].astype(str)
    df_summary = df_summary.drop(columns=["Exp GF", "Exp GA"])

    df_summary = df_summary[["Position", "Team", "Games", "Exp Wins", "Exp Draws", "Exp Losses", "Goals", "Exp Points"]]
    if use_median:
        df_summary.columns = ["Position", "Team", "Games", "Wins", "Draws", "Losses", "Goals", "Points"]

    # Position probabilities (always expected %)
    position_df = pd.DataFrame(position_counts).T.fillna(0)
    position_df = position_df.apply(lambda row: (row / row.sum()) * 100, axis=1)
    position_df = position_df.round(2)

    # Sort columns numerically
    position_df = position_df.reindex(sorted(position_df.columns, key=lambda x: int(x)), axis=1)

    # Align teams
    position_df = position_df.loc[df_summary["Team"]]

    return df_summary, position_df
