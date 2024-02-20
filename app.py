from compare_llm import compare_llm_results , get_report , get_db_schema_as_string
from sql_rag import Database
from fastapi import FastAPI, Request , Path , HTTPException, File, UploadFile , Security, Depends 
from fastapi.responses import FileResponse
from typing import Optional, Dict
import mysql.connector
import json
# from auth import verify_token
import os
import pandas as pd

from fastapi.responses import FileResponse

# Create an instance of the FastAPI class
app = FastAPI()





# Define a route for handling POST requests with parameters in the request body
@app.post("/process_request/")
async def process_request(request: Request):
    try:
        # Access request body
        request_body = await request.json()

        # Extract parameters from request body
        db_data = request_body.get("db")
        gpt_query = request_body.get("gpt_query")
        question = request_body.get("question")
        db_schema = request_body.get("db_schema")
        session_id = request_body.get("session_id")

        

        # Create a database connection
        db = Database(host=db_data.get("db_host"), 
                      db_user=db_data.get("db_user"), 
                      db_name=db_data.get("db_name"), 
                      db_password=db_data.get("db_password"))

        if db_schema == "":
            db_schema = get_db_schema_as_string(db)
            

        print(db.is_connected())

        # Process the data
        response, explanation, df = compare_llm_results(db, gpt_query, question, db_schema, session_id)
        print("asdasdasdasssssssssss")
        df_json = df.to_json(orient='records')

        processed_data = {
            "response": response,
            "df": df_json,
            "explanation": explanation
        }
        print(json.dumps(processed_data))
        

        # Return processed data as response
        return processed_data

    except Exception as e:
        # Print the error for debugging
        print(f"An error occurred: {e}")

        # Return an error response
        return {"error": "An error occurred while processing the request."}


# Define a route for handling POST requests to get the report file
@app.get("/reports/{session_id}")
async def get_report(session_id: str):
    """
    Retrieve a CSV report from the 'Reports' folder based on the provided session ID.

    Requires a valid authorization token in the 'Authorization' header.

    Returns:
        StreamingResponse: The CSV file content if found, otherwise a 404 error.
    """

    # Authenticate the user (replace with your implementation)
    # ... verify_token should validate the token and return user ID/session data

    report_path = f"Reports/output{session_id}.csv"
    try:
        with open(report_path, "rb") as report_file:
            content = report_file.read()
            return FileResponse(
                content,
                media_type="text/csv",
                headers={
                    "Content-Disposition": f"attachment; filename={report_path}"
                }
            )
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail="Report not found")


REPORTS_DIR = "Reports"
FRONT_DIR = "Front"

@app.get("/get_report/{session_id}")
def get_report(session_id: str = Path(..., title="The session ID")):
    file_path = os.path.join(REPORTS_DIR, f"output{session_id}.csv")
    if os.path.exists(file_path):
        return FileResponse(file_path, media_type='text/csv')
    else:
        return {"message": "Report not found"}

    # Define a main function to start the server
def main():
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=5000, reload=True)

# Check if the script is being run directly
if __name__ == "__main__":
    main()
