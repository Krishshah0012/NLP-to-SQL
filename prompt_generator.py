"""
Schema-aware prompt generator for LLM
"""
from typing import Dict, Any


class PromptGenerator:
    """Generate optimized prompts for SQL generation"""
    
    SYSTEM_PROMPT_TEMPLATE = """You are an expert SQL query generator. Your task is to convert natural language questions into accurate SQL queries.

Rules:
1. Generate ONLY valid SQLite SQL queries
2. Use the exact table and column names from the provided schema
3. Do NOT include any explanations or markdown formatting in your response - just the SQL query
4. Use proper JOIN syntax when querying multiple tables
5. Use appropriate aggregate functions (COUNT, SUM, AVG, etc.) when needed
6. Always use parameterized-style thinking but output raw SQL
7. Ensure queries are efficient and use proper indexes when possible
8. Return only SELECT queries - never generate INSERT, UPDATE, DELETE, or DROP statements
9. Use proper SQL syntax including WHERE clauses, GROUP BY, ORDER BY as needed

The database schema will be provided in the user's message."""

    USER_PROMPT_TEMPLATE = """Database Schema:
{schema}

Natural Language Query: {query}

Generate a SQL query for the above question. Return ONLY the SQL query, no explanations."""

    def generate_prompt(
        self,
        natural_language_query: str,
        schema: Dict[str, Any]
    ) -> Dict[str, str]:
        """
        Generate schema-aware prompt for LLM
        
        Args:
            natural_language_query: User's natural language question
            schema: Database schema dictionary
            
        Returns:
            Dictionary with system_prompt and user_prompt
        """
        schema_text = self._format_schema(schema)
        
        user_prompt = self.USER_PROMPT_TEMPLATE.format(
            schema=schema_text,
            query=natural_language_query
        )
        
        return {
            "system_prompt": self.SYSTEM_PROMPT_TEMPLATE,
            "user_prompt": user_prompt
        }
    
    def _format_schema(self, schema: Dict[str, Any]) -> str:
        """Format schema dictionary into readable text"""
        lines = []
        
        for table_name, table_info in schema["tables"].items():
            lines.append(f"\nTable: {table_name}")
            lines.append(f"  Row count: {table_info['row_count']}")
            lines.append("  Columns:")
            
            for col in table_info["columns"]:
                col_str = f"    - {col['name']} ({col['type']})"
                if col["primary_key"]:
                    col_str += " [PRIMARY KEY]"
                if not col["nullable"]:
                    col_str += " [NOT NULL]"
                lines.append(col_str)
            
            if table_info["foreign_keys"]:
                lines.append("  Foreign Keys:")
                for fk in table_info["foreign_keys"]:
                    if fk.get("column") and fk.get("references_table"):
                        ref_col = fk.get("references_column") or "id"
                        lines.append(
                            f"    - {fk['column']} -> "
                            f"{fk['references_table']}.{ref_col}"
                        )
        
        return "\n".join(lines)

