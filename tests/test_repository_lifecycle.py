import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from persistence.repository import SQLiteRepository

def test_repository_closes_and_health_checks_analytics(tmp_path):
    path = tmp_path / "lifecycle.db"
    repo = SQLiteRepository(str(path))
    repo.init_schema()
    assert repo.health_check() is True
    repo.close()
    assert repo._conn is None

if __name__ == "__main__":
    import tempfile
    with tempfile.TemporaryDirectory() as d:
        repo = SQLiteRepository(str(Path(d) / "lifecycle.db"))
        repo.init_schema()
        assert repo.health_check() is True
        repo.close()
    print("REPOSITORY LIFECYCLE AUDIT: 1 PASS")
