FROM python:3.12-bullseye

# Install Microsoft ODBC Driver 17 for SQL Server (Debian 11 / Bullseye)
RUN apt-get update && apt-get install -y --no-install-recommends \
        curl \
        gnupg \
        unixodbc-dev \
    && curl https://packages.microsoft.com/keys/microsoft.asc | apt-key add - \
    && curl https://packages.microsoft.com/config/debian/11/prod.list \
        > /etc/apt/sources.list.d/mssql-release.list \
    && apt-get update \
    && ACCEPT_EULA=Y apt-get install -y msodbcsql17 \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

RUN pip install --no-cache-dir pandas sqlalchemy pyodbc

COPY data_cleaner.py .

# CSV files are expected to be mounted at /data
# The SQL Server host is passed in via SQL_SERVER env var
ENV SQL_SERVER=host.docker.internal

ENTRYPOINT ["python", "data_cleaner.py"]

# ─── Quick-start commands ────────────────────────────────────────────────────

# 1. Build the image
#    docker build -t library_cleaner .

# 2. Run — mount the folder that contains the two CSV files to /data
#    (Windows PowerShell path style shown; adjust for your machine)
#
   #docker run --rm -v "C:/Users/Admin/Desktop/DataEngineeringMod5/050226-DataEngineeringMod5/Day_4/data:/data" -e SQL_SERVER=host.docker.internal,1433 -e SQL_USERNAME=notsahonest -e SQL_PASSWORD="password" library_cleaner --data-dir /data --load-to-sql
#    Omit --load-to-sql to do a dry run (CSVs only, no DB write).

# 3. Verify the latest pipeline run in SSMS / Azure Data Studio:
#    SELECT TOP 1 * FROM etl_pipeline_runs ORDER BY run_start DESC;
