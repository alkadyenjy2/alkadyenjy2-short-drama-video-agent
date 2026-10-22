import os
import unittest
from unittest.mock import patch

from persistence.repository import SQLiteRepository, get_repository


class RepositoryFactoryTests(unittest.TestCase):
    def test_defaults_to_sqlite_without_database_url(self):
        with patch.dict(os.environ, {}, clear=True):
            repo = get_repository()
        self.assertIsInstance(repo, SQLiteRepository)
        repo.close()

    def test_uses_postgres_when_database_url_is_configured(self):
        database_url = "postgresql://test:secret@localhost/testdb"
        with patch.dict(os.environ, {"DATABASE_URL": database_url}, clear=True):
            with patch("persistence.postgres_repository.PostgresRepository") as postgres:
                result = get_repository()
        postgres.assert_called_once_with(database_url=database_url)
        self.assertIs(result, postgres.return_value)

    def test_explicit_sqlite_path_overrides_database_url(self):
        with patch.dict(os.environ, {"DATABASE_URL": "postgresql://test:secret@localhost/testdb"}, clear=True):
            with patch("persistence.postgres_repository.PostgresRepository") as postgres:
                result = get_repository(db_path=":memory:")
        postgres.assert_not_called()
        self.assertIsInstance(result, SQLiteRepository)
        result.close()


if __name__ == "__main__":
    unittest.main()
