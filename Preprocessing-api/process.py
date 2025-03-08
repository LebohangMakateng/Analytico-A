from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.responses import StreamingResponse
from fastapi.middleware.wsgi import WSGIMiddleware
import dash
from dash import dcc, html, dash_table
from dash.dependencies import Input, Output, State
import io
import processManager
import pandas as pd
import base64
import time  # For simulating delay
import dash_bootstrap_components as dbc
from openai import OpenAI
import os

# Create the FastAPI app
app = FastAPI()

# Create the Dash app
dash_app = dash.Dash(__name__, requests_pathname_prefix='/dash/', external_stylesheets=[dbc.themes.BOOTSTRAP])
dash_app.layout = dcc.Loading(
    id="loading-full-page",
    type="default",
    fullscreen=True,  # Covers the entire page
    children=html.Div([
        # Your existing layout here
        html.H1(children='Analytico', 
            style={'textAlign': 'center', 'marginBottom': '50px'}),
    html.Div(
        dcc.Upload(
            id='upload-data',
    children=dbc.Button(
        'Upload CSV/Excel File',
        id='upload-button',
        color="primary",  # Blue background
        className="me-2",  # Margin
        style={'color': 'white'}
        ),
            multiple=False
        ),
        style={'textAlign': 'center', 'marginBottom': '50px'}  
    ), 
    html.Div(id='data-table-container', style={'textAlign': 'center','margin': '50px auto'}),  # Container for the csv DataTable
    html.Div(id='summary-table-container', style={'textAlign': 'center','margin': '50px auto'}), 
    html.Div(id='info-table-container', style={'textAlign': 'center','margin': '50px auto'}),  
    html.Div(id='outliers-graph-container', style={'textAlign': 'center','margin': '50px auto'}),
    html.Div(id='missing-values-graph-container', style={'textAlign': 'center','margin': '50px auto'}),
    dcc.Store(id='data-processed', data=False),  # Store to track if data is processed
    html.Div(
        dbc.Button(
        'Download Excel File',
        id='download-button',
        color="primary",  # Blue background
        className="me-2",  # Margin
        style={'color': 'white', 'display':'none'}
    ),
        style={
        'display': 'flex',
        'justifyContent': 'center',
        'alignItems': 'center',
        'margin': '20px auto'
    }
    ),
    dcc.Download(id='download-excel')
    ])
)

# Initialize OpenAI client
client = OpenAI(api_key=os.getenv('OPENAI_API_KEY'))

# Add this function to generate insights
def generate_data_insights(df):
    # Create a context about the data
    data_description = f"""
    This dataset contains {len(df)} rows and {len(df.columns)} columns.
    Columns: {', '.join(df.columns)}
    
    Key statistics:
    {df.describe().to_string()}
    
    Missing values:
    {df.isnull().sum().to_string()}
    """
    
    try:
        response = client.chat.completions.create(
            model="gpt-4",
            messages=[
                {"role": "system", "content": "You are a helpful data analyst assistant. Analyze the data and provide clear, actionable insights for non-technical business users."},
                {"role": "user", "content": f"Please analyze this data and provide business-friendly insights:\n{data_description}"}
            ]
        )
        return response.choices[0].message.content
    except Exception as e:
        return f"Unable to generate insights: {str(e)}"

# Callback to update the table and graph based on uploaded file# Callback to update the table and graph based on uploaded file
# Modify the update_output callback to include AI insights
@dash_app.callback(
    [Output('data-table-container', 'children'),
     Output('missing-values-graph-container', 'children'),
     Output('outliers-graph-container', 'children'),
     Output('summary-table-container', 'children'),
     Output('info-table-container', 'children'),
     Output('ai-insights-container', 'children'),  # New output
     Output('data-processed', 'data')],
    [Input('upload-data', 'contents')],
    [State('upload-data', 'filename')]
)
def update_output(contents, filename):
    if contents is None:
        return (html.Div("Please Upload data :)",
                         style={'textAlign': 'center',
                                'fontWeight': 'bold',
                                'fontSize': '20px',
                                'marginBottom': '10px'}), 
                None, None, None, False)
    
     # Simulate a delay (e.g., data processing)
    time.sleep(2)  # Delay for 5 seconds

    content_type, content_string = contents.split(',')
    decoded = base64.b64decode(content_string)
    try:
        if filename.endswith('.csv'):
            df = pd.read_csv(io.StringIO(decoded.decode('utf-8')))
        elif filename.endswith('.xlsx') or filename.endswith('.xls'):
            df = pd.read_excel(io.BytesIO(decoded))
        else:
            return "Unsupported file format."
    except Exception as e:
        return html.Div(f"Error processing file: {str(e)}"), None, None, None, False

    # Create a DataTable for the uploaded data
    data_table = dash_table.DataTable(
        data=df.to_dict('records'),
        columns=[{'name': col, 'id': col} for col in df.columns],
        page_size=10,  # Adjust the number of rows per page
        style_table={'overflowX': 'auto'},
        style_cell={'textAlign': 'left'},
    )

    # Add the filename as a title above the data table
    uploaded_data_table = html.Div([
        html.H3(f"Data Table: {filename}", style={'textAlign': 'center', 'marginBottom':'5px'}),
        data_table
    ], 
    style= card_style
    )
    html.Div(id='ai-insights-container', style={'textAlign': 'center', 'margin': '50px auto'}),
    # Check if the DataFrame is empty or has no missing values
    if df.empty or df.isnull().sum().sum() == 0:
        graph = html.Div("No missing values found in the uploaded file.",
                         style={'textAlign': 'center',
                                'fontWeight': 'bold',
                                'fontSize': '20px',
                                'marginBottom': '10px'})
    else:
        # Generate the graph for missing values
        graph = dcc.Graph(
            figure=processManager.create_missing_values_graph(df), style= card_style
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
        summary_table_content = processManager.generate_data_table(summary_df)

         # Generate the graph for missing values
        outliers_graph = dcc.Graph(
            figure=processManager.create_outliers_graph(numerical_df), style= card_style
        )

        # Add the title for the summary table
        summary_table = html.Div([
            html.H3("Numerical Data Summary Table", style={'textAlign': 'center','marginBottom':'0px'}),
            summary_table_content
        ], style= card_style)

    # Capture the df.info() output
    buffer = io.StringIO()
    df.info(buf=buffer)
    info_str = buffer.getvalue()

    # Display the df.info() output
    info_output = html.Div([
        html.H3("Info() Data Summary Table", style={'textAlign': 'center','marginBottom':'0px'}),
        html.Pre(info_str, style={'whiteSpace': 'pre-wrap', 'overflowX': 'auto'})
    ], style= card_style) 

    # Generate AI insights
    insights = generate_data_insights(df)
    insights_output = html.Div([
        html.H3("AI-Powered Insights", style={'textAlign': 'center', 'marginBottom': '10px'}),
        html.Div([
            html.P(insight, style={'marginBottom': '10px'}) 
            for insight in insights.split('\n') if insight.strip()
        ])
    ], style=card_style)
    # Add this near other layout components
    html.Div([
        dbc.Input(
            id='natural-language-query',
            type='text',
            placeholder='Ask questions about your data (e.g., "What are the top selling products?" or "Show me unusual patterns")',
            style={'marginBottom': '10px', 'width': '100%'}
        ),
        dbc.Button('Ask Question', id='query-button', color='primary', className='me-2')
    ], style={'width': '90%', 'margin': '20px auto'}),
    html.Div(id='query-result-container', style={'textAlign': 'center', 'margin': '20px auto'}),
    
    # Add this callback for handling natural language queries
    @dash_app.callback(
        Output('query-result-container', 'children'),
        [Input('query-button', 'n_clicks')],
        [State('natural-language-query', 'value'),
         State('upload-data', 'contents')]
    )
    def handle_query(n_clicks, query, contents):
        if not n_clicks or not query or not contents:
            return None
        
        # Process the uploaded data
        content_type, content_string = contents.split(',')
        decoded = base64.b64decode(content_string)
        df = pd.read_csv(io.StringIO(decoded.decode('utf-8')))
        
        try:
            response = client.chat.completions.create(
                model="gpt-4",
                messages=[
                    {"role": "system", "content": "You are a data analyst. Analyze the data and answer questions in simple business terms."},
                    {"role": "user", "content": f"Data:\n{df.head(10)}\n\nQuestion: {query}"}
                ]
            )
            
            return html.Div([
                html.H4("Answer", style={'marginBottom': '10px'}),
                html.P(response.choices[0].message.content)
            ], style=card_style)
        except Exception as e:
            return html.Div(f"Error processing query: {str(e)}", style=card_style)
    return uploaded_data_table, graph, outliers_graph, summary_table, info_output, insights_output, True

# Callback to show the download button only after data is processed
@dash_app.callback(
    Output('download-button', 'style'),
    [Input('data-processed', 'data')]
)
def toggle_download_button(data_processed):
    if data_processed:
        return {'display': 'block'}
    return {'display': 'none'}

# Callback to handle the download button click
@dash_app.callback(
    Output('download-excel', 'data'),
    [Input('download-button', 'n_clicks')],
    [State('upload-data', 'contents'), State('upload-data', 'filename')]
)
def download_excel(n_clicks, contents, filename):
    if n_clicks > 0 and contents is not None:
        content_type, content_string = contents.split(',')
        decoded = base64.b64decode(content_string)
        df = pd.read_csv(io.StringIO(decoded.decode('utf-8')))

        # Create a BytesIO object to store the Excel file
        excel_file = io.BytesIO()

        # Write the DataFrame and its description to the Excel file
        with pd.ExcelWriter(excel_file, engine='xlsxwriter') as writer:
            processManager.create_data_sheet(df, writer)
            processManager.create_summary_sheet(df, writer)
            processManager.create_missing_values_graph_excel(df, writer)

        # Seek to the beginning of the BytesIO object
        excel_file.seek(0)

        # Generate the filename for the Excel file
        excel_filename = filename.rsplit('.', 1)[0] + '_preprocessed.xlsx'

        return dcc.send_bytes(excel_file.getvalue(), filename=excel_filename)

    return None

# Mount the Dash app on a specific route
app.mount("/dash", WSGIMiddleware(dash_app.server))

@app.get("/")
def read_root():
    return {"message": "Welcome to Analytico!"}

# FastAPI endpoint for CSV to Excel conversion
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
            processManager.create_missing_values_graph_excel(df, writer)

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
    
# Define the card style
card_style = {
    'border': '1px solid #ddd',
    'border-radius': '10px',
    'box-shadow': '0 4px 8px rgba(0, 0, 0, 0.2)',
    'padding': '20px',
    'background-color': '#fff',
    'margin': '20px auto',
    'width': '90%',
}