I need to have:

A presentation (markdown) for the data cleaning app that includes:

* Architecture Diagram
* Proposed Solution
* A PowerBi Dashboard that tracks the pipeline runs along with at least 3 Data engineering metrics
* Demo
* Risks & Issues
* SWOT Analysis
* Stretch: Demo/Test Docker Swarm and explain how this would fit into the above

## Architecture Diagram

```mermaid
flowchart LR
	A[Raw CSV Files\n03_Library Systembook.csv\n03_Library SystemCustomers.csv] --> B[Docker Container\nlibrary_cleaner]

	B --> C[Python ETL Script\ndata_cleaner.py]

	C --> D[Data Cleaning + Validation\n- blanks/NA handling\n- duplicate removal\n- date fixes\n- referential checks]
	D --> E[Derived Fields\nDays Borrowed]
	E --> F[DE Metrics\ntransformation_metrics_all\n+ run_id/run_start]

	D --> G[Cleaned CSV Outputs\nSystembook Cleaned\nSystemCustomers Cleaned]

	C --> H[Pipeline Run Logging\netl_pipeline_runs\nrun_start/run_end/duration/status]

	C --> I[SQL Server\nDataEngineeringMod5_NiroshsLibrary]
	F --> I
	G --> I
	H --> I

	I --> J[fact_books_clean]
	I --> K[dim_customers_clean]
	I --> L[etl_metrics]
	I --> M[etl_pipeline_runs]

	J --> N[Power BI Dashboard]
	K --> N
	L --> N
	M --> N

	N --> O[Monitoring Views\n- Pipeline success/failure\n- Run duration trend\n- Data quality metrics trend]
```
