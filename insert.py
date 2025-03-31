import sqlite3

def execute_query(db_path, query, params=None):
    """
    Execute an SQL query on an SQLite database.

    :param db_path: Path to the SQLite database file.
    :param query: SQL query to execute.
    :param params: Tuple of parameters for parameterized queries (default: None).
    """
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        if params:
            cursor.execute(query, params)
        else:
            cursor.execute(query)
        
        conn.commit()
        cursor.close()
        conn.close()
    except sqlite3.Error as e:
        print(f"SQLite error: {e}")

# Setup Database
db_path = "employees.db"

# Create employees table
execute_query(db_path, """
CREATE TABLE IF NOT EXISTS employees (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    age INTEGER,
    department TEXT,
    salary REAL,
    experience INTEGER,
    city TEXT
)
""")

# Insert 10 employee records with Indian names and additional parameters
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
    execute_query(db_path, "INSERT INTO employees (name, age, department, salary, experience, city) VALUES (?, ?, ?, ?, ?, ?)", emp)

