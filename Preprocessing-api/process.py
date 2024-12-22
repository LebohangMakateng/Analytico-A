from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.responses import StreamingResponse
from fastapi.middleware.wsgi import WSGIMiddleware
import dash
from dash import dcc, html
from dash.dependencies import Input, Output
import io
import processManager
import pandas as pd
import base64

# Create the FastAPI app
app = FastAPI()

# Create the Dash app
dash_app = dash.Dash(__name__, requests_pathname_prefix='/dash/')

# Function to create the summary DataFrame
def create_summary_dataframe(df: pd.DataFrame) -> pd.DataFrame:
    summary_df = df.describe().T
    summary_df.reset_index(inplace=True)
    summary_df.rename(columns={'index': 'Metric'}, inplace=True)
    return summary_df

# Function to generate an HTML table from a DataFrame
def generate_html_table(df: pd.DataFrame) -> html.Table:
    """
    Generate an HTML table from a DataFrame with horizontal and vertical borders.
    """
    table_header = [
        html.Tr(
            [html.Th(col, style={'border': '1px solid black', 'padding': '5px', 'textAlign': 'center'}) for col in df.columns]
        )
    ]
    table_body = [
        html.Tr(
            [
                html.Td(df.iloc[i][col], style={'border': '1px solid black', 'padding': '5px', 'textAlign': 'center'})
                for col in df.columns
            ]
        )
        for i in range(len(df))
    ]

    return html.Table(
        children=table_header + table_body,
        style={
            'padding-top':'5px',
            'width': '80%',
            'margin': '15px',
            'border': '1px solid black',
            'borderCollapse': 'collapse',  # Ensures borders don't double up
        },
        className='summary-table'
    )


# Function to generate the missing values graph
def create_missing_values_graph(df: pd.DataFrame) -> dict:
    """
    Generate a bar graph showing the count of missing values for each column.
    """
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
    }

# Define the layout of the Dash app
dash_app.layout = html.Div(children=[
    html.H1(children='Analytico'),
    dcc.Upload(
        id='upload-data',
        children=html.Button('Upload CSV File'),
        multiple=False
    ),
    html.Div(id='output-message'),
    html.Div(id='summary-table-container'),  # Container for the summary table
    dcc.Graph(id='missing-values-graph')  # The bar graph
])

# Callback to update the table and graph based on uploaded file
@dash_app.callback(
    [
        Output('missing-values-graph', 'figure'),
        Output('output-message', 'children'),
        Output('summary-table-container', 'children')  # For the table
    ],
    [Input('upload-data', 'contents')]
)
def update_graph_and_table(contents):
    if contents is None:
        return {}, "Please upload a CSV file to see the missing values graph and table.", html.Div()

    content_type, content_string = contents.split(',')
    decoded = base64.b64decode(content_string)
    try:
        # Read the uploaded CSV file into a DataFrame
        df = pd.read_csv(io.StringIO(decoded.decode('utf-8')))
    except Exception as e:
        return {}, f"Error processing file: {str(e)}", html.Div()

    # Create the summary table
    summary_df = create_summary_dataframe(df)
    table = generate_html_table(summary_df)

    # Generate the graph
    graph_figure = create_missing_values_graph(df)

    return graph_figure, "Graph of missing values in the uploaded dataset.", table

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




