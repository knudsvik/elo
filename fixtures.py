import os
from collections import defaultdict

import pandas as pd
import requests
from dotenv import load_dotenv

from const import CLUBS, SEASONS


def get_fixtures(seasons=SEASONS, cache_file="fixtures.parquet", force_refresh=False):
    
    """
    Fetch fixtures for the specified seasons from the API.
    Returns a DataFrame with fixture data.
    """

    if not force_refresh and os.path.exists(cache_file):
        print(f"Loading fixtures from cache: {cache_file}")
        return pd.read_parquet(cache_file)
    
    print("Fetching the fixtures from api-football")

    load_dotenv()
    api_key = os.getenv("RAPID_API_KEY")
    url = "https://api-football-v1.p.rapidapi.com/v3/fixtures"

    headers = {
        "X-RapidAPI-Key": api_key,
        "X-RapidAPI-Host": "api-football-v1.p.rapidapi.com",
    }

    fixtures = pd.DataFrame()

    for season in seasons:
        querystring = {"league": "103", "season": season}  # Eliteserien

        response = requests.get(url, headers=headers, params=querystring)
        data = response.json()

        matches = []

        for match in data["response"]:
            date = match["fixture"]["date"]
            id = match["fixture"]["id"]
            status = match["fixture"]["status"]["short"]
            venue = match["fixture"]["venue"]["name"]
            home_goals = match["goals"]["home"]
            away_goals = match["goals"]["away"]
            home = match["teams"]["home"]["name"]
            away = match["teams"]["away"]["name"]

            matches.append(
                {
                    "id": id,
                    "season": season,
                    "date": date,
                    "home": home,
                    "home_goals": home_goals,
                    "away": away,
                    "away_goals": away_goals,
                    "venue": venue,
                    "status": status,
                }
            )

        # Add to DataFrame
        fixtures = pd.concat([fixtures, pd.DataFrame(matches)], ignore_index=True)

    # Clean the data
    int_columns = ["id", "season", "home_goals", "away_goals"]
    fixtures[int_columns] = fixtures[int_columns].astype("Int64")
    fixtures["date"] = pd.to_datetime(fixtures["date"], errors="coerce")

    # Fix club names
    variant_to_standard = {
        variant: standard for standard, variants in CLUBS.items() for variant in variants
    }
    fixtures["home"] = fixtures["home"].apply(lambda x: variant_to_standard.get(x, x))
    fixtures["away"] = fixtures["away"].apply(lambda x: variant_to_standard.get(x, x))

    fixtures.to_parquet(cache_file)
    print(f"Fixtures fetched successfully and cached to {cache_file}.")

    return fixtures


def compute_initial_tilts(fixtures_df, base_goals=False, max_matches=50):

    # Mean goals
    if not base_goals:
        base_goals = fixtures_df.home_goals.mean() + fixtures_df.away_goals.mean()

    team_matches = defaultdict(list)

    # 1. Build up a history per team from played games
    played = fixtures_df.dropna(subset=["home_goals", "away_goals"])

    for _, row in played.iterrows():
        home = row["home"]
        away = row["away"]
        total_goals = row["home_goals"] + row["away_goals"]
        date = row["date"]

        # Append match info to both home and away teams
        team_matches[home].append((away, total_goals, "home", date))
        team_matches[away].append((home, total_goals, "away", date))

    # 2. Estimate tilt per team
    team_tilt_raw = {}
    for team, matches in team_matches.items():
        # Sort by date (latest first), then take last max_matches
        matches = sorted(matches, key=lambda x: x[3], reverse=True)[:max_matches]

        tilt_product_sum = 0
        count = 0

        for opponent, total_goals, loc, _ in matches:
            if opponent not in team_matches:
                continue  # skip incomplete data

            # crude approx: assume opponent has tilt = 1 during initialization
            opp_tilt = 1

            if loc == "home":
                # total_goals = team_tilt * opp_tilt * base_goals
                tilt_estimate = total_goals / (opp_tilt * base_goals)
            else:  # away
                tilt_estimate = total_goals / (opp_tilt * base_goals)

            tilt_product_sum += tilt_estimate
            count += 1

        if count > 0:
            team_tilt_raw[team] = max(0.5, min(2.0, tilt_product_sum / count))
        else:
            team_tilt_raw[team] = 1.0  # fallback

    return team_tilt_raw
