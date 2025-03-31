import os
import json
import sqlite3
from flask import Flask, request, jsonify
from google import genai
from google.genai import types
from dotenv import load_dotenv

# Load environment variables from a .env file if present
load_dotenv()

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

def init_in_memory_db():
    """Initialize an in-memory SQLite DB and pre-populate it with employee records."""
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
    for emp in employees:
        cursor.execute("INSERT INTO employees (name, age, department, salary, experience, city) VALUES (?, ?, ?, ?, ?, ?)", emp)
    conn.commit()
    cursor.close()
    return conn

# Global in-memory database connection
in_memory_conn = init_in_memory_db()

def get_sql_response(sql_query):
    """Execute the SQL query on the in-memory DB. If a common naming error occurs, attempt a correction."""
    try:
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
        error_message = str(e)
        # Correct common naming issues: "employee" -> "employees", "emp_name" -> "name"
        if "no such table: employee" in error_message:
            corrected_query = sql_query.replace("employee", "employees").replace("emp_name", "name")
            try:
                cursor = in_memory_conn.cursor()
                cursor.execute(corrected_query)
                if corrected_query.strip().upper().startswith("SELECT"):
                    output = cursor.fetchall()
                else:
                    in_memory_conn.commit()
                    output = "Query executed successfully (after correction)"
                cursor.close()
                return output
            except sqlite3.Error as e2:
                return f"SQLite error after correction attempt: {e2}"
        else:
            return f"SQLite error: {e}"

app = Flask(__name__)

@app.route('/query', methods=['POST'])
def query_api():
    data = request.get_json()
    if not data or "query" not in data:
        return jsonify({"error": "No query provided"}), 400

    query_text = data["query"]

    client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))
    tools = types.Tool(function_declarations=[sql_function])
    config = types.GenerateContentConfig(tools=[tools])

    response = client.models.generate_content(
        model="gemini-2.0-flash",
        contents=query_text,
        config=config
    )

    function_call = None
    if response.candidates and response.candidates[0].content.parts:
        part = response.candidates[0].content.parts[0]
        if hasattr(part, "function_call") and part.function_call:
            function_call = part.function_call

    if function_call:
        try:
            args = function_call.args if isinstance(function_call.args, dict) else json.loads(function_call.args)
            sql_query = clean_sql_text(args.get("sql", ""))
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
        cleaned_output = clean_sql_text(response.text)
        return jsonify({
            "query": query_text,
            "output": cleaned_output,
            "message": "No function call was made by Gemini."
        })

if __name__ == '__main__':
    app.run(debug=True)
