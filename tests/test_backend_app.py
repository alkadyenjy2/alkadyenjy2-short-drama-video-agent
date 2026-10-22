import unittest
from unittest.mock import patch

import backend_app


class PersistentApiSchemaPermissionTests(unittest.TestCase):
    @patch("backend_app.PostgresRepository")
    def test_runtime_repository_does_not_run_schema_ddl(self, postgres_repository):
        result = backend_app.repository()

        postgres_repository.assert_called_once_with(initialize_schema=False)
        self.assertIs(result, postgres_repository.return_value)


if __name__ == "__main__":
    unittest.main()
