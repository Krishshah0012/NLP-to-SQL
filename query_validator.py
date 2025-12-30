"""
SQL query validation and safety checking module
"""
import re
from typing import Dict, List


class QueryValidator:
    """Validate SQL queries and check for safety issues"""
    
    # Dangerous SQL operations that should be blocked
    DANGEROUS_KEYWORDS = [
        "DROP", "DELETE", "TRUNCATE", "ALTER", "CREATE", "INSERT",
        "UPDATE", "REPLACE", "EXEC", "EXECUTE", "GRANT", "REVOKE"
    ]
    
    # Allowed operations (read-only)
    ALLOWED_KEYWORDS = ["SELECT", "WITH"]
    
    def __init__(self):
        self.dangerous_patterns = [
            re.compile(rf"\b{keyword}\b", re.IGNORECASE)
            for keyword in self.DANGEROUS_KEYWORDS
        ]
    
    def validate(self, sql: str) -> Dict[str, Any]:
        """
        Validate SQL query syntax and structure
        
        Args:
            sql: SQL query to validate
            
        Returns:
            Dictionary with validation result and error message if invalid
        """
        sql = sql.strip()
        
        # Check if query is empty
        if not sql:
            return {
                "is_valid": False,
                "error": "Query is empty"
            }
        
        # Check if query starts with allowed keyword
        sql_upper = sql.upper()
        if not any(sql_upper.strip().startswith(keyword) for keyword in self.ALLOWED_KEYWORDS):
            return {
                "is_valid": False,
                "error": "Query must start with SELECT or WITH"
            }
        
        # Basic syntax checks
        # Check for balanced parentheses
        if sql.count("(") != sql.count(")"):
            return {
                "is_valid": False,
                "error": "Unbalanced parentheses"
            }
        
        # Check for balanced quotes
        single_quotes = sql.count("'") - sql.count("\\'")
        double_quotes = sql.count('"') - sql.count('\\"')
        if single_quotes % 2 != 0 or double_quotes % 2 != 0:
            return {
                "is_valid": False,
                "error": "Unbalanced quotes"
            }
        
        return {
            "is_valid": True,
            "error": None
        }
    
    def is_safe(self, sql: str) -> bool:
        """
        Check if SQL query is safe to execute (read-only)
        
        Args:
            sql: SQL query to check
            
        Returns:
            True if query is safe, False otherwise
        """
        sql_upper = sql.upper()
        
        # Check for dangerous keywords
        for pattern in self.dangerous_patterns:
            if pattern.search(sql):
                return False
        
        # Ensure query starts with SELECT or WITH (CTE)
        if not any(sql_upper.strip().startswith(keyword) for keyword in self.ALLOWED_KEYWORDS):
            return False
        
        # Check for SQL injection patterns
        dangerous_patterns = [
            r";\s*(DROP|DELETE|INSERT|UPDATE)",  # Multiple statements
            r"UNION.*SELECT",  # SQL injection via UNION
            r"EXEC\s*\(",  # Execution functions
            r"xp_\w+",  # Extended stored procedures
        ]
        
        for pattern in dangerous_patterns:
            if re.search(pattern, sql, re.IGNORECASE):
                return False
        
        return True
    
    def get_safety_report(self, sql: str) -> Dict[str, Any]:
        """
        Get detailed safety report for a query
        
        Args:
            sql: SQL query to analyze
            
        Returns:
            Dictionary with safety analysis
        """
        is_safe = self.is_safe(sql)
        validation = self.validate(sql)
        
        issues = []
        
        if not is_safe:
            for pattern in self.dangerous_patterns:
                if pattern.search(sql):
                    issues.append(f"Contains dangerous keyword: {pattern.pattern}")
        
        return {
            "is_safe": is_safe,
            "is_valid": validation["is_valid"],
            "issues": issues,
            "validation_error": validation.get("error")
        }

