'''# Task:
1. Load your csvs into this notebook.
2. Clean the files.
3. Output them as clean csvs.

Stretch:
1. Add some data engineering metrics you want to track (e.g. how many rows tracked)
2. Output the files to local SSMS database with the DE metrics.
3. Put this into a Python script that can be run on demand '''
import pandas as pd
import argparse
from datetime import datetime
import urllib.parse
import pyodbc
from sqlalchemy import create_engine

def convert_blanks(df: pd.DataFrame) -> pd.DataFrame:
    # Replace blank strings with pandas NA for accurate metric calculations.
    return df.replace(r'^\s*$', pd.NA, regex=True)

def drop_duplicates_and_na(df: pd.DataFrame, subset: list) -> pd.DataFrame:
    # Drop duplicate rows.
    df = df.drop_duplicates()
    # Drop rows where all values in the subset are missing.
    df = df.dropna(subset=subset, how='all')
    return df

def drop_na_required_columns(df: pd.DataFrame, required_columns: list) -> pd.DataFrame:
    # Drop rows where any of the required columns are missing. (e.g. Customer ID, Books, Book Checkout)
    df = df.dropna(subset=required_columns)
    return df

def Check_Customer_Ids(df: pd.DataFrame, customer_df: pd.DataFrame) -> pd.DataFrame:
    # Keep only rows where the Customer ID exists in the customer table.
    df = df[df['Customer ID'].isin(customer_df['Customer ID'])]
    return df

def convert_to_int(df: pd.DataFrame, column_name: str) -> pd.DataFrame:
    # Convert the specified column to integer.
    df[column_name] = df[column_name].astype(int)
    return df

def strip_quotes(df: pd.DataFrame, column_name: str) -> pd.DataFrame:
    # Strip quotes from the specified column.
    df[column_name] = df[column_name].astype(str).str.replace('"', '', regex=False)
    return df

def Convert_to_datetime(df: pd.DataFrame, column_name: str) -> pd.DataFrame:
    # Pass the specified column as datetime and coercing errors to NaT.
    df[column_name] = pd.to_datetime(df[column_name], errors='coerce', dayfirst=True)
    return df

def convert_to_strings(df: pd.DataFrame, column_name: str) -> pd.DataFrame:
    # Convert the specified column to string.
    df[column_name] = df[column_name].astype(str)
    return df

def convert_xweeks_to_no_days(df: pd.DataFrame, column_name: str) -> pd.DataFrame:
    # Convert "x weeks" to number of days in the specified column.
    df[column_name] = df[column_name].apply(lambda x: int(x.split()[0]) * 7 ##first value is number times this by 7
                                                           if isinstance(x, str) and 'week' in x else x) ##as long as it is a string and contains week, otherwise return original value
    return df
##check dates checkout not after returned, if so set to NA
def check_checkout_not_after_returned(df: pd.DataFrame) -> pd.DataFrame:
    # If Book checkout is after Book Returned, set Book checkout to NA.
    df.loc[df['Book checkout'] > df['Book Returned'], 'Book checkout'] = pd.NA
    return df

def if__date_invalid_infer_checkout(df: pd.DataFrame) -> pd.DataFrame:
    # If Book checkout is missing, infer it from Book Returned minus allowed loan days.
    df['Book checkout'] = df['Book checkout'].fillna(
        df['Book Returned'] - pd.to_timedelta(df['Days allowed to borrow'], unit='D'))
    return df

##Enrich data by adding column to calculate Days borrowed and add this in []
def calculate_days_borrowed(df: pd.DataFrame) -> pd.DataFrame:
    #calculate the number of days a book was borrowed by subtracting the checkout date from the returned date
    df['Days Borrowed'] = (df['Book Returned'] - df['Book checkout']).dt.days
    return df



def calculate_metrics(raw_books: pd.DataFrame, raw_customers: pd.DataFrame, cleaned_books: pd.DataFrame, cleaned_customers: pd.DataFrame) -> pd.DataFrame:
    # Convert blanks to NA for accurate checks.
    raw_books = convert_blanks(raw_books.copy())
    raw_customers = convert_blanks(raw_customers.copy())

    # Identify rows where the book Customer ID does not exist in the customers file.
    rows_customer_not_found = int(
        (~raw_books['Customer ID'].dropna().astype(int).isin(raw_customers['Customer ID'].dropna().astype(int))).sum()
    )
    # Count duplicate rows in the raw data.
    book_duplicates_removed = int(raw_books.duplicated().sum())
    customer_duplicates_removed = int(raw_customers.duplicated().sum())

    # Parse the raw date columns for invalid date counting.
    book_checkout_raw = raw_books['Book checkout'].astype(str).str.replace('"', '', regex=False)
    book_returned_raw = raw_books['Book Returned'].astype(str).str.replace('"', '', regex=False)
    book_checkout_parsed = pd.to_datetime(book_checkout_raw, errors='coerce', dayfirst=True)
    book_returned_parsed = pd.to_datetime(book_returned_raw, errors='coerce', dayfirst=True)

    invalid_checkout_count = int(raw_books['Book checkout'].notna().sum() - book_checkout_parsed.notna().sum())
    invalid_returned_count = int(raw_books['Book Returned'].notna().sum() - book_returned_parsed.notna().sum())
    invalid_date_total = invalid_checkout_count + invalid_returned_count

    # Calculate outliers for loan duration using IQR.
    loan_duration_days = (book_returned_parsed - book_checkout_parsed).dt.days.dropna()
    if len(loan_duration_days) > 0:
        q1 = loan_duration_days.quantile(0.25)
        q3 = loan_duration_days.quantile(0.75)
        iqr = q3 - q1
        lower = q1 - 1.5 * iqr
        upper = q3 + 1.5 * iqr
        outlier_count = int(((loan_duration_days < lower) | (loan_duration_days > upper)).sum())
    else:
        outlier_count = 0

    summary_rows = [
        {'metric_group': 'drop_counts', 'dataset': 'SystemBook', 'column': '', 'metric_name': 'RowsDropped', 'value': raw_books.shape[0] - cleaned_books.shape[0]},
        {'metric_group': 'drop_counts', 'dataset': 'SystemBook', 'column': '', 'metric_name': 'ColsDropped', 'value': raw_books.shape[1] - cleaned_books.shape[1]},
        {'metric_group': 'drop_counts', 'dataset': 'SystemCustomers', 'column': '', 'metric_name': 'RowsDropped', 'value': raw_customers.shape[0] - cleaned_customers.shape[0]},
        {'metric_group': 'drop_counts', 'dataset': 'SystemCustomers', 'column': '', 'metric_name': 'ColsDropped', 'value': raw_customers.shape[1] - cleaned_customers.shape[1]},
        {'metric_group': 'referential_integrity', 'dataset': 'SystemBook', 'column': 'Customer ID', 'metric_name': 'RowsCustomerNotFound', 'value': rows_customer_not_found},
        {'metric_group': 'duplicates', 'dataset': 'SystemBook', 'column': '', 'metric_name': 'DuplicateRowsRemoved', 'value': book_duplicates_removed},
        {'metric_group': 'duplicates', 'dataset': 'SystemCustomers', 'column': '', 'metric_name': 'DuplicateRowsRemoved', 'value': customer_duplicates_removed},
        {'metric_group': 'invalid_dates', 'dataset': 'SystemBook', 'column': 'Book checkout', 'metric_name': 'InvalidDateCount', 'value': invalid_checkout_count},
        {'metric_group': 'invalid_dates', 'dataset': 'SystemBook', 'column': 'Book Returned', 'metric_name': 'InvalidDateCount', 'value': invalid_returned_count},
        {'metric_group': 'invalid_dates', 'dataset': 'SystemBook', 'column': '', 'metric_name': 'InvalidDateTotal', 'value': invalid_date_total},
        {'metric_group': 'outliers', 'dataset': 'SystemBook', 'column': 'loan_duration_days', 'metric_name': 'IQR_OutlierCount', 'value': outlier_count},
    ]

    return pd.DataFrame(summary_rows)


def load_to_sql_server(books_df: pd.DataFrame, customers_df: pd.DataFrame, metrics_df: pd.DataFrame) -> None:
    # SQL DB connection details.
    SERVER = "localhost"
    DRIVER = "ODBC Driver 17 for SQL Server"
    DATABASE = "DataEngineeringMod5_NiroshsLibrary"  # Change this if you want a different database name

    # Create database if it does not exist.
    master_conn = pyodbc.connect(
        f"DRIVER={{{DRIVER}}};SERVER={SERVER};DATABASE=master;Trusted_Connection=yes;",
        autocommit=True,
    )
    master_conn.cursor().execute(
        f"IF DB_ID(N'{DATABASE}') IS NULL CREATE DATABASE [{DATABASE}]"
    )
    master_conn.close()

    # Connect to database via SQLAlchemy
    params = urllib.parse.quote_plus(
        f"DRIVER={{{DRIVER}}};SERVER={SERVER};DATABASE={DATABASE};Trusted_Connection=yes;"
    )
    engine = create_engine(f"mssql+pyodbc:///?odbc_connect={params}")

    # Prepare dataframes for SQL loading
    books_to_load = books_df.copy()
    customers_to_load = customers_df.copy()
    metrics_to_load = metrics_df.copy()

    run_timestamp = datetime.now()
    books_to_load["load_timestamp"] = run_timestamp
    customers_to_load["load_timestamp"] = run_timestamp
    metrics_to_load["load_timestamp"] = run_timestamp

    # Load to SQL tables.
    books_to_load.to_sql("fact_books_clean", con=engine, if_exists="replace", index=False)
    customers_to_load.to_sql("dim_customers_clean", con=engine, if_exists="replace", index=False)
    metrics_to_load.to_sql("etl_metrics", con=engine, if_exists="replace", index=False)

    print('SQL Server load complete')
    print(f'Server: {SERVER}')
    print(f'Database: {DATABASE}')
    print('Tables: fact_books_clean, dim_customers_clean, etl_metrics')


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description='Clean library CSVs and optionally load to SQL Server.')
    parser.add_argument(
        '--load-to-sql',
        action='store_true',
        help='Load cleaned data and metrics into local SQL Server.',
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()

    # Load raw CSV files.
    raw_books = pd.read_csv('03_Library Systembook.csv')
    raw_customers = pd.read_csv('03_Library SystemCustomers.csv')

    # Clean customers first — needed as a reference for book customer ID checks.
    cleaned_customers = convert_blanks(raw_customers.copy())
    cleaned_customers = drop_duplicates_and_na(cleaned_customers, subset=['Customer ID', 'Customer Name'])
    cleaned_customers = convert_to_int(cleaned_customers, 'Customer ID')
    cleaned_customers = convert_to_strings(cleaned_customers, 'Customer Name')

    # Clean books using the helper functions, passing the cleaned customers for ID validation.
    cleaned_books = convert_blanks(raw_books.copy())
    cleaned_books = drop_duplicates_and_na(cleaned_books, subset=['Customer ID', 'Books', 'Book checkout'])
    cleaned_books = drop_na_required_columns(cleaned_books, ['Customer ID', 'Books', 'Book checkout'])
    cleaned_books = Check_Customer_Ids(cleaned_books, cleaned_customers)
    cleaned_books = convert_to_int(cleaned_books, 'Customer ID')
    cleaned_books = convert_to_int(cleaned_books, 'Id')
    cleaned_books = convert_to_strings(cleaned_books, 'Books')
    cleaned_books = strip_quotes(cleaned_books, 'Book checkout')
    cleaned_books = Convert_to_datetime(cleaned_books, 'Book checkout')
    cleaned_books = strip_quotes(cleaned_books, 'Book Returned')
    cleaned_books = Convert_to_datetime(cleaned_books, 'Book Returned')
    cleaned_books = convert_xweeks_to_no_days(cleaned_books, 'Days allowed to borrow')
    cleaned_books = check_checkout_not_after_returned(cleaned_books)
    cleaned_books = if__date_invalid_infer_checkout(cleaned_books)

    # Enrich with calculated days borrowed.
    cleaned_books = calculate_days_borrowed(cleaned_books)


    # Write the cleaned CSV outputs.
    cleaned_books.to_csv('03_Library Systembook Cleaned.csv', index=False)
    cleaned_customers.to_csv('03_Library SystemCustomers Cleaned.csv', index=False)

    # Calculate data engineering metrics for the transformation.
    metrics = calculate_metrics(raw_books, raw_customers, cleaned_books, cleaned_customers)
    metrics.to_csv('transformation_metrics_all.csv', index=False)

    # Load the cleaned data and metrics into local SQL Server (optional).
    if args.load_to_sql:
        load_to_sql_server(cleaned_books, cleaned_customers, metrics)
    else:
        print('Skipped SQL Server load. Use --load-to-sql to enable it.')

    # Print summary info.
    print('Cleaning complete')
    print(f'Raw SystemBook rows: {raw_books.shape[0]}, columns: {raw_books.shape[1]}')
    print(f'Cleaned SystemBook rows: {cleaned_books.shape[0]}, columns: {cleaned_books.shape[1]}')
    print(f'Raw SystemCustomers rows: {raw_customers.shape[0]}, columns: {raw_customers.shape[1]}')
    print(f'Cleaned SystemCustomers rows: {cleaned_customers.shape[0]}, columns: {cleaned_customers.shape[1]}')
    print('Output files:')
    print('  - 03_Library Systembook Cleaned.csv')
    print('  - 03_Library SystemCustomers Cleaned.csv')
    print('  - transformation_metrics_all.csv')


if __name__ == '__main__':
    main()
