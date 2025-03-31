import os
import json
import sqlite3
from flask import Flask, request, jsonify
from google import genai
from google.genai import types
from dotenv import load_dotenv

sql_function = {
    "name": "get_sql_response",
    "description": "Converts a natural language query to a SQL statement and executes it on the SQLite database 'employees.db'.",
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
    Execute the provided SQL query using SQLite3 and return the output.
    Uses 'employees.db' as the database file.
    """
    try:
        conn = sqlite3.connect("employees.db")
        cursor = conn.cursor()
        cursor.execute(sql_query)
        if sql_query.strip().upper().startswith("SELECT"):
            output = cursor.fetchall()
        else:
            conn.commit()
            output = "Query executed successfully"
        cursor.close()
        conn.close()
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
    client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))
    tools = types.Tool(function_declarations=[sql_function])
    config = types.GenerateContentConfig(tools=[tools])

    response = client.models.generate_content(
        model="gemini-2.0-flash",
        contents=query_text,
        config=config,
    )
    function_call = None
    if response.candidates and response.candidates[0].content.parts:
        part = response.candidates[0].content.parts[0]
        if hasattr(part, "function_call") and part.function_call:
            function_call = part.function_call

    if function_call:
        try:
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
