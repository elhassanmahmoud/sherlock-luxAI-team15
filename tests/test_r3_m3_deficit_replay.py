from scripts.r3_m3_deficit_replay import trigger, summarize


def test_public_score_is_checked_on_the_acting_seat_before_even_the_last_action():
    assert not trigger(49, [1, 1], [5, 6], 0)
    assert not trigger(50, [1, 0], [5, 6], 0)
    assert not trigger(50, [2, 0], [5, 6], 0)
    assert not trigger(50, [1, 1], [5, 5], 1)
    assert not trigger(50, [1, 1], [5, 6], 1)
    assert trigger(50, [1, 1], [5, 6], 0)
    assert trigger(100, [1, 1], [6, 5], 1)
    assert not trigger(101, [1, 1], [5, 6], 0)


def test_exposure_at_each_loss_trigger_counts_previous_and_simultaneous_winners():
    def row(won, step):
        return {'original_game_win':won, 'trigger':{'match_step':step} if step is not None else None}
    result = summarize([row(False,50),row(False,70),row(False,None),
                        row(True,50),row(True,60),row(True,99),row(True,None)])
    assert result['old_losses'] == {'total':3,'triggered':2}
    assert result['protected_wins'] == {'total':4,'triggered':3}
    assert result['cumulative_at_loss_triggers'] == [
        {'match_step':50,'triggered_losses':1,'triggered_protected_wins':1},
        {'match_step':70,'triggered_losses':2,'triggered_protected_wins':2}]
