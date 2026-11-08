import os
from dotenv import load_dotenv
from groq import Groq

load_dotenv()

client = Groq(api_key=os.getenv("GROQ_API_KEY"))

response = client.chat.completions.create(
    messages=[{"role": "user", "content": "Write a SQL query to get the 5 highest paid employees from a table called employees."}],
    model="qwen/qwen3.8-27b",
)
print(response.choices[0].message.content)