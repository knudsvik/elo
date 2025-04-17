import pandas as pd
import random
import requests
from datetime import date
from io import StringIO
from const import CLUBS, HFA

DEBUG = False

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

    def __init__(self, home, away, home_goals=None, away_goals=None, home_advantage = HFA):
        self.hfa = home_advantage
        self.home = Club(home)
        self.away = Club(away)

        self.home_goals = home_goals
        self.away_goals = away_goals

        self.dr = self.home.elo + self.hfa - self.away.elo
        self.elo = 1 / (10 ** (-self.dr / 400) + 1)

        if DEBUG:
            print(f"The {self.home.name} vs {self.away.name} game has been initialised.")
            print(f"The ELO of home team, {self.home.name}, before match is: {round(self.home.elo, 1)}")
            print(f"The ELO of away team, {self.away.name}, before match is: {round(self.away.elo, 1)}")
            print(f"The ELO difference is: {round(self.dr, 1)}")
            print(f"The Calculated expected score for home team is: {round(self.elo, 2)}")

        # Only do result logic if real goals were provided
        if self.home_goals is not None and self.away_goals is not None:
            self.set_result_from_goals()
            self.expected_elo_exchange()
            if DEBUG:
                print(f"Expected ELO exchange points for a {self.home.name} win: {self.expected_elo_exchange}")

    def set_result_from_goals(self):
        if self.home_goals == self.away_goals:
            self.result = "draw"
        elif self.home_goals > self.away_goals:
            self.result = "home"
        else:
            self.result = "away"

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


    def simulate_result(self):

        # Step 1: Use already-calculated expected score
        expected_home_score = self.elo  # This is already calculated in __init__
        delta_elo = self.dr

        # Step 2: Estimate draw chance (ClubElo-inspired)
        p_draw = draw_probability(delta_elo)
        p_draw = max(0.10, p_draw)

        # Step 3: Split rest between home/away
        p_home = expected_home_score - p_draw / 2
        p_away = 1 - p_home - p_draw

        # Safety checks
        p_home = max(0, min(1, p_home))
        p_away = max(0, min(1, p_away))

        # Step 4: Simulate result
        roll = random.random()
        if roll < p_home:
            self.result = "home"
        elif roll < p_home + p_draw:
            self.result = "draw"
        else:
            self.result = "away"

        if DEBUG:
            print(f"Simulated match result: {self.home.name} vs {self.away.name}")
            print(f"Probabilities: Home {round(p_home*100)}% | Draw {round(p_draw*100)}% | Away {round(p_away*100)}%")
            print(f"Random draw: {round(roll, 3)} → Result: {self.result.capitalize()}")

    ## NOT IN USE YET
    def elo_exchange_margin(self, p_margin):
        '''
        Weighting goal difference
        p_margin: likelyhood for a specific margin
        p_1X2: the likelyhood to win (or lose) by any margin.
        '''
        elo_1goal = self.expected_elo_exchange / sum( margin**(1/2) * p_margin / p_1X2)
        
        self.elo_points_margin = elo_1goal * margin**(1/2)

        return print(f"ELO exchange points for home team due to margin: {self.elo_points_margin}")

    ## NOT IN USE YET
    def update_tilt(self, exp_game_total_goals, game_total_goals):
        '''
        Updates tilt after a game
        Tilt is designed to be a measure of offensiveness
        from http://clubelo.com/System
        '''
        self.home.tilt = 0.98 * self.home.tilt + 0.02 * game_total_goals / self.away.tilt / exp_game_total_goals
        self.away.tilt = 0.98 * self.away.tilt + 0.02 * game_total_goals / self.home.tilt / exp_game_total_goals
        return print(f"The tilts have been updated, new home team tilt: {self.home.tilt}, new away team tilt: {self.away.tilt}")
    
        
def simulate(home, away, n=1000, hfa=HFA):
    results = {"home": 0, "draw": 0, "away": 0}

    for _ in range(n):
        match = Match(home, away, home_advantage=hfa)
        match.simulate_result()
        results[match.result] += 1

    print(f"\nSimulated {n} matches between {home} and {away}:")
    for result, count in results.items():
        percentage = round(100 * count / n, 1)
        print(f"{result.capitalize():<5}: {count} ({percentage}%)")

    return results

def draw_probability(delta_elo):
    # Higher draws near 0, lower draws when one team is much stronger
    p_draw = 0.29 - 0.0006 * abs(delta_elo)
    return max(0.12, min(p_draw, 0.35))