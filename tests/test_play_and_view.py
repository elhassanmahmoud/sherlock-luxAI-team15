"""Demo-Werkzeug vom 22.10.2026: Replay als HTML mit dem offiziellen Viewer."""
import json

from scripts.play_and_view import match_sequence, match_wins, replay_html


def test_replay_html_embeds_replay_unchanged():
    replay = {"observations": [{"team_wins": [2, 1]}], "metadata": {"seed": 7}, "params": {}}
    html = replay_html(replay)
    start = html.index("window.episode = ") + len("window.episode = ")
    end = html.index(";\n    </script>", start)
    assert json.loads(html[start:end]) == replay
    assert 'src="https://s3vis.lux-ai.org/index.js"' in html


def test_match_wins_reads_both_sides():
    replay = {"observations": [{"team_wins": [0, 0]}, {"team_wins": [1, 2]}]}
    assert match_wins(replay, "player_0") == (1, 2)
    assert match_wins(replay, "player_1") == (2, 1)


def test_match_sequence_per_match_winner():
    wins = ([0, 0], [0, 0], [1, 0], [1, 0], [1, 1], [2, 1])
    replay = {"observations": [{"team_wins": w} for w in wins]}
    assert match_sequence(replay, "player_0") == [True, False, True]
    assert match_sequence(replay, "player_1") == [False, True, False]
