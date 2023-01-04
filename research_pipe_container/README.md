# Title

# Team
Dmitri Rozgonjuk
Lisanne Siniväli
Eerik-Sven Puudist
Cheng-Han Chung

TO DO:
- check that data is imported to DWH and NEO
- schedule Airflow to:
    - every August 1st to delete the contents in 'data_ready' dir
    - run the DAG
        - this should initialize the augmentation process again and compute all stats
        - also updates the DBs
- write the readme


# Pipeline Structure
- [GENERAL PIPELINE FIGURE]

- [DATA CLEANING/AUGMENT FIGURE]

## Relational DB Schema
- [ERD FIGURE]

## Graph DB Schema
- [GRAPH SCHEMA FIGURE]

# Files
## Directory tree

DIRS

dags: files necessary for Airflow DAG run
    - tables: data tables from initial ingestion as well as raw augmented article table
    - augmentation: files for augmentations
     - article_journal.csv
     - names_genders.csv
    - data_ready: clean and augmented data tables for query use
    - scripts: python scripts for ETL
        - raw_to_tables.py
        - augmentations.py
        - crossref_queries.py
        - final_tables.py
        - sql_queries.py
        - neo4j_queries.py
        

logs: airflow logs
neo4j: neo4j-related files
plugins: folder for optional airflow plugins, currently not used

FILES
docker-compose.yaml
kaggle.json
README.md
requirements.txt
analytical_queries.ipynb

- [TREE]
- [EXPLANATIONS]

# Prerequisites
- pip install prerequs
- download the data
    - python3 dags/scripts/raw_to_tables.py
- Docker Desktop
- Docker Memory > 4GB

- kaggle.json (in the same dir as dags)

# How to Run
Once Airflow is set up and the services are running, it's time to initiate the pipeline via a DAG. The main function of the DAG is to check if there are clean data tables. If yes, connections are made with databases and data tables are loaded from .csv-s to Postgres DWH and Neo4J. Then, analytic queries can be run from the Jupyter Notebook. If there are no clean data tables, checks are made if the uncleaned (without augmentations) data tables exist. If yes, the data tables are augmented. If no, it is checked whether the raw data folder exists in the directory. If yes, the data are cleaned and augmented. If no, data is first downloaded from the Kaggle repository, cleaned and augmented, and prepared for the databases.

**NOTE**. In case the raw dataset is not in the directory, it needs to be downloaded from Kaggle. For that, one needs to use a Kaggle username alongside the token/key. For more information, see: https://pypi.org/project/opendatasets/

Below is the step-by-step description of how to run the project:
1. Navigate to the root directory of this project.
2. From command line (or Terminal on a Mac), run <br>
`echo -e "AIRFLOW_UID=$(id -u)\nAIRFLOW_GID=0" > .env`  <br>
This creates an environment file for Airflow to allow to run it as a superuser.
3. Run `docker-compose up airflow-init`. This initializes Airflow with username and pwd 'airflow' to be used.
4. Now, run `docker-compose up`. This runs all the services described in the `docker-compose.yaml` file. These services include Airflow, Jupyter Notebook, PostgreSQL, and Neo4J.




## Interacting with Services
In order to be able to use Jupyter Notebook, Neo4J, and Airflow from browser, use the following links:
- Airflow: http://localhost:8080/
- Jupyter Notebook: http://localhost:8888/
- Neo4J: http://localhost:7474/

# Comments on Design Choices
## Subsetting the entire dataset
Although it is possible to work with the entire Arxiv dataset available in Kaggle, we decided to limit our data to indexed journal articles with a valid DOI for which at least one of the category tags included 'cs.', or Computer Science. Hence, only eligible entities (i.e., authors, journals) were included in further databases and analyses.

## Data Augmentations
### `article`
We queried Crossref API with a given work's DOI. Works of type `journal-article` were updated with citation counts and journal ISSNs. We did not query more information, since this was sufficient for our purposes.
 
### `journal`
In order to get the journal information, we need the journal ISSN list from the article table. Although journal Impact Factor is a more common metric, it is trademarked and, hence, retrieving it is not open-source. The alternative is to use SNIP: the source-normalized impact per publication. This is the average number of citations per publication, corrected for differences in citation practice between research domains. Fortunately, the list of journals and their SNIP is available from the CWTS website (https://www.journalindicators.com/).

### `author`
For each author, we used a names-genders dataset to add supposed genders to each author. Although affiliation could also be of interest, there are several problems due to which we decided not to find affiliation data. First, the article augmentation source was largely missing affiliation data for authors. Second, in some cases, making queries based on author names were not possible (e.g., only author's first name initial was present - not allowing to identify the author properly). Third, authors' affiliation may change dynamically (e.g., when changing an institution) and authors can also have multiple affiliations. Fourth, author affiliation in itself was not within the scope of the present project.
