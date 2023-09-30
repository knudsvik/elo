import pandas as pd
import requests
from datetime import date
from io import StringIO
from const import CLUBS

# Fetch latest one-day ELO rankings:
today = date.today()
today = "2023-09-12"
r = requests.get(f'http://api.clubelo.com/{today}')
data = StringIO(r.text)
df_elo = pd.read_csv(data, sep=",")

class Club:

    def __init__(self, name):
        self.name = name
        self.elo = df_elo.loc[df_elo['Club'] == CLUBS.get(self.name)]["Elo"].values[0]
        self.tilt = 1  # Should have 50 games in it..
        
class Match:

    def __init__(self, home, away):
        self.home = Club(home)
        self.away = Club(away)
        print(f"The {self.home.name} vs {self.away.name} game has been initialised.")
        
        self.dr = abs(self.home.elo - self.away.elo)
        print(f"The ELO difference is: {round(self.dr, 1)}")

        self.elo()
        print(f"The Calculated elo is: {round(self.elo, 2)}")


    def elo(self):
        '''
        The ELO equation
        from http://clubelo.com/System
        '''
        self.elo = 1 / (10 ** (-self.dr / 400) + 1)


    def elo_exchange_result(self, result: str, k=20):
        '''
        Updates the elo after a game
        Points exchange (from http://clubelo.com/System)
        result: home, draw or away
        result: 1 for win, 0.5 for draw, 0 for loss
        '''
        if result == "draw":
            R = .5
        elif result == "home":
            R = 1
        elif result == "away":
            R = 0

        self.elo_points_result = (R - self.elo) * k

        return print(f"ELO exchange points for home team due to result: {self.elo_points_result}")
    

    def elo_exchange_margin(self, p_margin):
        '''
        Weighting goal difference
        p_margin: likelyhood for a specific margin
        p_1X2: the likelyhood to win (or lose) by any margin.
        '''
        elo_1goal = self.elo_points_result / sum( margin**(1/2) * p_margin / p_1X2)
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