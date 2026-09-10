"""Where the counters and the leaderboard live.

Day 1: in memory, lost on restart, one copy per process.
Day 4: in Postgres when a database URL is configured, so every copy of the app shares
the same numbers and they survive restarts and deploys.
"""

import psycopg

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


SCHEMA = """
CREATE TABLE IF NOT EXISTS counters (
    name  TEXT PRIMARY KEY,
    value BIGINT NOT NULL DEFAULT 0
);
CREATE TABLE IF NOT EXISTS leaderboard (
    id                   BIGSERIAL PRIMARY KEY,
    name                 TEXT NOT NULL,
    predicted_income_usd NUMERIC(12, 2) NOT NULL,
    created_at           TIMESTAMPTZ NOT NULL DEFAULT now()
);
INSERT INTO counters (name, value) VALUES ('fortunes_told', 0) ON CONFLICT DO NOTHING;
"""


class PostgresStatsStore:
    """Same three methods as StatsStore, backed by two tables.

    One short connection per call. Simple, and plenty for a class-sized amount of traffic.
    """

    def __init__(self, url: str) -> None:
        self._url = url
        with self._connect() as conn:
            conn.execute(SCHEMA)

    def _connect(self) -> psycopg.Connection:
        return psycopg.connect(self._url, autocommit=True, connect_timeout=5)

    def record_fortune(self) -> None:
        with self._connect() as conn:
            conn.execute("UPDATE counters SET value = value + 1 WHERE name = 'fortunes_told'")

    def record_income(self, name: str, income: float) -> None:
        with self._connect() as conn:
            conn.execute(
                "INSERT INTO leaderboard (name, predicted_income_usd) VALUES (%s, %s)",
                (name, round(income, 2)),
            )

    def snapshot(self) -> StatsResponse:
        with self._connect() as conn:
            told = conn.execute(
                "SELECT value FROM counters WHERE name = 'fortunes_told'"
            ).fetchone()
            rows = conn.execute(
                "SELECT name, predicted_income_usd FROM leaderboard "
                "ORDER BY predicted_income_usd DESC, created_at ASC LIMIT %s",
                (LEADERBOARD_SIZE,),
            ).fetchall()
        return StatsResponse(
            fortunes_told=int(told[0]) if told else 0,
            leaderboard=[
                LeaderboardEntry(name=name, predicted_income_usd=float(income))
                for name, income in rows
            ],
        )


def make_store(database_url: str | None) -> StatsStore | PostgresStatsStore:
    return PostgresStatsStore(database_url) if database_url else StatsStore()
