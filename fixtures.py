import requests
from bs4 import BeautifulSoup
import pandas as pd
from collections import defaultdict

headers = {
    "User-Agent": "Mozilla/5.0"
    }
base_url = "https://www.fotball.no/fotballdata/turnering/terminliste/?fiksId="
fixtures = pd.DataFrame()

tournaments = {2025: '199603',
               2024: '192924',
               2023: '186850',
               2022: '181484'
               }

for season in tournaments:

    url = base_url + tournaments[season]
    response = requests.get(url, headers=headers)
    soup = BeautifulSoup(response.text, "html.parser")

    # Look for table rows (tr) in the fixture list
    rows = soup.find_all("tr")

    data = []
    for row in rows:
        cols = row.find_all("td")
        if len(cols) >= 5:
            round = cols[0].text.strip()
            date = cols[1].text.strip()
            day = cols[2].text.strip()
            time = cols[3].text.strip()
            home = cols[4].text.strip()
            result = cols[5].text.strip()
            away = cols[6].text.strip()
            arena = cols[7].text.strip()
            match_no = cols[8].text.strip()

            data.append({
                "season": season,
                "round": round,
                "date": date,
                "time": time,
                "home": home,
                "result": result,
                "away": away,
                "arena": arena,
                "match number": match_no
            })

    # Add to DataFrame
    fixtures = pd.concat([fixtures, pd.DataFrame(data)], ignore_index=True)

goals = fixtures['result'].str.split('-', n=1, expand=True).apply(lambda col: col.str.strip())

home_goals = pd.to_numeric(goals[0], errors='coerce').astype("Int64")
away_goals = pd.to_numeric(goals[1], errors='coerce').astype("Int64")

# Fill NaN with empty string, otherwise convert to int then to string
fixtures['home_goals'] = home_goals
fixtures['away_goals'] = away_goals

int_columns = ["round", "match number"]
fixtures[int_columns] = fixtures[int_columns].astype(int)

fixtures["date"] = pd.to_datetime(fixtures["date"], format="%d.%m.%Y", errors="coerce")




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

tilts = compute_initial_tilts(fixtures)
