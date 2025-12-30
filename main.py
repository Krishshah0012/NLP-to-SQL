"""
Simple CLI example for Natural Language to SQL translation
"""
import os
import sys
from nlp_to_sql import NLToSQLTranslator
from config import settings


def main():
    """Main CLI function"""
    if not settings.OPENAI_API_KEY:
        print("Error: OPENAI_API_KEY environment variable not set")
        print("Please set it with: export OPENAI_API_KEY='your-key-here'")
        sys.exit(1)
    
    if len(sys.argv) < 2:
        print("Usage: python main.py '<natural language query>'")
        print("\nExample:")
        print("  python main.py 'Show me all customers'")
        print("  python main.py 'What are the top 5 products by price?'")
        sys.exit(1)
    
    query = " ".join(sys.argv[1:])
    
    try:
        # Initialize translator
        translator = NLToSQLTranslator(settings.DATABASE_PATH)
        
        print(f"\n📝 Natural Language Query: {query}\n")
        
        # Translate
        print("🔄 Translating to SQL...")
        result = translator.translate(query, use_cache=True)
        
        print(f"✅ Generated SQL:")
        print(f"   {result['sql']}\n")
        
        if result.get('explanation'):
            print(f"💡 Explanation: {result['explanation']}\n")
        
        if result.get('cached'):
            print("💾 Result retrieved from cache\n")
        
        # Execute query
        print("🔍 Executing query...")
        execution_result = translator.execute_query(result['sql'])
        
        print(f"\n📊 Results ({execution_result['row_count']} rows):")
        print("-" * 80)
        
        if execution_result['row_count'] > 0:
            # Print column headers
            columns = execution_result['columns']
            print(" | ".join(f"{col:15}" for col in columns))
            print("-" * 80)
            
            # Print rows (limit to 10 for display)
            for row in execution_result['data'][:10]:
                print(" | ".join(f"{str(val):15}" for val in row.values()))
            
            if execution_result['row_count'] > 10:
                print(f"... and {execution_result['row_count'] - 10} more rows")
        else:
            print("No results found")
        
        print("-" * 80)
        print(f"⏱️  Execution time: {result.get('execution_time', 0):.2f}s")
        
    except ValueError as e:
        print(f"❌ Error: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
