from fastapi import FastAPI
from fastapi import FastAPI, UploadFile, File, HTTPException
import pandas as pd
import io
from fastapi.responses import StreamingResponse
import matplotlib.pyplot as plt
import matplotlib.ticker as ticker

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