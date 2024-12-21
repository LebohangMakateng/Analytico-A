from fastapi import FastAPI, UploadFile, File, HTTPException
import pandas as pd
import io
from fastapi.responses import StreamingResponse
from fastapi.middleware.wsgi import WSGIMiddleware
import dash
from dash import dcc
from dash import html
from dash.dependencies import Input, Output
import io
import processManager
import pandas as pd
import base64

# Create the FastAPI app
app = FastAPI()

#RUN 'fastapi dev process.py' to start server
#FastAPI automatically generates interactive API documentation. 
# You can access it at http://127.0.0.1:8000/docs to explore your API and test the endpoints.

#docs at: https://fastapi.tiangolo.com/#check-it

# Create the Dash app
dash_app = dash.Dash(__name__, requests_pathname_prefix='/dash/')
# Define the layout of the Dash app
dash_app.layout = html.Div(children=[
    html.H1(children='Analytico'),
    dcc.Upload(
        id='upload-data',
        children=html.Button('Upload CSV File'),
        multiple=False
    ),
    html.Div(id='output-message'),
    dcc.Graph(id='missing-values-graph')
])

# Callback to update the graph based on uploaded file
@dash_app.callback(
    [Output('missing-values-graph', 'figure'),
     Output('output-message', 'children')],
    [Input('upload-data', 'contents')]
)
def update_graph(contents):
    if contents is None:
        return {}, "Please upload a CSV file to see the missing values graph."
    
    content_type, content_string = contents.split(',')
    decoded = base64.b64decode(content_string)
    try:
        # Read the uploaded CSV file into a DataFrame
        df = pd.read_csv(io.StringIO(decoded.decode('utf-8')))
    except Exception as e:
        return {}, f"Error processing file: {str(e)}"
    
    # Create the missing values graph
    imgdata, message = processManager.create_missing_values_graphUi(df)
    
    if message:
        return {}, message
    
    # Convert image data to base64 for display
    encoded_image = base64.b64encode(imgdata.getvalue()).decode()
    
    # Update the graph
    return {
        'data': [
            {
                'x': df.columns,
                'y': df.isnull().sum(),
                'type': 'bar',
                'name': 'Missing Values'
            },
        ],
        'layout': {
            'title': 'Count of Missing Values by Column'
        }
    }, "Graph of missing values in the uploaded dataset."

# Mount the Dash app on a specific route
app.mount("/dash", WSGIMiddleware(dash_app.server))

@app.get("/")
def read_root():
    return {"message": "Welcome to Analytico!"}


# FAST API Endpoints
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
            create_missing_values_graph(df, writer)
            create_outlier_graphs(df, writer)  # Add this line

        # Seek to the beginning of the BytesIO object
        excel_file.seek(0)

        # Generate the filename for the Excel file
        excel_filename = file.filename.rsplit('.', 1)[0] + '_with_summary_missing_values_and_outliers.xlsx'

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




