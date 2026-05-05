
## Architecture Diagram

![Architecture Diagram](Architecture%20for%20Library%20Data%20Conversion.png)

## User Stories

1. As a librarian, I want new customer and book loan CSV files uploaded into the pipeline so that I do not have to prepare the data manually each time.
2. As a data analyst, I want the pipeline to check for missing customer IDs, blank rows, and invalid dates so that data issues are identified before they affect reports.
3. As a librarian, I want book loan records matched to the correct customer record so that I can see who borrowed each book.
4. As a library manager, I want duplicate and invalid loan records removed or flagged so that weekly and monthly reports are accurate.
5. As a stakeholder, I want the cleaned library data stored in a SQL database or warehouse so that the team can query a trusted source of data.
6. As a reporting user, I want a dashboard showing borrowing activity, returns, and possible overdue items so that I can monitor how the library service is being used.

## Delivery Plan

### Option: Kanban

#### Backlog
- Confirm business rules with stakeholder
- Define expected schema for both CSV files
- Confirm output reports needed

#### To Do
- Build file ingestion step
- Add validation checks for file type, headers, and required fields
- Convert CSV data into tabular structures

#### In Progress
- Create user stories
- Finalise delivery plan

#### Done
- Create GitHub repo and clone to VM
- Create architecture diagram

### Delivery Phases

#### Phase 1 - Design
- confirm scope and business rules
- review source CSV files
- finalise architecture

#### Phase 2 - Ingest and Validate
- load source files
- validate structure and content
- log invalid records

#### Phase 3 - Clean and Transform
- remove blanks and duplicates
- standardise values
- apply business rules

#### Phase 4 - Load and Report
- load clean data into SQL DB or DW
- connect reporting tool
- build initial reports