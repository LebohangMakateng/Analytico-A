from fastapi import FastAPI, UploadFile, File, HTTPException
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
            processManager.create_data_sheet(df, writer)
            processManager.create_summary_sheet(df, writer)
            processManager.create_missing_values_graph(df, writer)
            processManager.create_outlier_graphs(df, writer)  # Add this line

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




