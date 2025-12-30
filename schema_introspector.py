"""
Database schema introspection module
"""
import sqlite3
from typing import Dict, List, Any


class SchemaIntrospector:
    """Extract and structure database schema information"""
    
    def __init__(self, database_path: str):
        self.database_path = database_path
    
    def get_schema(self) -> Dict[str, Any]:
        """
        Extract complete database schema
        
        Returns:
            Dictionary containing tables, columns, and relationships
        """
        conn = sqlite3.connect(self.database_path)
        cursor = conn.cursor()
        
        schema = {
            "tables": {},
            "relationships": []
        }
        
        # Get all table names
        cursor.execute("""
            SELECT name FROM sqlite_master 
            WHERE type='table' AND name NOT LIKE 'sqlite_%'
            ORDER BY name
        """)
        tables = [row[0] for row in cursor.fetchall()]
        
        # Get schema for each table
        for table_name in tables:
            table_info = self._get_table_info(cursor, table_name)
            schema["tables"][table_name] = table_info
        
        # Get foreign key relationships
        schema["relationships"] = self._get_relationships(cursor, tables)
        
        conn.close()
        return schema
    
    def _get_table_info(self, cursor: sqlite3.Cursor, table_name: str) -> Dict[str, Any]:
        """Get detailed information about a table"""
        # Get column information
        cursor.execute(f"PRAGMA table_info({table_name})")
        columns_info = cursor.fetchall()
        
        columns = []
        primary_keys = []
        
        for col_info in columns_info:
            col_id, col_name, col_type, not_null, default_val, is_pk = col_info
            
            column = {
                "name": col_name,
                "type": col_type,
                "nullable": not bool(not_null),
                "default": default_val,
                "primary_key": bool(is_pk)
            }
            columns.append(column)
            
            if is_pk:
                primary_keys.append(col_name)
        
        # Get foreign keys
        cursor.execute(f"PRAGMA foreign_key_list({table_name})")
        foreign_keys = cursor.fetchall()
        
        fk_info = []
        for fk in foreign_keys:
            fk_info.append({
                "column": columns[fk[3]]["name"] if fk[3] < len(columns) else None,
                "references_table": fk[2],
                "references_column": fk[4] if len(fk) > 4 else None
            })
        
        # Get sample data count
        cursor.execute(f"SELECT COUNT(*) FROM {table_name}")
        row_count = cursor.fetchone()[0]
        
        return {
            "columns": columns,
            "primary_keys": primary_keys,
            "foreign_keys": fk_info,
            "row_count": row_count
        }
    
    def _get_relationships(self, cursor: sqlite3.Cursor, tables: List[str]) -> List[Dict[str, Any]]:
        """Extract relationships between tables"""
        relationships = []
        
        for table_name in tables:
            cursor.execute(f"PRAGMA foreign_key_list({table_name})")
            fks = cursor.fetchall()
            
            for fk in fks:
                relationships.append({
                    "from_table": table_name,
                    "from_column": None,  # Column index is in fk[3]
                    "to_table": fk[2],
                    "to_column": fk[4] if len(fk) > 4 else None,
                    "relationship_type": "many_to_one"
                })
        
        return relationships
    
    def get_schema_text(self) -> str:
        """Get schema as formatted text for prompts"""
        schema = self.get_schema()
        
        lines = ["Database Schema:\n"]
        
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
                    if fk["column"] and fk["references_table"]:
                        lines.append(
                            f"    - {fk['column']} -> {fk['references_table']}"
                            f".{fk['references_column'] or 'id'}"
                        )
        
        return "\n".join(lines)

