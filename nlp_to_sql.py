"""
Main NL to SQL translation module with schema awareness and caching
"""
import sqlite3
import openai
import os
import hashlib
import json
import time
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta

from schema_introspector import SchemaIntrospector
from prompt_generator import PromptGenerator
from query_validator import QueryValidator
from cache_manager import CacheManager


class NLToSQLTranslator:
    """Main translator class that orchestrates NL to SQL conversion"""
    
    def __init__(self, database_path: str, cache_enabled: bool = True):
        self.database_path = database_path
        self.cache_enabled = cache_enabled
        
        # Initialize OpenAI client
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            raise ValueError("OPENAI_API_KEY environment variable not set")
        self.client = openai.OpenAI(api_key=api_key)
        
        # Initialize components
        self.introspector = SchemaIntrospector(database_path)
        self.prompt_generator = PromptGenerator()
        self.validator = QueryValidator()
        self.cache = CacheManager() if cache_enabled else None
        
        # Load schema
        self.schema = self.introspector.get_schema()
    
    def get_schema(self) -> Dict[str, Any]:
        """Get database schema information"""
        return self.schema
    
    def translate(
        self,
        natural_language_query: str,
        use_cache: bool = True
    ) -> Dict[str, Any]:
        """
        Translate natural language query to SQL
        
        Args:
            natural_language_query: Natural language question
            use_cache: Whether to use cache for this query
            
        Returns:
            Dictionary with SQL, explanation, and metadata
        """
        start_time = time.time()
        
        # Check cache first
        if use_cache and self.cache:
            cache_key = self._generate_cache_key(natural_language_query)
            cached_result = self.cache.get(cache_key)
            if cached_result:
                cached_result["cached"] = True
                cached_result["execution_time"] = time.time() - start_time
                return cached_result
        
        # Generate schema-aware prompt
        prompt = self.prompt_generator.generate_prompt(
            natural_language_query=natural_language_query,
            schema=self.schema
        )
        
        # Call OpenAI API
        try:
            response = self.client.chat.completions.create(
                model="gpt-4",
                messages=[
                    {"role": "system", "content": prompt["system_prompt"]},
                    {"role": "user", "content": prompt["user_prompt"]}
                ],
                temperature=0.1,  # Low temperature for consistent SQL generation
                max_tokens=500
            )
            
            sql_query = response.choices[0].message.content.strip()
            
            # Clean up SQL (remove markdown code blocks if present)
            if sql_query.startswith("```sql"):
                sql_query = sql_query[6:]
            if sql_query.startswith("```"):
                sql_query = sql_query[3:]
            if sql_query.endswith("```"):
                sql_query = sql_query[:-3]
            sql_query = sql_query.strip()
            
            # Validate query
            validation_result = self.validator.validate(sql_query)
            if not validation_result["is_valid"]:
                raise ValueError(
                    f"Generated SQL is invalid: {validation_result['error']}"
                )
            
            # Check safety
            if not self.validator.is_safe(sql_query):
                raise ValueError(
                    "Generated SQL contains potentially unsafe operations"
                )
            
            result = {
                "sql": sql_query,
                "explanation": self._extract_explanation(response.choices[0].message.content),
                "cached": False,
                "execution_time": time.time() - start_time
            }
            
            # Cache result
            if use_cache and self.cache:
                self.cache.set(cache_key, result)
            
            return result
            
        except openai.OpenAIError as e:
            raise ValueError(f"OpenAI API error: {str(e)}")
        except Exception as e:
            raise ValueError(f"Translation error: {str(e)}")
    
    def execute_query(
        self,
        sql: str,
        limit: int = 100
    ) -> Dict[str, Any]:
        """
        Execute SQL query and return results
        
        Args:
            sql: SQL query to execute
            limit: Maximum number of rows to return
            
        Returns:
            Dictionary with results, row count, and columns
        """
        # Final safety check
        if not self.validator.is_safe(sql):
            raise ValueError("Query contains potentially unsafe operations")
        
        try:
            conn = sqlite3.connect(self.database_path)
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            
            # Add LIMIT if not present and query is SELECT
            if sql.strip().upper().startswith("SELECT"):
                if "LIMIT" not in sql.upper():
                    sql = f"{sql.rstrip(';')} LIMIT {limit}"
            
            cursor.execute(sql)
            rows = cursor.fetchall()
            
            # Get column names
            columns = [description[0] for description in cursor.description] if cursor.description else []
            
            # Convert rows to dictionaries
            data = [dict(row) for row in rows]
            
            conn.close()
            
            return {
                "data": data,
                "row_count": len(data),
                "columns": columns
            }
            
        except sqlite3.Error as e:
            raise ValueError(f"Database error: {str(e)}")
        except Exception as e:
            raise ValueError(f"Execution error: {str(e)}")
    
    def _generate_cache_key(self, query: str) -> str:
        """Generate cache key from natural language query"""
        # Normalize query (lowercase, strip whitespace)
        normalized = query.lower().strip()
        return hashlib.md5(normalized.encode()).hexdigest()
    
    def _extract_explanation(self, content: str) -> Optional[str]:
        """Extract explanation from LLM response if present"""
        # Simple extraction - look for explanation markers
        if "explanation:" in content.lower() or "note:" in content.lower():
            lines = content.split("\n")
            explanation_lines = []
            in_explanation = False
            for line in lines:
                if "explanation:" in line.lower() or "note:" in line.lower():
                    in_explanation = True
                    explanation_lines.append(line.split(":", 1)[1].strip() if ":" in line else line)
                elif in_explanation and line.strip():
                    if line.strip().startswith("```"):
                        break
                    explanation_lines.append(line.strip())
            if explanation_lines:
                return " ".join(explanation_lines)
        return None

