from fastapi import FastAPI
from fastapi import FastAPI, UploadFile, File, HTTPException
import pandas as pd
import numpy as np
from sklearn.preprocessing import StandardScaler
from sklearn.impute import KNNImputer
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
