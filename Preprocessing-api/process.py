from fastapi import FastAPI
from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.responses import JSONResponse
import pandas as pd
import io
from fastapi.responses import StreamingResponse

app = FastAPI()

#FastAPI automatically generates interactive API documentation. 
# You can access it at http://127.0.0.1:8000/docs to explore your API and test the endpoints.

# Utility function to read CSV file
def read_csv_file(file: UploadFile):
    if file.filename.endswith('.csv'):
        content = file.file.read().decode("utf-8")
        data = pd.read_csv(io.StringIO(content))
        return data
    else:
        raise HTTPException(status_code=400, detail="Invalid file format. Please upload a CSV file.")
    
@app.post("/handle_missing_values_mean/")
async def handle_missing_values_mean(file: UploadFile = File(...)):
    data = read_csv_file(file)

    # Identify numeric features
    numeric_features = data.select_dtypes(include=['float', 'int']).columns

    # Handle missing values using mean imputation
    for feature in numeric_features:
        data[feature].fillna(data[feature].mean(), inplace=True)

    # Create a StreamingResponse with CSV data
    stream = io.StringIO()
    data.to_csv(stream, index=False)
    response = StreamingResponse(iter([stream.getvalue()]), media_type="text/csv")
    response.headers["Content-Disposition"] = "attachment; filename=processed_data.csv"

    return response

@app.post("/detect_missing_values/")
async def detect_missing_values(file: UploadFile = File(...)):
    data = read_csv_file(file)
    
    # Replace empty strings with NaN
    data = data.replace(r'^\s*$', pd.NA, regex=True)
    
    # Detect missing values
    missing_values = data.isnull().sum()
    missing_percentage = (missing_values / len(data)) * 100

    # Prepare the response
    missing_data = {
        column: {
            "count": int(count),
            "percentage": round(percentage, 2)
        }
        for column, (count, percentage) in zip(missing_values.index, zip(missing_values, missing_percentage))
        if count > 0
    }

    # Get rows with missing values
    rows_with_missing = data[data.isnull().any(axis=1)].index.tolist()

    response = {
        "missing_values_by_column": missing_data,
        "rows_with_missing_values": rows_with_missing,
        "total_rows": len(data),
        "total_columns": len(data.columns)
    }

    if missing_data:
        return JSONResponse(content=response)
    else:
        return JSONResponse(content={"message": "No missing values found in the data."})