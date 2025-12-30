# Quick Start Guide

## Setup (5 minutes)

1. **Install dependencies:**
```bash
pip install -r requirements.txt
```

2. **Set your OpenAI API key:**
```bash
export OPENAI_API_KEY="your-api-key-here"
```

3. **Start the API server:**
```bash
python app.py
```

The API will be running at `http://localhost:8000`

## Test the API

### Using cURL:

```bash
# Translate natural language to SQL
curl -X POST "http://localhost:8000/translate" \
  -H "Content-Type: application/json" \
  -d '{"query": "Show me all customers"}'

# Query and execute in one step
curl -X POST "http://localhost:8000/query" \
  -H "Content-Type: application/json" \
  -d '{"query": "What are the top 5 products by price?"}'
```

### Using Python:

```python
import requests

# Translate
response = requests.post(
    "http://localhost:8000/translate",
    json={"query": "Show me all customers with their order counts"}
)
print(response.json())

# Query and execute
response = requests.post(
    "http://localhost:8000/query",
    json={"query": "What is the total revenue?"}
)
print(response.json())
```

### Using CLI:

```bash
python main.py "Show me all customers"
python main.py "What are the top 5 products by price?"
```

## Example Queries

Try these natural language queries:

- "Show me all customers"
- "What are the top 5 products by price?"
- "Which customers have placed orders?"
- "What is the total revenue?"
- "Show me customers with more than 3 orders"
- "What is the average order value?"

## API Documentation

Once the server is running, visit:
- Swagger UI: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`

## Troubleshooting

**Error: OPENAI_API_KEY not set**
- Make sure you've exported the environment variable or set it in a `.env` file

**Error: Database not found**
- Ensure `retail.db` exists in the project directory
- Or set `DATABASE_PATH` environment variable to your database path

**Error: Module not found**
- Run `pip install -r requirements.txt` to install all dependencies

