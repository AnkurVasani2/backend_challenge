import os
import json
import sqlite3
from flask import Flask, request, jsonify
from google import genai
from google.genai import types
from dotenv import load_dotenv

# Load environment variables from a .env file if present
load_dotenv()

# Initialize the in-memory SQLite database and pre-populate it with sample data
def init_in_memory_db():
    # Using check_same_thread=False so the connection can be shared across threads (for testing purposes)
    conn = sqlite3.connect(':memory:', check_same_thread=False)
    cursor = conn.cursor()
    # Create the employees table
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
    # Pre-populate with sample employee records
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
    for emp in employees:
        cursor.execute("INSERT INTO employees (name, age, department, salary, experience, city) VALUES (?, ?, ?, ?, ?, ?)", emp)
    conn.commit()
    cursor.close()
    return conn

# Create a global in-memory database connection
in_memory_conn = init_in_memory_db()

# Define the function declaration for converting the natural language query to SQL and executing it.
sql_function = {
    "name": "get_sql_response",
    "description": "Converts a natural language query to a SQL statement and executes it on the in-memory SQLite database.",
    "parameters": {
        "type": "object",
        "properties": {
            "sql": {
                "type": "string",
                "description": "The SQL statement to execute.",
            },
        },
        "required": ["sql"],
    },
}

def get_sql_response(sql_query):
    """
    Execute the provided SQL query using the in-memory SQLite database.
    """
    try:
        cursor = in_memory_conn.cursor()
        cursor.execute(sql_query)
        # If it's a SELECT query, fetch and return the results.
        if sql_query.strip().upper().startswith("SELECT"):
            output = cursor.fetchall()
        else:
            in_memory_conn.commit()
            output = "Query executed successfully"
        cursor.close()
        return output
    except sqlite3.Error as e:
        return f"SQLite error: {e}"

app = Flask(__name__)

@app.route('/query', methods=['POST'])
def query_api():
    data = request.get_json()
    if not data or 'query' not in data:
        return jsonify({"error": "No query provided"}), 400

    query_text = data['query']

    # Configure the Gemini API client and tool using the function calling pattern.
    client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))
    tools = types.Tool(function_declarations=[sql_function])
    config = types.GenerateContentConfig(tools=[tools])

    response = client.models.generate_content(
        model="gemini-2.0-flash",
        contents=query_text,
        config=config,
    )

    # Check if a function call was returned.
    function_call = None
    if response.candidates and response.candidates[0].content.parts:
        part = response.candidates[0].content.parts[0]
        if hasattr(part, "function_call") and part.function_call:
            function_call = part.function_call

    if function_call:
        try:
            # If the function call arguments are already a dict, use them directly.
            if isinstance(function_call.args, dict):
                args = function_call.args
            else:
                args = json.loads(function_call.args)
            sql_query = args.get("sql", "")
            result = get_sql_response(sql_query)
            return jsonify({
                "query": query_text,
                "generated_sql": sql_query,
                "result": result,
                "message": "Query processed successfully!"
            })
        except Exception as e:
            return jsonify({"error": f"Error parsing function call arguments: {e}"}), 500
    else:
        return jsonify({
            "query": query_text,
            "output": response.text,
            "message": "No function call was made by Gemini."
        })

if __name__ == '__main__':
    app.run(debug=True)
