import pandas as pd
import argparse
import psycopg2
from datetime import datetime
from pathlib import Path
from psycopg2.extras import execute_values

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
    # Drop rows where any of the required columns are missing. (e.g. Customer ID, Books)
    df = df.dropna(subset=required_columns)
    return df

def check_customer_ids(df: pd.DataFrame, customer_df: pd.DataFrame) -> pd.DataFrame:
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


def get_postgres_type(series: pd.Series) -> str:
    if pd.api.types.is_integer_dtype(series):
        return 'INTEGER'
    if pd.api.types.is_float_dtype(series):
        return 'DOUBLE PRECISION'
    if pd.api.types.is_datetime64_any_dtype(series):
        return 'TIMESTAMP'
    return 'TEXT'


def prepare_records(df: pd.DataFrame) -> list[tuple]:
    prepared_df = df.copy().where(pd.notna(df), None)
    return [tuple(row) for row in prepared_df.itertuples(index=False, name=None)]


def load_dataframe_to_table(cursor, df: pd.DataFrame, table_name: str) -> None:
    column_definitions = []
    quoted_columns = []

    for column in df.columns:
        column_type = get_postgres_type(df[column])
        column_definitions.append(f'"{column}" {column_type}')
        quoted_columns.append(f'"{column}"')

    cursor.execute(f'DROP TABLE IF EXISTS {table_name}')
    cursor.execute(
        f'''
        CREATE TABLE {table_name} (
            {", ".join(column_definitions)}
        )
        '''
    )

    records = prepare_records(df)
    if not records:
        return

    insert_sql = f'INSERT INTO {table_name} ({", ".join(quoted_columns)}) VALUES %s'
    execute_values(cursor, insert_sql, records)


def load_to_postgres(
    books_df: pd.DataFrame,
    customers_df: pd.DataFrame,
    metrics_df: pd.DataFrame,
) -> None:
    host = 'host.docker.internal'
    user = 'postgres'
    password = 'password'
    database = 'postgres'

    books_to_load = books_df.copy()
    customers_to_load = customers_df.copy()
    metrics_to_load = metrics_df.copy()

    run_timestamp = datetime.now()
    books_to_load['load_timestamp'] = run_timestamp
    customers_to_load['load_timestamp'] = run_timestamp
    metrics_to_load['load_timestamp'] = run_timestamp

    try:
        conn = psycopg2.connect(
            host=host,
            user=user,
            password=password,
            database=database,
        )
        cursor = conn.cursor()
        print('Connected to database')

        load_dataframe_to_table(cursor, books_to_load, 'fact_books_clean')
        print("Table 'fact_books_clean' ready.")

        load_dataframe_to_table(cursor, customers_to_load, 'dim_customers_clean')
        print("Table 'dim_customers_clean' ready.")

        load_dataframe_to_table(cursor, metrics_to_load, 'etl_metrics')
        print("Table 'etl_metrics' ready.")

        conn.commit()
        print('PostgreSQL load complete')
        print(f'Host: {host}')
        print(f'Database: {database}')
        print('Tables: fact_books_clean, dim_customers_clean, etl_metrics')

        cursor.close()
        conn.close()
        print('Database connection closed.')

    except Exception as e:
        print(f'Error: {e}')


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description='Clean library CSVs and optionally load to PostgreSQL.')
    parser.add_argument(
        '--input-dir',
        default='.',
        help='Directory containing raw input CSV files.',
    )
    parser.add_argument(
        '--output-dir',
        default='.',
        help='Directory where cleaned CSV files and metrics will be written.',
    )
    parser.add_argument('--load-to-db', action='store_true', help='Load cleaned data and metrics into PostgreSQL.')
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    input_dir = Path(args.input_dir)
    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    books_input = input_dir / '03_Library Systembook.csv'
    customers_input = input_dir / '03_Library SystemCustomers.csv'

    if not books_input.exists() or not customers_input.exists():
        available_files = sorted([path.name for path in input_dir.glob('*')]) if input_dir.exists() else []
        raise FileNotFoundError(
            'Input CSV files were not found. '\
            f'Expected: {books_input} and {customers_input}. '\
            f'Input directory exists: {input_dir.exists()}. '\
            f'Files visible in input directory: {available_files}'
        )

    # Load raw CSV files.
    raw_books = pd.read_csv(books_input)
    raw_customers = pd.read_csv(customers_input)

    # Clean customers first — needed as a reference for book customer ID checks.
    cleaned_customers = convert_blanks(raw_customers.copy())
    cleaned_customers = drop_duplicates_and_na(cleaned_customers, subset=['Customer ID', 'Customer Name'])
    cleaned_customers = convert_to_int(cleaned_customers, 'Customer ID')
    cleaned_customers = convert_to_strings(cleaned_customers, 'Customer Name')

    # Clean books using the helper functions, passing the cleaned customers for ID validation.
    cleaned_books = convert_blanks(raw_books.copy())
    cleaned_books = drop_duplicates_and_na(cleaned_books, subset=['Customer ID', 'Books'])
    cleaned_books = drop_na_required_columns(cleaned_books, ['Customer ID', 'Books', 'Book checkout'])
    cleaned_books = check_customer_ids(cleaned_books, cleaned_customers)
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
    books_output = output_dir / '03_Library Systembook Cleaned.csv'
    customers_output = output_dir / '03_Library SystemCustomers Cleaned.csv'
    metrics_output = output_dir / 'transformation_metrics_all.csv'

    cleaned_books.to_csv(books_output, index=False)
    cleaned_customers.to_csv(customers_output, index=False)

    # Calculate data engineering metrics for the transformation.
    metrics = calculate_metrics(raw_books, raw_customers, cleaned_books, cleaned_customers)
    metrics.to_csv(metrics_output, index=False)

    # Load the cleaned data and metrics into PostgreSQL (optional).
    if args.load_to_db:
        load_to_postgres(cleaned_books, cleaned_customers, metrics)
    else:
        print('Skipped PostgreSQL load. Use --load-to-db to enable it.')

    # Print summary info.
    print('Cleaning complete')
    print(f'Raw SystemBook rows: {raw_books.shape[0]}, columns: {raw_books.shape[1]}')
    print(f'Cleaned SystemBook rows: {cleaned_books.shape[0]}, columns: {cleaned_books.shape[1]}')
    print(f'Raw SystemCustomers rows: {raw_customers.shape[0]}, columns: {raw_customers.shape[1]}')
    print(f'Cleaned SystemCustomers rows: {cleaned_customers.shape[0]}, columns: {cleaned_customers.shape[1]}')
    print('Preview of cleaned books:')
    print(cleaned_books.head(5).to_string(index=False))
    print('Preview of cleaned customers:')
    print(cleaned_customers.head(5).to_string(index=False))
    print('Output files:')
    print(f'  - {books_output}')
    print(f'  - {customers_output}')
    print(f'  - {metrics_output}')


if __name__ == '__main__':
    main()
