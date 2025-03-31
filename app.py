import os
import json
import sqlite3
from flask import Flask, request, jsonify
from google import genai
from google.genai import types
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Initialize Flask app
app = Flask(__name__)
client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))

# SQL function schema for Gemini
sql_function = {
    "name": "get_sql_response",
    "description": "Converts a natural language query to a SQL statement and executes it on the in-memory SQLite database.",
    "parameters": {
        "type": "object",
        "properties": {
            "sql": {
                "type": "string",
                "description": "The SQL statement to execute."
            }
        },
        "required": ["sql"]
    }
}

def clean_sql_text(sql_text):
    """Remove markdown code block markers from the SQL text."""
    sql_text = sql_text.strip()
    if sql_text.startswith("```"):
        lines = sql_text.splitlines()
        if lines[0].startswith("```"):
            lines = lines[1:]
        if lines and lines[-1].strip() == "```":
            lines = lines[:-1]
        return "\n".join(lines).strip()
    return sql_text

def init_in_memory_db():
    """Initialize an in-memory SQLite DB and populate it with employee records."""
    conn = sqlite3.connect(":memory:", check_same_thread=False)
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE employees (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            age INTEGER,
            department TEXT,
            salary REAL,
            experience INTEGER,
            city TEXT
        )
    """)
    employees = [
        ("Amit Sharma", 30, "HR", 50000, 5, "Mumbai"),
        ("Rajesh Kumar", 28, "Engineering", 75000, 3, "Bangalore"),
        ("Priya Verma", 35, "Marketing", 60000, 8, "Delhi"),
        ("Sanjay Patel", 40, "Finance", 80000, 12, "Ahmedabad"),
        ("Neha Gupta", 26, "Sales", 55000, 2, "Pune"),
        ("Vikas Yadav", 32, "Support", 48000, 6, "Hyderabad"),
        ("Anjali Nair", 29, "Product", 70000, 4, "Chennai"),
        ("Ravi Menon", 37, "Operations", 72000, 10, "Kolkata"),
        ("Swati Joshi", 31, "IT", 65000, 7, "Jaipur"),
        ("Deepak Mishra", 27, "Design", 58000, 3, "Indore")
    ]
    cursor.executemany("INSERT INTO employees (name, age, department, salary, experience, city) VALUES (?, ?, ?, ?, ?, ?)", employees)
    conn.commit()
    cursor.close()
    return conn

# Global in-memory database connection
in_memory_conn = init_in_memory_db()

def get_sql_response(sql_query):
    """Execute the SQL query on the in-memory DB."""
    try:
        sql_query = clean_sql_text(sql_query)
        cursor = in_memory_conn.cursor()
        cursor.execute(sql_query)
        if sql_query.strip().upper().startswith("SELECT"):
            output = cursor.fetchall()
        else:
            in_memory_conn.commit()
            output = "Query executed successfully"
        cursor.close()
        return output
    except sqlite3.Error as e:
        return f"SQLite error: {e}"

def query_gemini(prompt):
    """Generate SQL from a natural language prompt using Gemini."""
    response = client.models.generate_content(model="gemini-2.0-flash", contents=prompt)
    return response.text.strip() if response.text else "No response from Gemini."

@app.route('/query', methods=['POST'])
def query_api():
    data = request.get_json()
    if not data or "query" not in data:
        return jsonify({"error": "No query provided"}), 400

    query_text = data["query"]
    prompt = f"Convert the following natural language query into SQL: dont include extra characters in your response like '\n' etc \n{query_text}\nSchema: CREATE TABLE employees (id INTEGER PRIMARY KEY, name TEXT, age INTEGER, department TEXT, salary REAL, experience INTEGER, city TEXT);"
    sql_query = clean_sql_text(query_gemini(prompt))
    result = get_sql_response(sql_query)

    return jsonify({
        "query": query_text,
        "generated_sql": sql_query,
        "result": result,
        "message": "Query processed successfully!"
    })

@app.route('/validate', methods=['POST'])
def validate_api():
    data = request.get_json()
    if not data or "query" not in data:
        return jsonify({"error": "No SQL query provided"}), 400
    
    sql_query = clean_sql_text(data["query"])
    response = client.models.generate_content(model="gemini-2.0-flash", contents=f"Validate this SQL query and give a clear 2 sentence validation message: {sql_query}")
    validation_message = response.text.strip() if response.text else "Validation completed with no issues."
    return jsonify({"query": sql_query, "validation_message": validation_message})

@app.route('/explain', methods=['POST'])
def explain_api():
    data = request.get_json()
    if not data or "query" not in data:
        return jsonify({"error": "No SQL query provided"}), 400
    
    sql_query = clean_sql_text(data["query"])
    response = client.models.generate_content(model="gemini-2.0-flash", contents=f"Explain this SQL query in detail in atmost 5 sentences without  \n's : {sql_query}")
    explanation = response.text.strip() if response.text else "Explanation generated."
    return jsonify({"query": sql_query, "explanation": explanation})

if __name__ == '__main__':
    app.run(debug=True)
