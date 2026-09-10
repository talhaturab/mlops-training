from app.store import StatsStore


def test_leaderboard_sorted_and_capped_at_ten():
    store = StatsStore()
    for i in range(12):
        store.record_income(f"p{i}", float(i * 1000))
    snap = store.snapshot()
    assert len(snap.leaderboard) == 10
    assert snap.leaderboard[0].name == "p11"
    assert snap.leaderboard[-1].name == "p2"


def test_fortunes_counter():
    store = StatsStore()
    store.record_fortune()
    store.record_fortune()
    assert store.snapshot().fortunes_told == 2


def test_make_store_defaults_to_memory():
    from app.store import make_store

    assert isinstance(make_store(None), StatsStore)
