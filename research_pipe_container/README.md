# Title

# Team
Dmitri Rozgonjuk<br>
Lisanne Siniväli<br>
Eerik-Sven Puudist<br>
Cheng-Han Chung<br>

# 1. Pipeline Overview
The general pipeline structure is presented in Figure 1. Below is the high-level overview of the steps:
1. **Ingestion and Preliminary Preprocessing**: Data is ingested from Kaggle and first clean data tables in .csv format are saved.
2. **Augmentation**: Clean data are augmented via APIs or static data files, and saved to another directory as clean and augmented .csv-s.
3. **Loading to databases**: The cleaned and augmented .csv files are read into `pandas` and loaded to Postgres (data warehousing) as well as to Neo4J database.
4. **Analytic queries**: The data are ready for analytic queries which are done from browser via Jupyter Notebook and Neo4J.

[FIGURE 1: GENERAL PIPELINE FIGURE]

Largely, the process is automated via pipeline orchestration done with Apache Airflow. The data files are kept until the scheduled update in augmentation (yearly), and the cleaned and augmented data files are then deleted to be replaced by updated data files. However, for the raw data files, one needs to run a `python` script from command line (see below).

## 1.1. Relational Database Schema
We use `postgres` as the relational database. The database schema is presented in Figure 2. The aim for this database was to allow us to run queries on author-related statistics (please see the notebook `analytic_queries.ipynb`).

![[Figure 2. Entity-relationship diagram]](images/dwh_erd.png)

## 1.2. Graph Database Schema
We use Neo4J as the graph database. The database schema is similar to the schema shown in Figure 2; however, the main difference is that the yellow tables in Figure 2 (`journal`, `article`, `author`, and `category`) are treated as nodes, where the other two tables, `authorship` and `article_category` are relationships `AUTHORED` and `BELONG_TO`, linking authors-articles and articles-categories, respectively, in Neo4J. the aim of this database was primarily to allow us to extract and visualize (in Neo4J) the ego-network of given researcher. For instance, when given a researcher's name, we wanted to create the possibility to see with whom and on what the person has collaborated.

## 1.3. Data Cleaning and Transformations
TBW 

## 1.4. Data Augmentations
TBW

# 2. How to Run
## 2.1. Prerequisites<br>
- It is assumed that the entire project is on a local machine (i.e., your computer). If not, clone it from github:<br>
`git clone <PROJECT GITHUB LINK>`.
- If you want to ingest the raw data from Kaggle, you will need to prepare a `kaggle.json` file and include it in the project root directory. The default file is included but it needs to be updated with the appropriate credentials. More information can be found here: https://pypi.org/project/opendatasets/.

## 2.2. Run the Pipeline
1. Start your `Docker Desktop` and make sure to allocate sufficient memory (`Settings -> Resources -> Memory`, say 6.25 GB).
2. Navigate to the root directory of this project.
3. From command line (or Terminal on a Mac), run <br>
`echo -e "AIRFLOW_UID=$(id -u)\nAIRFLOW_GID=0" > .env`  <br>
This creates an environment file for Airflow to allow to run it as a superuser.
4. Run `docker-compose up airflow-init`. This initializes Airflow with username and pwd 'airflow' to be used. Wait until the run is completed.
5. Now, run `docker-compose up`. This runs all the services described in the `docker-compose.yaml` file. These services include Airflow, Jupyter Notebook, PostgreSQL, and Neo4J. This may take some time, but it is suggested to keep an eye on the progress from command line, especially whether all services have been properly started. This command also install all the necessary `python` modules and packages.
6. Make sure that all services are up and running. For that, try accessing the services from your browser:
    - Airflow: http://localhost:8080/
    - Jupyter Notebook: http://localhost:8888/
    - Neo4J: http://localhost:7474/ 

    If it's not possible to access all services, wait for some time. Typically, the problem occurs with Neo4J, and if it's not possible to start the service(s), you can also try stopping the process (press twice `Ctrl (or Cmd) + C`) and `docker-compose down`. Then, repeat the process, starting from Step 4.
7. The project folder includes the data tables by default. However, you can also test data ingestion, transformation, and augmentation yourself by deleting the .csv files. **Caution!** Doing so will mean a significantly long runtime (can be more than half a day). If you do choose to go without the default data tables (in repositories `dags/tables` and `dags/data_ready`, see below for description), navigate to the root directory of this project and run the following commands from Terminal: <br>
    - Install the necessary packages (on your local machine):<br> 
    `python -m pip install -r requirements.txt`
    - Run the following command:<br>
    `python3 dags/scripts/raw_to_tables.py`<br>
    This script will (1) download the Kaggle data on your machine, (2) unzip it (appx 3+ GB), (3) extract the necessary data, (4) make the preliminary data cleaning, (5) create the tables depicted in Figure 2, and (6) saves the tables to the `dags/tables` directory in .csv format. Note: you might be asked for your Kaggle credentials from the command line but usually it works also when the file is in the root directory of the project.

8. Navigate to Airflow (http://localhost:8080/). If everything is correct, you should see a DAG called `research_pipeline_dag`. Click on it. Then click on `Graph`. You should now be able to see the DAG. 
9. To trigger the DAG, click on the button on the right that resembles 'Play'. Select `Trigger DAG` when prompted. This triggers the DAG. Wiat for the execution to be finished.
10. Navigate to Jupyter Notebook (http://localhost:8888/) and run the analytical queries for Relational Database. Of note, it is also possible to run Neo4J queries from the notebook, but for our purposes, we run the Neo4J queries from Neo4J browser interface (http://localhost:7474/)
11. And this should be it. Airflow should trigger the data update in summer (at around 1st August), so nothing should change before that.

# 3. Files and Directories
## 3.1 Directory Tree and a Brief Functional Overview
Below is a high-level overview of the general directory structure. Some files (e.g., for caching) that are produced but will not be directly itneracted with by the user are not presented below:

`research_pipe_container/`: the root directory
- `docker-compose.yaml`: Docker container configuration file
- `README.md`: the file you're reading now
- `requirements.txt`: Python libraries/modules to be installed
- `analytical_queries.ipynb`: example queries for Postgres,a nd the possiblity to query Neo4J from Jupyter Notebook
- `dags/`: main directory for scripts, etc
    - `research_pipeline_dag.py`: the entire DAG configuration and scripts for Airflow
    - `augmentation/`
            `article_journal.csv`: clean table with only journal articles
            `cwts2021.csv`: the 2021 data for journals' impact (SNIPs)
            `names_genders.csv`: most of the names matched with genders
    - `data_ready/`: directory with clean and aaugmented data
        - `article_augmented_raw.csv`: the augmented article table where data are not filtered based on column `type` value
        - `article_category.csv`: each article linked to each category label
        - `article.csv`: clean augmented table with only `type` `journal-article`
        - `author.csv`: clean table with each unique author with their attributes (see Figure 2)
        - `authorship.csv`: each individual author-article relationship table
        - `category.csv`: each unique article category with super- and subdomains
        - `journal.csv`: each unique journal with impact metrics (SNIPs)
    - `scripts/`: ETL scripts
        - `raw_to_tables.py`: a module written to primarily be run from command line. Includes data ingestion from source (Kaggle), preliminary pre-processing, and initial data tables (in Figure 2) preparation
        - `augmentations.py`: augmentation scripts for article (CrossRef queries), journal metrics (from a static .csv prepared from a .xslsx file online), and authors (h-index computation using the binary search algorithm)
        - `final_tables.py`: checking if clean tables exist; if not, augmentations are applied, statistics, and tables are cleaned
        - `sql_queries.py`: dropping, creating, and inserting into Postgres tables
        - `neo4j_queries.py`: Neo4J connection class, data insertion (in batches) from pandas to Neo4J
    - `tables/`: directory with preliminary data tables after ingestion and preliminary preprocessing
        - `article_category.csv`: each article linked to each category label
        - `article.csv`: table with extract journal articles (missing `type`, etc)
        - `author.csv`: each unique author with their attributes (see Figure 2)
        - `authorship.csv`: each individual author-article relationship table
        - `category.csv`: each unique article category with super- and subdomains
        - `journal.csv`: an empty journal table placeholder to be filled in augmentation process
- `images/`
        `dwh_erd.png`: Figure 2 .png file
- `logs/`: Airflow logs
- `neo4j/`: Neo4J related files and folders
- `plugins/`: Airflow plugins (not used in this project)

# 4. Design Choices
## 4.1. Subsetting the Entire Dataset
Although it is possible to work with the entire Arxiv dataset available in Kaggle, we decided to limit our data to indexed journal articles with a valid DOI for which at least one of the category tags included 'cs.', or Computer Science. Hence, only eligible entities (i.e., authors, journals) were included in further databases and analyses.

## 4.2. Data Augmentations
### 4.2.1. `article`
We queried Crossref API with a given work's DOI. Works of type `journal-article` were updated with citation counts and journal ISSNs. We did not query more information, since this was sufficient for our purposes.
 
### 4.2.2. `journal`
In order to get the journal information, we need the journal ISSN list from the article table. Although journal Impact Factor is a more common metric, it is trademarked and, hence, retrieving it is not open-source. The alternative is to use SNIP: the source-normalized impact per publication. This is the average number of citations per publication, corrected for differences in citation practice between research domains. Fortunately, the list of journals and their SNIP is available from the CWTS website (https://www.journalindicators.com/).

### 4.2.3. `author`
For each author, we used a names-genders dataset to add supposed genders to each author. Although affiliation could also be of interest, there are several problems due to which we decided not to find affiliation data. First, the article augmentation source was largely missing affiliation data for authors. Second, in some cases, making queries based on author names were not possible (e.g., only author's first name initial was present - not allowing to identify the author properly). Third, authors' affiliation may change dynamically (e.g., when changing an institution) and authors can also have multiple affiliations. Fourth, author affiliation in itself was not within the scope of the present project.

# 5. Discussion and Conclusions
Working with this pipeline demanded a lot of effort for several reasons. First, this pipeline works relatively easily on a small data set (say, 100 articles) - but working with tens of thousands (or more) data samples is very slow, especially in the augmentation phase where querying Crossref too often and in large amount may result in a blocked IP. Second, most of the frustration was likely experienced with Neo4J, as its functioning is, at times, unreliable. 

WRITE MORE!!!
