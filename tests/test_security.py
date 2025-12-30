"""Security tests for SQL injection prevention and input validation"""

import pytest
from src.nodes import validate_sql_query
from src.errors import SQLGenerationError


class TestSQLInjectionPrevention:
    """Test SQL injection attack prevention"""

    @pytest.fixture
    def allowed_tables(self):
        """Common allowed tables for testing"""
        return {'sales', 'products', 'customers'}

    def test_multiple_statements_blocked(self, allowed_tables):
        """Multiple SQL statements should be blocked"""
        with pytest.raises(SQLGenerationError):
            validate_sql_query(
                "SELECT * FROM sales; DROP TABLE users;",
                allowed_tables
            )

    def test_inline_comments_blocked(self, allowed_tables):
        """Inline comments should be blocked"""
        with pytest.raises(SQLGenerationError):
            validate_sql_query(
                "SELECT * FROM sales -- comment",
                allowed_tables
            )

    def test_block_comments_blocked(self, allowed_tables):
        """Block comments should be blocked"""
        with pytest.raises(SQLGenerationError):
            validate_sql_query(
                "SELECT * FROM sales /* comment */",
                allowed_tables
            )

    def test_drop_table_blocked(self, allowed_tables):
        """DROP TABLE statements should be blocked"""
        with pytest.raises(SQLGenerationError):
            validate_sql_query(
                "DROP TABLE sales",
                allowed_tables
            )

    def test_delete_blocked(self, allowed_tables):
        """DELETE statements should be blocked"""
        with pytest.raises(SQLGenerationError):
            validate_sql_query(
                "DELETE FROM sales",
                allowed_tables
            )

    def test_update_blocked(self, allowed_tables):
        """UPDATE statements should be blocked"""
        with pytest.raises(SQLGenerationError):
            validate_sql_query(
                "UPDATE sales SET price=0",
                allowed_tables
            )

    def test_insert_blocked(self, allowed_tables):
        """INSERT statements should be blocked"""
        with pytest.raises(SQLGenerationError):
            validate_sql_query(
                "INSERT INTO sales VALUES (1, 2, 3)",
                allowed_tables
            )

    def test_alter_blocked(self, allowed_tables):
        """ALTER statements should be blocked"""
        with pytest.raises(SQLGenerationError):
            validate_sql_query(
                "ALTER TABLE sales ADD COLUMN fake INT",
                allowed_tables
            )

    def test_unknown_table_blocked(self, allowed_tables):
        """Queries with unknown tables should be blocked"""
        with pytest.raises(SQLGenerationError):
            validate_sql_query(
                "SELECT * FROM unknown_table",
                allowed_tables
            )

    def test_valid_select_allowed(self, allowed_tables):
        """Valid SELECT queries should pass"""
        queries = [
            "SELECT * FROM sales",
            "SELECT COUNT(*) FROM products WHERE price > 100",
            "SELECT name, price FROM products ORDER BY price DESC",
            "SELECT s.id, p.name FROM sales s JOIN products p ON s.product_id = p.id"
        ]

        for query in queries:
            assert validate_sql_query(query, allowed_tables) is True

    def test_case_insensitive_keywords(self, allowed_tables):
        """SQL keywords should be detected case-insensitively"""
        with pytest.raises(SQLGenerationError):
            validate_sql_query(
                "SeLeCt * FrOm sales; DrOp TaBlE users",
                allowed_tables
            )


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
