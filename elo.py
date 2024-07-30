import pandas as pd
import requests
from datetime import date
from io import StringIO
from const import CLUBS

# Fetch latest one-day ELO rankings:
today = date.today()
#today = "2024-07-11"
r = requests.get(f'http://api.clubelo.com/{today}')
data = StringIO(r.text)
df_elo = pd.read_csv(data, sep=",")

class Club:

    def __init__(self, name):
        self.name = name
        if self.name in CLUBS:
            self.name_elo = CLUBS.get(self.name)
        else:
            self.name_elo = self.name
        self.elo = df_elo.loc[df_elo['Club'] == self.name_elo]["Elo"].values[0]
        self.tilt = 1  # Should have 50 games in it..
        
class Match:

    def __init__(self, home, away, home_goals, away_goals, home_advantage = 100):
        self.hfa = home_advantage
        self.home = Club(home)
        self.away = Club(away)
        self.margin = abs(home_goals - away_goals)
        if home_goals == away_goals:
            self.result = "draw"
        elif home_goals > away_goals:
            self.result = "home"
        else:
            self.result = "away"
        print(f"The {self.home.name} vs {self.away.name} game has been initialised.")
        
        self.dr = abs(self.home.elo + self.hfa - self.away.elo)
        
        print(f"The ELO of home team, {self.home.name}, before match is: {round(self.home.elo, 1)}")
        print(f"The ELO of away team, {self.away.name}, before match is: {round(self.away.elo, 1)}")
        print(f"The ELO difference is: {round(self.dr, 1)}")

        self.elo()
        self.expected_elo_exchange()

        print(f"The Calculated elo is: {round(self.elo, 2)}")
        return print(f"Expected ELO exchange points for a {self.home.name} win: {self.expected_elo_exchange}")


    def elo(self):
        '''
        The ELO equation
        from http://clubelo.com/System
        '''
        self.elo = 1 / (10 ** (-self.dr / 400) + 1)


    def expected_elo_exchange(self, k=20):
        '''
        Updates the elo after a game
        Points exchange (from http://clubelo.com/System)
        result: home, draw or away
        result: 1 for win, 0.5 for draw, 0 for loss
        '''
        if self.result == "draw":
            R = .5
        elif self.result == "home":
            R = 1
        elif self.result == "away":
            R = 0

        self.expected_elo_exchange = (R - self.elo) * k

        
    

    def elo_exchange_margin(self, p_margin):
        '''
        Weighting goal difference
        p_margin: likelyhood for a specific margin
        p_1X2: the likelyhood to win (or lose) by any margin.
        '''
        elo_1goal = self.expected_elo_exchange / sum( margin**(1/2) * p_margin / p_1X2)
        
        self.elo_points_margin = elo_1goal * margin**(1/2)

        return print(f"ELO exchange points for home team due to margin: {self.elo_points_margin}")


    def update_tilt(self, exp_game_total_goals, game_total_goals):
        '''
        Updates tilt after a game
        Tilt is designed to be a measure of offensiveness
        from http://clubelo.com/System
        '''
        self.home.tilt = 0.98 * self.home.tilt + 0.02 * game_total_goals / self.away.tilt / exp_game_total_goals
        self.away.tilt = 0.98 * self.away.tilt + 0.02 * game_total_goals / self.home.tilt / exp_game_total_goals
        return print(f"The tilts have been updated, new home team tilt: {self.home.tilt}, new away team tilt: {self.away.tilt}")
    
class Fixtures:

    def __init__(self):
        r = requests.get(f'http://api.clubelo.com/Fixtures')
        data = StringIO(r.text)
        self.data = pd.read_csv(data, sep=",")
    
        