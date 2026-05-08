# Library Data Cleaning Pipeline - Presentation

## 1. Introduction

### What we're doing

So we're building a Docker container that runs a python app that takes raw CSV files, cleans them up, enriches, and dumps the results into SQL Server. Power BI pulls from there and shows us dashboards and metrics.

### Why does this matter?

Right now, every time someone needs clean library data, it's a manual job to clear out junk data and enrich. This way it's automated, repeatable, and we can actually track what's happening. You can see exactly what got cleaned, when it ran, how long it took etc. Anything else required can then be built on the sql server using the relational database.

### What we're using

- Two CSV files: books and customers data
- Python app does the work inside adocker container
- Exports CSVs & throws it all into SQL Server
- Power BI is then used to show the metrics

---

## 2. How it Works

![Architecture Diagram](Architecture%20Diagram.drawio.png)

*Figure 1: The whole flow—CSVs go in, get cleaned in Docker, land in SQL Server, Power BI reads it.*

Here's the basic flow:

- Throw the CSV files into a folder
- Docker container runs the cleaner script
- Script validates, dedupes, fixes dates, enriches etc
- Cleaned data and metrics get written to csvs and to SQL Server
- Every run is tracked in a pipeline runs table so we know what happened
- Power BI connects to the database and makes pretty dashboards

---

## 3. What I Actually Built

### The pieces

- **Drop files here**: CSV files go into a folder
- **Docker runs it**: Python script fires up, does all the cleaning and validation
- **CSVs returned:** CSVs of the cleaned data and the metrics get written back to the origin folder
- **SQL Server catches it**: Everything gets written to a database called `NiroshsLibrary`
- **Power BI shows it**: Dashboards pull from the database

### Where the data lives

It writes to four tables:

- `fact_books_clean` - cleaned book data
- `dim_customers_clean` - cleaned customer data
- `etl_metrics` - data quality numbers (how many dupes we found, invalid dates, etc.)
- `etl_pipeline_runs` - basically a log of every time the pipeline ran (when, how long it took, did it work?)

### Why this works

It's simple. You can run it as many times as you want and it'll work the same way every time. Everything's tracked, so if something goes wrong, you can see what happened. Docker means it doesn't matter what machine you're on you can just spin up the container.

---

## 4. Power BI Dashboard

### What we want to see

A dashboard that shows: is the pipeline healthy? how's the data quality? what changed over time?

### Key numbers to track

- How many times did it run (by day, by week)?
- How long does it usually take?
- How many runs failed vs succeeded?
- How many duplicate rows did we throw out?
- How many bad dates did we fix?
- Any other data quality issues?

---

## 5. How We'll Demo This

1. Build the Docker image
2. Run it the first time (watch it clean data and write to SQL)
3. Run it again (show that it works consistently)
4. Open Power BI and show the metrics updating in real time

---

## 6. What Could Go Wrong

### Stuff we need to watch for

- Docker can't reach SQL Server (network stuff port, firewall, auth)
- CSV files change format or add/remove columns
- Data's so bad that our cleaning rules throw out too much
- Credentials get accidentally hardcoded somewhere

### How we're handling it

- We're using environment variables for credentials, not baking them into code
- We validate the SQL connection before we even start cleaning
- If something breaks, everything gets logged to the pipeline runs table so you can see what happened
- We have a cleanup script to reset everything for testing

---

## 7. Quick SWOT

### What we got right

- It's simple and it works the same way every time
- You can see exactly what's happening with metrics and run logs
- Data gets from CSV to Power BI pretty fast

### Where it's weak

- Right now you have to manually drop files; it's not automated yet
- Storage location & SQL Server are just the local pc
- Writes to the same location as the input and doesn't move the old files so both clean and raw csvs in the same place
- One container can only process so much at once
- If something breaks, you need to jump into logs and figure it out
- Not dynamic, if something doesn't follow the naming convention

### Opportunities

- You could run this for multiple libraries at once (Docker Swarm)
- Work out a plan to schedule it.
- Add alerts e.g."run took twice as long as usual" or "quality metrics dropped"
- Write runbooks for various errors as and when they occur
- Create a storage location for it to connect to and set the SQL server connection details so it can be accessed remotely not just locally.
- Move the raw data into an archive and output the clean in a new folder e.g. Cleaned_08_05_2026 etc
- Work with Libraries and collate all the files they'll send and build schema out for each variation, could even split these into seperate apps to run on different docker containers

---

## 8. Next Level: Docker Swarm (Future proofing)

![Docker Swarm Architecture](Docker%20Swarm%20Library.png)

*Figure 2: Run multiple cleaners in parallel across a cluster. Each library's files get processed faster, and if one fails, another one picks up the work.*

### How it'd work

- All libraries dump their files into one place
- A job queue says "this library's data needs cleaning"
- Swarm spins up multiple cleaner containers and spreads the work across them
- Everyone writes to the same SQL Server
- Power BI sees all the libraries' metrics in one place
- If a container dies, Swarm automatically reruns the job on a healthy one
- Further research and development would likely be required. But this would allow resiliency and scalability for many future libraries to join the party.

It's basically like scaling up from "one person doing the cleaning" to "a whole team doing it in parallel."

---

## 9. What's Next

- Schedule this to run automatically instead of manually
- Make sure it's able to handle different CSVs
- Create a proper storage location and enable dynamic handling of this
- If we've got time, spin up Swarm and test it with a couple libraries
