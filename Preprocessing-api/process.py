from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.responses import StreamingResponse
from fastapi.middleware.wsgi import WSGIMiddleware
import dash
from dash import dcc, html
from dash.dependencies import Input, Output, State
import io
import processManager
import pandas as pd
import base64

# Create the FastAPI app
app = FastAPI()

# Create the Dash app
dash_app = dash.Dash(__name__, requests_pathname_prefix='/dash/')

# Define the layout of the Dash app
dash_app.layout = html.Div(children=[
    html.H1(children='Analytico', 
            style={'textAlign': 'center', 'marginBottom': '50px'}),
    html.Div(
        dcc.Upload(
            id='upload-data',
            children=html.Button('Upload CSV File'),
            multiple=False
        ),
        style={'textAlign': 'center', 'marginBottom': '50px'}  
    ), 
    html.Div(id='summary-table-container'),  
    html.Div(id='missing-values-graph-container', style={'width': '60%','textAlign': 'center','margin': '0 auto'})  # Center the div horizontally})  # Placeholder for the graph
])

# Callback to update the table and graph based on uploaded file@dash_app.callback(
@dash_app.callback(
    [Output('missing-values-graph-container', 'children'),
     Output('summary-table-container', 'children')],
    [Input('upload-data', 'contents')],
    [State('upload-data', 'filename')]
)
def update_output(contents, filename):
    if contents is None:
        return html.Div("Please Upload data :)",
                        style={'textAlign': 'center',
                               'fontWeight': 'bold',
                               'fontSize': '20px',
                               'marginBottom': '10px'}), None

    content_type, content_string = contents.split(',')
    decoded = base64.b64decode(content_string)
    try:
        df = pd.read_csv(io.StringIO(decoded.decode('utf-8')))
    except Exception as e:
        return html.Div(f"Error processing file: {str(e)}"), None

    # Generate the graph for missing values
    graph = dcc.Graph(
        figure=processManager.create_missing_values_graph(df)
    )

    # Filter numerical columns
    numerical_df = df.select_dtypes(include=['number'])

    # Check if numerical_df is empty
    if numerical_df.empty:
        summary_table = html.Div("No numerical columns found in the uploaded file.",
                                 style={'textAlign': 'center',
                                        'fontWeight': 'bold',
                                        'fontSize': '20px',
                                        'marginBottom': '10px'})
    else:
        # Create the summary table for numerical columns
        summary_df = processManager.create_summary_dataframe(numerical_df)
        summary_table = processManager.generate_html_table(summary_df)

    return graph, summary_table

# Mount the Dash app on a specific route
app.mount("/dash", WSGIMiddleware(dash_app.server))

@app.get("/")
def read_root():
    return {"message": "Welcome to Analytico!"}

#Region FAST API Endpoints
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
#endregion