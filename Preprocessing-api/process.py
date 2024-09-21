from fastapi import FastAPI, UploadFile, File, HTTPException
import pandas as pd
import io
from fastapi.responses import StreamingResponse
import matplotlib.pyplot as plt
import matplotlib.ticker as ticker

app = FastAPI()

#FastAPI automatically generates interactive API documentation. 
# You can access it at http://127.0.0.1:8000/docs to explore your API and test the endpoints.

# region csv to excel
@app.post("/csv_to_excel_with_description/")
async def csv_to_excel_with_description(file: UploadFile = File(...)):
    if not file.filename.endswith('.csv'):
        raise HTTPException(status_code=400, detail="Only CSV files are allowed")

    try:
        contents = await file.read()
        df = pd.read_csv(io.StringIO(contents.decode('utf-8')))

        # Create a BytesIO object to store the Excel file
        excel_file = io.BytesIO()

        # Write the DataFrame and its description to the Excel file
        with pd.ExcelWriter(excel_file, engine='xlsxwriter') as writer:
            create_data_sheet(df, writer)
            create_summary_sheet(df, writer)

        # Seek to the beginning of the BytesIO object
        excel_file.seek(0)

        # Generate the filename for the Excel file
        excel_filename = file.filename.rsplit('.', 1)[0] + '_with_summary.xlsx'

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

def create_data_sheet(df: pd.DataFrame, writer: pd.ExcelWriter) -> None:
    """
    Create the 'Data' sheet with the full dataset and adjust column widths.
    """
    df.to_excel(writer, sheet_name='Data', index=False)
    worksheet = writer.sheets['Data']
    
    for i, col in enumerate(df.columns):
        max_len = max(
            df[col].astype(str).map(len).max(),  # max length of column data
            len(str(col))  # length of column name
        )
        worksheet.set_column(i, i, max_len + 2)  # Add a little extra space

def create_summary_sheet(df: pd.DataFrame, writer: pd.ExcelWriter) -> None:
    """
    Create the 'Summary' sheet with descriptive statistics and adjust column widths.
    """
    summary_df = df.describe().T
    summary_df.to_excel(writer, sheet_name='Summary')
    worksheet = writer.sheets['Summary']
    
    for i, col in enumerate(summary_df.columns):
        max_len = max(
            summary_df[col].astype(str).map(len).max(),  # max length of column data
            len(str(col))  # length of column name
        )
        worksheet.set_column(i, i, max_len + 2)  # Add a little extra space
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




