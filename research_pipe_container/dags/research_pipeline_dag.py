from datetime import datetime, timedelta
import os

# Airflow-related imports
from airflow import DAG
from airflow.operators.empty import EmptyOperator # Dummy operator
from airflow.operators.python import PythonOperator # Python operator
from airflow.providers.postgres.operators.postgres import PostgresOperator # PostgresOperator
# from airflow.operators.bash import BashOperator # Bash operator
from airflow.utils.dates import days_ago

# Import the custom scripts
from scripts.raw_to_tables import *
from scripts.augmentations import *
from scripts.final_tables import *
from scripts.sql_queries import *
from scripts.neo4j_queries import *

# Import necessary libraries
import pandas as pd # working with dataframes
import numpy as np # vector operations

### Misc
from math import floor
import time
import requests
import warnings # suppress warnings
import os # accessing directories
from tqdm import tqdm # track loop runtime
from unidecode import unidecode # international encoding fo names
import psycopg2


#### ------ Python Functions ------  ####
# Insert into tables (helper function)
def insert_to_tables(cur, table, query):
    ''' Helper function for inserting values to Postresql tables
    Args:
        table (pd.DataFrame): pandas table
        query (SQL query): correspondive SQL query for 'table' for data insertion in DB
    '''
    print(f'Inserting table -- {table.name} -- ...')
    
    try:
        for i, row in table.iterrows():
            cur.execute(query, list(row))
        print(f'Table -- {table.name} -- successfully inserted!')
    except:
        print(f'Error with table -- {table.name} --')
    print()

# DAG task functions
def find_tables_or_ingest_raw():
    print('Checking if tables are prepared as .csv files...')
    if os.path.exists('dags/tables/author.csv'):
        print("'author.csv' exists.")
        pass
    if os.path.exists('dags/tables/article.csv'):
        print("'article.csv' exists.")
        pass
    if os.path.exists('dags/tables/authorship.csv'):
        print("'authorship.csv' exists.")
        pass
    if os.path.exists('dags/tables/article_category.csv'):
        print("'article_category.csv' exists.")
        pass
    if os.path.exists('dags/tables/category.csv'):
        print("'category.csv' exists.")
        pass
    if os.path.exists('dags/tables/journal.csv'):
        print("'journal.csv' exists.")
        pass
        print('Tables exist in the directory!')

    ## If tables do not exist, pull from kaggle (or local machine), proprocess to tables
    else: 
        print('Preparing tables...')
        print()
        ingest_and_prepare()
        print('Tables are in the working directory!')

def check_or_augment():
    """Function to either check if clean tables exist
    or clean the data and write them to .csv
    """

    if os.path.exists('dags/data_ready/article_augmented_raw.csv'):
        if os.path.exists('dags/data_ready/article.csv'):
            article = pd.read_csv('dags/data_ready/article.csv')
        else:
            article_journal = pd.read_csv('dags/data_ready/article_augmented_raw.csv')
            article = article_journal[article_journal['type'] == 'journal-article'].reset_index(drop = True)
            article.to_csv('dags/data_ready/article.csv', index = False)
    else:
        article = article_ready()
    
    # Journal
    journal = journal_ready()

    # Remove not found journals from articles
    article = article[article['journal_issn'].isin(journal['journal_issn'])].reset_index(drop = True)
    # Update 'article.csv' in 'data_ready' directory
    article.to_csv('dags/data_ready/article.csv', index = False)

    authorship = authorship_ready(article)
    author = author_ready(article, authorship)
    article_category = article_category_ready(article)
    category = category_ready(article_category)

def pandas_to_dwh():
    # Import the data
    try:
        article = pd.read_csv('dags/data_ready/article.csv')
        author = pd.read_csv('dags/data_ready/author.csv')
        authorship = pd.read_csv('dags/data_ready/authorship.csv')
        category = pd.read_csv('dags/data_ready/category.csv')
        article_category = pd.read_csv('dags/data_ready/article_category.csv')
        journal = pd.read_csv('dags/data_ready/journal.csv')
        tables = [article, author, authorship, category, article_category, journal]

        # Name of tables (for later print)
        article.name = 'article'
        author.name = 'author'
        authorship.name = 'authorship'
        category.name = 'category'
        article_category.name = 'article_category'
        journal.name = 'journal'
        print(article.head(2))
        print(author.head(2))
        print(authorship.head(2))
        print(category.head(2))
        print(article_category.head(2))
        print(journal.head(2))
        print('All tables staged for DWH.')
    except:
        print('Error with importing the data tables')
       
    # Connect to the database
    conn = psycopg2.connect(host="postgres", user="airflow", password="airflow", database ="airflow", port = 5432)
    conn.set_session(autocommit=True)
    cur = conn.cursor()

    # create sparkify database with UTF8 encoding
    cur.execute("DROP DATABASE IF EXISTS research_db")
    cur.execute("CREATE DATABASE research_db WITH ENCODING 'utf8' TEMPLATE template0")

    # Drop Tables 
    try: 
        for query in drop_tables:
            cur.execute(query)
            conn.commit()
        print('All tables dropped.')
    except:
        print('Error with dropping tables.')
        
    # Create Tables
    try: 
        for query in create_tables:
            cur.execute(query)
            conn.commit()
        print('All tables created.')
    except:
        print('Error with creating tables.')

    # Insert into tables
    for i in tqdm(range(len(tables))):
        insert_to_tables(cur, tables[i], insert_tables[i])

def pandas_to_neo():
    # Import the data
    try:
        article = pd.read_csv('dags/data_ready/article.csv')
        author = pd.read_csv('dags/data_ready/author.csv')
        authorship = pd.read_csv('dags/data_ready/authorship.csv')
        category = pd.read_csv('dags/data_ready/category.csv')
        article_category = pd.read_csv('dags/data_ready/article_category.csv')
        journal = pd.read_csv('dags/data_ready/journal.csv')
        tables = [article, author, authorship, category, article_category, journal]

        # Name of tables (for later print)
        article.name = 'article'
        author.name = 'author'
        authorship.name = 'authorship'
        category.name = 'category'
        article_category.name = 'article_category'
        journal.name = 'journal'
        print(article.head(2))
        print(author.head(2))
        print(authorship.head(2))
        print(category.head(2))
        print(article_category.head(2))
        print(journal.head(2))
        print('All tables staged for Neo4J.')
    except:
        print('Error with importing the data tables.')

    # Neo4J Connection
    try:
        print('Trying to establish Neo4J connection...')
        conn_neo = Neo4jConnection(uri='bolt://neo:7687', user='', pwd='')
        print('Neo4J Connection established!')
        
        try:
            print('Deleting previous nodes and relationships...')
            # Delete all relationships that exist
            conn_neo.query('MATCH (a) -[r] -> () DELETE a, r')
            # Delete all nodes that exist
            conn_neo.query('MATCH (a) DELETE a') 
        except:
            print('Error with deleting nodes and relationships.')
       
        try:
            print('Settings constraints to unique IDs...')
            # Add ID uniqueness constraint to optimize queries
            conn_neo.query('CREATE CONSTRAINT ON(n:Category) ASSERT n.id IS UNIQUE')
            conn_neo.query('CREATE CONSTRAINT ON(j:Journal) ASSERT j.id IS UNIQUE')
            conn_neo.query('CREATE CONSTRAINT ON(au:Author) ASSERT au.id IS UNIQUE')
            conn_neo.query('CREATE CONSTRAINT ON(ar:Article) ASSERT ar.id IS UNIQUE')
        except:
            print('Could not set constraints.')

        print(f'Inserting pandas to NEO4J...')
        try: 
            print("Adding 'article' nodes to Neo4J...")
            add_article(conn_neo, article)
            print("'article' added to Neo4J!")
        except: 
            print("Could not add 'article' to Neo4J")  

        try: 
            print("Adding 'author' nodes to Neo4J...")
            add_author(conn_neo, author)
            print("'author' added to Neo4J!")
        except: 
            print("Could not add 'author' to Neo4J")  
        
        try: 
            print("Adding 'category' nodes to Neo4J...")
            add_category(conn_neo, category)
            print("'category' added to Neo4J!")
        except:
            print("Could not add 'category' to Neo4J")
        
        try: 
            print("Adding 'journal' nodes to Neo4J...")
            add_journal(conn_neo, journal)
            print("'journal' added to Neo4J!")
        except: 
            print("Could not add 'journal' nodes to Neo4J")        

        try: 
            print("Adding 'article_category' relationship to Neo4J...")
            add_article_category(conn_neo, article_category)
            print("'article_category' added to Neo4J!")
        except: 
            print("Could not add 'article_category' to Neo4J")  

        try: 
            print("Adding 'authorship' relationship to Neo4J...")
            add_authorship(conn_neo, authorship)
            print("'authorship' added to Neo4J!")
        except: 
            print("Could not add 'authorship' to Neo4J")

        
        print(f'pandas to Neo4J inserted!')
        
        print('Error or entities already exist (check the subsequent info)!')
        print('Below are the counts of entities in the Neo4J database (must be non-null):')
        n_articles = conn_neo.query('MATCH (n:Article) RETURN COUNT(n) AS ct')
        n_authors = conn_neo.query('MATCH (n:Author) RETURN COUNT(n) AS ct')
        n_journals = conn_neo.query('MATCH (n:Journal) RETURN COUNT(n) AS ct')   
        n_categories =  conn_neo.query('MATCH (n:Category) RETURN COUNT(n) AS ct')  
            
        print(f"Number of articles in the NEO4J database: {n_articles[0]['ct']}")
        print(f"Number of authors in the NEO4J database: {n_authors[0]['ct']}")
        print(f"Number of journals in the NEO4J database: {n_journals[0]['ct']}")
        print(f"Number of categories in the NEO4J database: {n_categories[0]['ct']}")
    except:
        print('Neo4J Connection not established...')


#### ------ AIRFLOW ------  ####
# Cron notation: https://cloud.google.com/scheduler/docs/configuring/cron-job-schedules
## Also: https://crontab.guru/

# Adding default parameters:
default_args = {
    'owner': 'dmitri_rozgonjuk',
    'depends_on_past': False, # The DAG does not have dependencies on past runs
    'retries': 3, # On failure, the task are retried 3 times
    'schedule_interval': None,
    #'schedule_interval': '0 2 1 8 *', # Schedule interval yearly to 03:00 01.08
    'retry_delay': timedelta(minutes = 5), # Retries happen every 5 minutes
    'catchup' : False, # Catchup is turned off
    'email_on_retry': False, # Do not email on retry
    'email_on_failure': False, # Also, do not email on failure
    'start_date': days_ago(1), # set starting day in the past
}

# Define the DAG
dag = DAG('research_pipeline_dag',
          default_args=default_args,
          description= 'Run the Research Data Pipeline and Prepare Databases',
        )

# Define the tasks
## Starting the DAG
start_operator = EmptyOperator(task_id='Begin_Execution',  dag = dag)

## Find tables or ingest raw data
ingest_task1 = PythonOperator(task_id='find_tables_or_ingest_raw', python_callable = find_tables_or_ingest_raw, dag = dag)

## Load the data or augment and save as csv
augment_task2 = PythonOperator(task_id='check_or_augment', python_callable = check_or_augment, dag = dag)

## Make the connection with Postgres, load pandas tables to DWH
postgres_task3 = PythonOperator(task_id='pandas_to_dwh', python_callable = pandas_to_dwh, dag = dag)

# Neo4J Connection and data load
neo_task3 = PythonOperator(task_id='pandas_to_neo', python_callable = pandas_to_neo, dag = dag)

## Ending the DAG
end_operator = EmptyOperator(task_id='Stop_Execution',  dag = dag)

# Create task dependencies/pipeline
## Initially, data load to Postgres and Neo4J was parallel - but this produced errors (memory issues)
start_operator >> ingest_task1 >> augment_task2 >> postgres_task3 >> neo_task3 >> end_operator
# augment_task2 >> postgres_task3 >> end_operator
# augment_task2 >> neo_task3 >> end_operator