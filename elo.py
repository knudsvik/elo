import random

import numpy as np

from const import HFA, MEAN_GOALS
from fetch_elo import fetch_elo_data

DEBUG = False

df_elo = fetch_elo_data()


def set_tilts(tilts_dict):
    global tilts
    tilts = tilts_dict


class Club:

    def __init__(self, name, tilt_lookup=True):
        self.name = name
        self.elo = df_elo.loc[df_elo["Club"] == self.name]["Elo"].values[0]
        self.tilt = tilts.get(name, 1) if tilt_lookup else 1


class Match:

    def __init__(
        self,
        home,
        away,
        home_goals=None,
        away_goals=None,
        home_advantage=HFA,
        noise=True,
    ):
        self.hfa = home_advantage
        self.home = Club(home)
        self.away = Club(away)

        self.home_goals = home_goals
        self.away_goals = away_goals

        self.dr = self.home.elo + self.hfa - self.away.elo

        if noise:
            self.dr += np.random.normal(0, 15)  # ~15 ELO points

        self.elo = 1 / (10 ** (-self.dr / 400) + 1)

        if DEBUG:
            print(
                f"The {self.home.name} vs {self.away.name} game has been initialised."
            )
            print(
                f"The ELO of home team, {self.home.name}, before match is: {round(self.home.elo, 1)}"
            )
            print(
                f"The ELO of away team, {self.away.name}, before match is: {round(self.away.elo, 1)}"
            )
            print(f"The ELO difference is: {round(self.dr, 1)}")
            print(
                f"The Calculated expected score for home team is: {round(self.elo, 2)}"
            )

        # Only do result logic if real goals were provided
        if self.home_goals is not None and self.away_goals is not None:
            self.set_result_from_goals()
            self.expected_elo_exchange()
            if DEBUG:
                print(
                    f"Expected ELO exchange points for a {self.home.name} win: {self.expected_elo_exchange}"
                )

    def set_result_from_goals(self):
        if self.home_goals == self.away_goals:
            self.result = "draw"
        elif self.home_goals > self.away_goals:
            self.result = "home"
        else:
            self.result = "away"

    def expected_elo_exchange(self, k=20):
        """
        Updates the elo after a game
        Points exchange (from http://clubelo.com/System)
        result: home, draw or away
        result: 1 for win, 0.5 for draw, 0 for loss
        """
        if self.result == "draw":
            R = 0.5
        elif self.result == "home":
            R = 1
        elif self.result == "away":
            R = 0

        self.expected_elo_exchange = (R - self.elo) * k

    def apply_elo_exchange(self, k=20):
        if self.result == "draw":
            R = 0.5
        elif self.result == "home":
            R = 1.0
        else:
            R = 0.0

        # Calculate expected result again if not cached
        expected_home = self.elo
        exchange = (R - expected_home) * k

        self.home.elo += exchange
        self.away.elo -= exchange

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
            print(
                f"Probabilities: Home {round(p_home*100)}% | Draw {round(p_draw*100)}% | Away {round(p_away*100)}%"
            )
            print(f"Random draw: {round(roll, 3)} → Result: {self.result.capitalize()}")

    def simulate_goals(self, base_goals=MEAN_GOALS):
        """Simulate realistic scorelines using tilt logic"""
        # Step 1: Expected total goals
        exp_total_goals = self.home.tilt * self.away.tilt * base_goals

        # Step 2: Expected goal share (favoring the stronger team)
        home_share = self.elo  # already calculated: expected result for home team
        away_share = 1 - home_share

        exp_home_goals = exp_total_goals * home_share
        exp_away_goals = exp_total_goals * away_share

        # Step 3: Simulate actual goals using Poisson distribution
        self.home_goals = np.random.poisson(exp_home_goals)
        self.away_goals = np.random.poisson(exp_away_goals)

        self.set_result_from_goals()

        if DEBUG:
            print(
                f"Simulated score: {self.home.name} {self.home_goals} - {self.away_goals} {self.away.name}"
            )

    ## NOT IN USE YET
    def elo_exchange_margin(self, p_margin):
        """
        Weighting goal difference
        p_margin: likelyhood for a specific margin
        p_1X2: the likelyhood to win (or lose) by any margin.
        """
        elo_1goal = self.expected_elo_exchange / sum(
            margin ** (1 / 2) * p_margin / p_1X2
        )

        self.elo_points_margin = elo_1goal * margin ** (1 / 2)

        return print(
            f"ELO exchange points for home team due to margin: {self.elo_points_margin}"
        )

    ## NOT IN USE YET
    def update_tilt(self, exp_game_total_goals, game_total_goals):
        """
        Updates tilt after a game
        Tilt is designed to be a measure of offensiveness
        from http://clubelo.com/System
        """
        self.home.tilt = (
            0.98 * self.home.tilt
            + 0.02 * game_total_goals / self.away.tilt / exp_game_total_goals
        )
        self.away.tilt = (
            0.98 * self.away.tilt
            + 0.02 * game_total_goals / self.home.tilt / exp_game_total_goals
        )
        return print(
            f"The tilts have been updated, new home team tilt: {self.home.tilt}, new away team tilt: {self.away.tilt}"
        )


def draw_probability(delta_elo):
    # Higher draws near 0, lower draws when one team is much stronger
    p_draw = 0.29 - 0.0006 * abs(delta_elo)
    return max(0.12, min(p_draw, 0.35))
