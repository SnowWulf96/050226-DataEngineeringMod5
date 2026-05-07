# Part 1:
Containerise your data cleaning app so that it outputs clean csv files as a printed output.

# Part 2:
Update the above so that it loads the data into an "always on" docker container with a database OR output CSV files locally.
# Part 3 (Stretch):

Create a front end container, back end container and allow the user to UPLOAD the csv file.

Hint: You may need Docker Compose (yaml)

front end for upload button for user to upload a csv whihc then talks to another container that cleans it and outputs it back to the front end for download.

Need front end to not shutdown