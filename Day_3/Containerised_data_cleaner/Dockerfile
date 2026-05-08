FROM python:3.12-slim
WORKDIR /app
RUN pip install pandas psycopg2-binary
COPY backend_cleaner.py .
ENTRYPOINT ["python", "backend_cleaner.py"]


### Get docker to run the DB
##docker run -d --name library_db -e POSTGRES_PASSWORD=password -p 5432:5432 postgres:15-alpine

## Stop DB
##docker stop library_db

##remove DB
##docker rm library_db

# Build and run app
##docker build -t library_cleaner .
##docker run --rm -v "c:/Users/Admin/Desktop/DataEngineeringMod5/050226-DataEngineeringMod5/Day 3/Containerised_data_cleaner/:/input" -v "c:/Users/Admin/Desktop/DataEngineeringMod5/050226-DataEngineeringMod5/Day 3/Containerised_data_cleaner/:/output" library_cleaner --input-dir /input --output-dir /output --load-to-db

# Check the max load timestamp in the DB to confirm that the cleaner has run and loaded data
##docker exec -it library_db psql -U postgres -d postgres -c "SELECT MAX(load_timestamp) FROM fact_books_clean;"