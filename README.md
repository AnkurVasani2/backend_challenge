# **SQL Query Generator API**

#### Render Link: https://backend-challengege.onrender.com
#### [Postman Collection File](https://ankur-team.postman.co/workspace/Ankur-Team-Workspace~c55a835e-3204-4c03-8f36-44dd73f76f9e/collection/40041981-22d518f7-9b86-4c23-b906-53b57037ffb8?action=share&creator=40041981)

## API Documentation

This project provides an API that allows you to:

- **POST /query**: Convert a natural language query to an SQL query and execute it on an in-memory SQLite database.
- **POST /validate**: Validate a given SQL query and return a validation message.
- **POST /explain**: Provide an explanation of the SQL query to help understand its structure and purpose.

### API Endpoints

1. **POST /query**  
   **Description**: Convert a natural language query to an SQL statement and execute it on the in-memory SQLite database.  
   **Request Body**:
   ```json
   {
     "query": "What is the average salary of employees in the HR department?"
   }
   ```
### Response Example:
```bash 
{
  "query": "What is the average salary of employees in the HR department?",
  "generated_sql": "SELECT AVG(salary) FROM employees WHERE department = 'HR'",
  "result": 50000.0,
  "message": "Query processed successfully!"
}
```
2. POST /validate
Description: Validate a given SQL query for correctness and return a validation message.
Request Body:
```bash
{
  "query": "SELECT * FROM employees WHERE department = 'Engineering'"
}
```
Response Example:
```bash
{
  "query": "SELECT * FROM employees WHERE department = 'Engineering'",
  "validation_message": "The SQL query is valid and will return all employee
  s from the Engineering department."
}
```
3. POST /explain
Description: Explain the given SQL query in detail.
Request Body:

```bash
{
  "query": "SELECT * FROM employees WHERE department = 'Engineering'"
}
```
```bash
{
  "query": "SELECT * FROM employees WHERE department = 'Engineering'",
  "explanation": "This query selects all columns from the 'employees' table where the department is 'Engineering'."
}
```

## Postman Collection
You can easily test the API using the provided Postman collection. To import and use the collection, follow these steps:

Steps to Import the Postman Collection
1. Download the Postman Collection:

Click the link below to download the collection:
[Postman Collection File](https://ankur-team.postman.co/workspace/Ankur-Team-Workspace~c55a835e-3204-4c03-8f36-44dd73f76f9e/collection/40041981-22d518f7-9b86-4c23-b906-53b57037ffb8?action=share&creator=40041981)

2. Import the Collection into Postman:

- Open Postman.

- Click Import in the top left corner of the Postman app.

- Choose Upload Files and select the downloaded JSON file for the collection.

3. Make API Requests: After importing the collection, you can easily test the API by sending requests through Postman. You can try the sample requests provided or modify them according to your requirements.


## Running the Project Locally
To run this project on your local machine:

### Prerequisites
Make sure you have Python 3.x installed and have a virtual environment (optional but recommended).

1. Clone the Repository:

```bash
git clone https://github.com/AnkurVasani2/backend_challenge.git
cd backend_challenge
```
2. Set Up a Virtual Environment (optional but recommended):

- Create a virtual environment:
```bash 
python -m venv venv
```
- Activate the virtual environment:

   - On Windows:
    ```bash 
    venv\Scripts\activate
    ```
3. Install Dependencies: Install the required Python libraries from requirements.txt:

```
pip install -r requirements.txt
```
4. Set Up Environment Variables: Create a .env file in the project root directory and add your Google Gemini API key:

```
GEMINI_API_KEY=your_api_key_here
```

5. Start the Flask Server:
```
python app.py
```