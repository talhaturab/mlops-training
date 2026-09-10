from app.config import Settings


def test_no_database_by_default():
    assert Settings(_env_file=None).effective_database_url is None


def test_database_url_wins_over_parts():
    s = Settings(_env_file=None, database_url="postgresql://x", db_host="h", db_password="p")
    assert s.effective_database_url == "postgresql://x"


def test_database_url_is_built_from_parts():
    s = Settings(_env_file=None, db_host="db.internal", db_password="secret")
    assert s.effective_database_url == "postgresql://oracle:secret@db.internal:5432/oracle"


def test_parts_without_password_mean_no_database():
    assert Settings(_env_file=None, db_host="db.internal").effective_database_url is None
