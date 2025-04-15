import requests
from bs4 import BeautifulSoup
import pandas as pd

url = "https://www.fotball.no/fotballdata/turnering/terminliste/?fiksId=199603"
headers = {
    "User-Agent": "Mozilla/5.0"
}

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
            "round": round,
            "date": date,
            "time": time,
            "home": home,
            "result": result,
            "away": away,
            "arena": arena,
            "match number": match_no
        })

# Convert to DataFrame
fixtures = pd.DataFrame(data)

goals = fixtures['result'].str.split('-', n=1, expand=True).apply(lambda col: col.str.strip())

home_goals = pd.to_numeric(goals[0], errors='coerce')
away_goals = pd.to_numeric(goals[1], errors='coerce')

# Fill NaN with empty string, otherwise convert to int then to string
fixtures['home_goals'] = home_goals
fixtures['away_goals'] = away_goals