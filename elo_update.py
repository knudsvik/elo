import pandas as pd
from elo import Match, set_tilts


def update_elo_with_fixtures(elo_df, fixtures_df, tilts=None):
    """
    Update ELO ratings based on played fixtures after the last ELO update for each club.
    Skips matches where either club is missing from the ELO data.
    Returns a new DataFrame with updated ELOs and dates.
    """
    
    elo_df = elo_df.copy()
    if tilts is not None:
        set_tilts(tilts)
    club_elo = {row['Club']: {'Elo': row['Elo'], 'EloDate': row['EloDate']} for _, row in elo_df.iterrows()}
    played = fixtures_df[
        fixtures_df['status'].isin(['FT', 'PEN'])
    ].sort_values('date')
    updated_teams = set()
    for _, row in played.iterrows():
        home, away = row['home'], row['away']
        if home not in club_elo or away not in club_elo:
            continue
        date = pd.to_datetime(row['date']).tz_localize(None)
        home_elo_date = pd.to_datetime(club_elo[home]['EloDate']).tz_localize(None)
        away_elo_date = pd.to_datetime(club_elo[away]['EloDate']).tz_localize(None)
        if date > home_elo_date or date > away_elo_date:
            match = Match(
                home=home,
                away=away,
                home_goals=row['home_goals'],
                away_goals=row['away_goals'],
                noise=False
            )
            match.home.elo = club_elo[home]['Elo']
            match.away.elo = club_elo[away]['Elo']
            match.set_result_from_goals()
            match.apply_elo_exchange()
            club_elo[home]['Elo'] = match.home.elo
            club_elo[home]['EloDate'] = date
            club_elo[away]['Elo'] = match.away.elo
            club_elo[away]['EloDate'] = date
            updated_teams.add(home)
            updated_teams.add(away)
    print(f"{len(updated_teams)} teams had their ELO updated.")
    updated_elo = pd.DataFrame([
        {'Club': club, 'Elo': data['Elo'], 'EloDate': data['EloDate']}
        for club, data in club_elo.items()
    ])
    return updated_elo
