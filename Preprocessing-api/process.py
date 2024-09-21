from fastapi import FastAPI, UploadFile, File, HTTPException, Query, Request
from fastapi.responses import PlainTextResponse
from fastapi.templating import Jinja2Templates
import pandas as pd
import io
from io import StringIO
import math
from fastapi.responses import StreamingResponse
import matplotlib.pyplot as plt
import matplotlib.ticker as ticker
from typing import List, Dict
from pydantic import BaseModel
import csv

app = FastAPI()

#FastAPI automatically generates interactive API documentation. 
# You can access it at http://127.0.0.1:8000/docs to explore your API and test the endpoints.

# region Utility function to read CSV file
def read_csv_file(file: UploadFile):
    if file.filename.endswith('.csv'):
        content = file.file.read().decode("utf-8")
        data = pd.read_csv(io.StringIO(content))
        return data
    else:
        raise HTTPException(status_code=400, detail="Invalid file format. Please upload a CSV file.")
# endregion

# region statistical summary
@app.post("/describe_csv",
          summary = 'Statistics for Numerical Variables' )
async def describe_csv(file: UploadFile = File(...)):
    try:
        data = read_csv_file(file)
        desc = data.describe().T
        
        # Convert the DataFrame to a Markdown table
        markdown_table = desc.to_markdown()
        
        return PlainTextResponse(content=markdown_table)
    
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
#endregion

# region csv to excel
@app.post("/csv_to_excel/")
async def csv_to_excel(file: UploadFile = File(...)):
    if not file.filename.endswith('.csv'):
        raise HTTPException(status_code=400, detail="Only CSV files are allowed")

    try:
        contents = await file.read()
        df = pd.read_csv(io.StringIO(contents.decode('utf-8')))

        # Create a BytesIO object to store the Excel file
        excel_file = io.BytesIO()

        # Write the DataFrame to the Excel file
        with pd.ExcelWriter(excel_file, engine='xlsxwriter') as writer:
            df.to_excel(writer, sheet_name='Data', index=False)

        # Seek to the beginning of the BytesIO object
        excel_file.seek(0)

        # Generate the filename for the Excel file
        excel_filename = file.filename.rsplit('.', 1)[0] + '.xlsx'

        # Return the Excel file as a streaming response
        return StreamingResponse(
            excel_file,
            media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            headers={
                "Content-Disposition": f"attachment; filename={excel_filename}"
            }
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"An error occurred: {str(e)}")
# endregion

# region handle missing values using mean option
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
#endregion

# region Detect missing values and return them in a bar graph
@app.post("/detect_missing_values/",
          summary="Count of missing values in Bar Graph")

async def detect_missing_values(file: UploadFile = File(...)):
    data = read_csv_file(file)
    
    # Replace empty strings with NaN
    data = data.replace(r'^\s*$', pd.NA, regex=True)
    
    # Detect missing values
    missing_values = data.isnull().sum()

    # Prepare the data for plotting
    columns = [col for col, count in zip(missing_values.index, missing_values) if count > 0]
    counts = [count for count in missing_values if count > 0]

    if not columns:
        return {"message": "No missing values found in the data."}

    # Create the bar graph
    fig, ax = plt.subplots(figsize=(12, 6))
    ax.bar(columns, counts)
    ax.set_title('Count of Missing Values by Column')
    ax.set_xlabel('Columns')
    ax.set_ylabel('Count of Missing Values')
    plt.xticks(rotation=45, ha='right')
    
    # Set y-axis to use only integer values
    ax.yaxis.set_major_locator(ticker.MaxNLocator(integer=True))
    
    # Add value labels on top of each bar
    for i, v in enumerate(counts):
        ax.text(i, v, str(v), ha='center', va='bottom')

    plt.tight_layout()

    # Save the plot to a bytes buffer
    buf = io.BytesIO()
    plt.savefig(buf, format='png')
    buf.seek(0)
    plt.close(fig)

    # Return the image as a streaming response
    return StreamingResponse(buf, media_type="image/png")
# endregion




