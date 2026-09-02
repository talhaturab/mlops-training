"""In-memory counters. Lost on restart, shared across every request in this process.

This is deliberate for Day 1. The persistence day replaces it with a database.
"""

from app.schemas import LeaderboardEntry, StatsResponse

LEADERBOARD_SIZE = 10


class StatsStore:
    def __init__(self) -> None:
        self.fortunes_told = 0
        self._leaderboard: list[LeaderboardEntry] = []

    def record_fortune(self) -> None:
        self.fortunes_told += 1

    def record_income(self, name: str, income: float) -> None:
        self._leaderboard.append(LeaderboardEntry(name=name, predicted_income_usd=round(income, 2)))
        self._leaderboard.sort(key=lambda e: e.predicted_income_usd, reverse=True)
        del self._leaderboard[LEADERBOARD_SIZE:]

    def snapshot(self) -> StatsResponse:
        return StatsResponse(fortunes_told=self.fortunes_told, leaderboard=list(self._leaderboard))
