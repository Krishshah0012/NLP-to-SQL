import sqlite3
import openai
import os


openai_client = openai.OpenAI(api_key=os.getenv("OPENAI_API_KEY"))