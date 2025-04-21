import requests
from bs4 import BeautifulSoup
import pandas as pd

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

home_goals = pd.to_numeric(goals[0], errors='coerce')
away_goals = pd.to_numeric(goals[1], errors='coerce')

# Fill NaN with empty string, otherwise convert to int then to string
fixtures['home_goals'] = home_goals
fixtures['away_goals'] = away_goals

int_columns = ["round", "match number"]
fixtures[int_columns] = fixtures[int_columns].astype(int)

fixtures["date"] = pd.to_datetime(fixtures["date"], format="%d.%m.%Y", errors="coerce")