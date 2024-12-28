 #This file is used to handle the logic/business rules for the process.py script.
import io
import matplotlib.pyplot as plt
import matplotlib.ticker as ticker
from typing import Dict
import pandas as pd
from dash import dcc, html

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

def create_missing_values_graph(df: pd.DataFrame, writer: pd.ExcelWriter) -> None:
    """
    Create a 'Missing Values' sheet with a bar graph of missing values.
    """
    # Replace empty strings with NaN
    df = df.replace(r'^\s*$', pd.NA, regex=True)
    
    # Detect missing values
    missing_values = df.isnull().sum()

    # Prepare the data for plotting
    columns = [col for col, count in zip(missing_values.index, missing_values) if count > 0]
    counts = [count for count in missing_values if count > 0]

    if not columns:
        worksheet = writer.book.add_worksheet('Missing Values')
        worksheet.write('A1', 'No missing values found in the data.')
        return

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

    # Save the plot to the Excel file
    imgdata = io.BytesIO()
    fig.savefig(imgdata, format='png')
    worksheet = writer.book.add_worksheet('Missing Values')
    worksheet.insert_image('A1', '', {'image_data': imgdata})

    plt.close(fig)

def detect_outliers(df: pd.DataFrame) -> Dict[str, int]:
    numeric_features = df.select_dtypes(include=['float', 'int']).columns
    outliers = {}
    for feature in numeric_features:
        Q1 = df[feature].quantile(0.25)
        Q3 = df[feature].quantile(0.75)
        IQR = Q3 - Q1
        lower_bound = Q1 - (1.5 * IQR)
        upper_bound = Q3 + (1.5 * IQR)
        outliers[feature] = ((df[feature] < lower_bound) | (df[feature] > upper_bound)).sum()
    return outliers

# Function to create missing values graph
def create_missing_values_graphUi(df: pd.DataFrame):
    # Replace empty strings with NaN
    df = df.replace(r'^\s*$', pd.NA, regex=True)
    
    # Detect missing values
    missing_values = df.isnull().sum()
    
    # Prepare the data for plotting
    columns = [col for col, count in zip(missing_values.index, missing_values) if count > 0]
    counts = [count for count in missing_values if count > 0]
    
    if not columns:
        return None, "No missing values found in the data."
    
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
    
    # Convert plot to image data
    imgdata = io.BytesIO()
    fig.savefig(imgdata, format='png')
    imgdata.seek(0)
    
    plt.close(fig)
    
    return imgdata, None

def create_summary_dataframeUi(df: pd.DataFrame) -> pd.DataFrame:
    """
    Create a summary DataFrame with descriptive statistics.
    """
    summary_df = df.describe().T  # Transpose to match the format
    summary_df.reset_index(inplace=True)  # Reset index to make 'index' a column
    summary_df.rename(columns={'index': 'Metric'}, inplace=True)  # Rename index column
    return summary_df

# region: Private methods

# Function to create the summary DataFrame
def create_summary_dataframe(df: pd.DataFrame) -> pd.DataFrame:
    summary_df = df.describe().T
    summary_df.reset_index(inplace=True)
    summary_df.rename(columns={'index': 'Metric'}, inplace=True)
    return summary_df

import dash_table


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
