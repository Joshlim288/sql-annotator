# sql-annotator
A program that takes in a SQL query and returns annotations for the query in natural language through highlighting.

Please note that the PostgreSQL database that you would like to run queries on must have been initialised prior to running this application.

- project.py (entry point for the application)
- preprocessing.py (handles query pre-processing for annotation)
- annotation.py (handles annotation using the query's QEP)
- interface.py (user-friendly interface for displaying annotations)

The screens defined in interface.py also load their design and layout from their respective .ui files.

The application can be run from project.py. 

## Requirements
PostgreSQL version 14, running on port 5432

Python version 3.8 and above

Python packages required:
1) PyQt5 (run: pip install PyQt5)
2) psycopg2 (run: pip install psycopg2)
