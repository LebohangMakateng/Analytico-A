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
import json
import numpy as np

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

def generate_info_table(df):
    buffer = StringIO()
    buffer.write(f"<class 'pandas.core.frame.DataFrame'>\n")
    buffer.write(f"RangeIndex: {len(df)} entries, 0 to {len(df)-1}\n")
    buffer.write(f"Data columns (total {len(df.columns)} columns):\n")
    buffer.write(" #   Column    Non-Null Count  Dtype  \n")
    buffer.write("---  ------    --------------  -----  \n")
    
    for i, col in enumerate(df.columns):
        dtype = df[col].dtype
        non_null_count = df[col].count()
        buffer.write(f" {i:2}  {col:<10} {non_null_count:5} non-null  {dtype}\n")
    
    buffer.write(f"\ndtypes: {', '.join([f'{dtype}({sum(df.dtypes==dtype)})' for dtype in df.dtypes.unique()])}\n")
    memory_usage = df.memory_usage(deep=True).sum()
    buffer.write(f"memory usage: {memory_usage / 1024**2:.2f}+ MB\n")
    
    return buffer.getvalue()

@app.post("/data_info/")
async def return_data_info(file: UploadFile = File(...)):
    try:
        # Read the CSV file
        contents = await file.read()
        data = pd.read_csv(io.StringIO(contents.decode('utf-8')))

        # Generate the info table
        info_table = generate_info_table(data)

        # Return the info table as plain text
        return PlainTextResponse(content=info_table)

    except Exception as e:
        return PlainTextResponse(content=f"An error occurred: {str(e)}", status_code=500)

# Set up Jinja2 templates
templates = Jinja2Templates(directory="templates")

@app.post("/display_csv_data_html/")
async def display_csv_data(
    request: Request,
    file: UploadFile = File(...),
    page: int = Query(1, description="Page number", ge=1),
    rows_per_page: int = Query(10, description="Rows per page", ge=1, le=100)
):
    if not file.filename.endswith('.csv'):
        raise HTTPException(status_code=400, detail="Only CSV files are allowed")

    try:
        contents = await file.read()
        data = pd.read_csv(io.StringIO(contents.decode('utf-8')))

        # Calculate pagination
        total_rows = len(data)
        total_pages = math.ceil(total_rows / rows_per_page)
        start_row = (page - 1) * rows_per_page
        end_row = start_row + rows_per_page

        # Get the data for the current page
        page_data = data.iloc[start_row:end_row]

        # Convert the DataFrame to an HTML table
        html_table = page_data.to_html(classes=['table', 'table-striped', 'table-hover'], index=False)

        # Prepare context for the template
        context = {
            "request": request,
            "table": html_table,
            "page": page,
            "total_pages": total_pages,
            "rows_per_page": rows_per_page,
            "start_row": start_row + 1,
            "end_row": min(end_row, total_rows),
            "total_rows": total_rows
        }

        # Render the template
        return templates.TemplateResponse("csv_display.html", context)

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"An error occurred: {str(e)}")

    
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