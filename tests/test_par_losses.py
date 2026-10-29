"""Auswahl der nachzuspielenden Spiele fuer die Niederlagen-Analyse (scripts.par_losses)."""
import pandas as pd

from scripts.par_losses import select_games


def test_select_games_filters_opponent_and_result():
    df = pd.DataFrame([
        dict(seed=800000, side="player_0", opponent="sol92_sq", result=0.0),
        dict(seed=800000, side="player_1", opponent="sol92_sq", result=1.0),
        dict(seed=800001, side="player_0", opponent="solution92", result=0.0),
        dict(seed=800002, side="player_1", opponent="self:x/agent_p0.pth", result=0.0),
    ])
    assert select_games(df, "sol92_sq", "lost") == [(800000, "player_0", "sol92_sq")]
    assert select_games(df, "sol92_sq", "won") == [(800000, "player_1", "sol92_sq")]
    assert len(select_games(df, None, "lost")) == 3
    assert select_games(df, None, "all")[-1] == (800002, "player_1", "self:x/agent_p0.pth")
