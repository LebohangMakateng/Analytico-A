 #This file is used to handle the logic/business rules for the process.py script.
import io
import matplotlib.pyplot as plt
import matplotlib.ticker as ticker
from typing import Dict
import pandas as pd
from dash import dash_table
import plotly.graph_objs as go

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

#excel
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

# Function to create the summary DataFrame'
#UI
def create_summary_dataframe(df: pd.DataFrame) -> pd.DataFrame:
    summary_df = df.describe().T
    summary_df.reset_index(inplace=True)
    summary_df.rename(columns={'index': 'Metric'}, inplace=True)
    return summary_df

##Function to Generate a Dash DataTable from a DataFrame.
def generate_data_table(df: pd.DataFrame) -> dash_table.DataTable:
    """
    Generate a Dash DataTable from a DataFrame.
    """
    return dash_table.DataTable(
        data=df.to_dict('records'),
        columns=[{'name': col, 'id': col} for col in df.columns],
        style_table={'overflowX': 'auto', 'margin': '15px auto', 'width': '60%'},
        style_cell={'textAlign': 'center', 'padding': '5px'},
        style_header={'fontWeight': 'bold'},
        page_size=10  # Adjust the number of rows per page
    )

# Function to generate the missing values graph
def create_missing_values_graph(df: pd.DataFrame) -> go.Figure:
    """
    Generate a Plotly bar graph showing the count of missing values for each column.
    """
    missing_counts = df.isnull().sum()

    # Create a bar chart using Plotly
    fig = go.Figure(data=[
        go.Bar(
            x=df.columns,
            y=missing_counts,
            name='Missing Values'
        )
    ])

    # Update layout to ensure Y-axis uses integer values and set background to white
    fig.update_layout(
        title='Count of Missing Values by Column',
        yaxis=dict(
            tickmode='linear',
            tick0=0,
            dtick=1  # Ensures the Y-axis uses integer values
        ),
        plot_bgcolor='white',  # Set plot background to white
        paper_bgcolor='white'  # Set paper background to white
    )

    return fig

def create_missing_values_graph_excel(df: pd.DataFrame, writer: pd.ExcelWriter) -> None:
    """
    Create a 'Missing Values' sheet with a bar graph of missing values in an Excel file.
    """
    # Your existing code for creating a graph and inserting it into an Excel sheet
    df = df.replace(r'^\s*$', pd.NA, regex=True)
    missing_values = df.isnull().sum()
    columns = [col for col, count in zip(missing_values.index, missing_values) if count > 0]
    counts = [count for count in missing_values if count > 0]

    if not columns:
        worksheet = writer.book.add_worksheet('Missing Values')
        worksheet.write('A1', 'No missing values found in the data.')
        return

    fig, ax = plt.subplots(figsize=(12, 6))
    ax.bar(columns, counts)
    ax.set_title('Count of Missing Values by Column')
    ax.set_xlabel('Columns')
    ax.set_ylabel('Count of Missing Values')
    plt.xticks(rotation=45, ha='right')
    ax.yaxis.set_major_locator(ticker.MaxNLocator(integer=True))
    for i, v in enumerate(counts):
        ax.text(i, v, str(v), ha='center', va='bottom')
    plt.tight_layout()

    imgdata = io.BytesIO()
    fig.savefig(imgdata, format='png')
    worksheet = writer.book.add_worksheet('Missing Values')
    worksheet.insert_image('A1', '', {'image_data': imgdata})

    plt.close(fig)

#TODO:
## Missing value imputation refers to replacing missing data with substituted values in a dataset.
## Handling Missing Values using mode or a special category for categorical features
## https://chatgpt.com/share/6771b52a-d5fc-800a-ba5c-069df7d3ff53
## You can automate this handling for multiple categorical features in a dataset:
##Example:
# Replace missing values in all categorical columns
##for column in df.select_dtypes(include=['object', 'category']).columns:
##    # Replace with mode or a special category
##    df[column].fillna(df[column].mode()[0], inplace=True)  # Using mode
    # df[column].fillna('Missing', inplace=True)           # Using a special category
##This approach works efficiently for datasets with many categorical features.