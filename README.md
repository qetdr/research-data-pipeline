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

![[Figure 3. Graph database schema]](images/graph_db_schema.png)

## 1.3. Data Cleaning and Transformations
Below is the step-by step description of data cleaning and transformations done within the pipeline.The following steps are in the functionality of `dags/scripts/raw_to_tables.py` module.

1. Data are downloaded from kaggle, unzipped, and only the necessary columns are extracted and converted to a `pandas DataFrame`.
2. Initial cleaning is perfoemd: records with a missing DOI are removed, , duplicates (based on `article_id`) are dropped, only the articles that include the category `cs` (stands for 'computer science') are included.
3. Initial table extraction:
    - `authorship` and `author`: names are parsed from the dataset extracted in previous step. For each author, first, last, and middle names are extracted. Names are cleaned (removing non-alphabetical characters). Author identifier is created (in the form LastnameF where 'F' stands for first name initial). `authorship` table is a long-format table with each author corresponding to each article. `author table` is extracted so that unique name identifiers create their own table.
    - `article_category` and `category`: similarly, lists of article categories are parsed and `article_category` (long-format table with each vcateogry label correspodning to article) and unique categories forming a table with super- and subdomain identifiers.
    - initial `article` and `journal` tables are created. 
4. Once these tables are prepared, these tables are then cleaned for missing values, NaN-values, etc. Authors with too long last names are removed. Tables are written to `.csv` format in the `dags/tables` directory.

Next the clean data for use in databases are created and augmented. Here, the module `/dags/scripts/final_tables.py` is relevant. Here, the process starts with prearing and augmenting the `article` table, since it defines what parts of other tables are included. 

5. We query the DOIs of articles against Crossref API to receive the work type, number of citations and journal ISSN. for that, we use the helper-function `fetch_article_augments()` from `/dags/scripts/augmentations.py`. The querying is done in batches of 2000, where after each batch, the data are udpated in the .csv file. **WARNING!** This process is very slow, since too many queries per second may result in the IP being blocked. Hence, we chose the stable but slow option over fast but highly risky. After the `article` table is augmented, we select only the works where type is `journal-article`. Other tables are updated accordingly

6. `journal` table is then augmented. We ad the source-normalizedd impact factors from the CWTS website. However, for convenience, we have downloaded the Excel workbook and use this a source locally. The helper-functions `check_or_prepare_journal_metrics()` and `find_journal_stats()` from `/dags/scripts/augmentations.py` are used.

7. Finally, we augment the `author` table. We start by including genders for authors based on their first name. The names are retrieved from a static dataset which is included in the  `dags/augmentation/` directory. First names from `author` table are matched with the names in data. If a match is found, gender is updated; otherwise, gender remains a NaN. Then, we also compute various statistics for each author. Additionally, we compute the h-index for each author based on the metrics from the database. For h-index computation, we use the `hindex()` function from `/dags/scripts/augmentations.py`.

8. Finally, we update all tables to be in coherence with each other (meaning that each entity/node has relations, etc).

9. Clean data tables are saved in `.csv` format to `dags/data_ready/` directory from where it can be used for loading to databases.

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

# 5. Example Queries and Results
In the present pipeline, we had several analytic goals for which the pipeline was created. The aim of the Data Warehouse was to provide insights into the productivity (operationalized as the number of total publications) and influence (operationalized as citation count) of top researchers in the database. 

## 5.1. Data Warehouse Queries
Below are (1) analytic questions, (2) SQL-queries (via Python), and pictures of results of the queries.

### 5.1.1. Who are the top 0.01% scientists with the most publications in the sample?
<pre>
SELECT author_id, rank_total_pubs as rank, total_pubs as publications
FROM author 
ORDER BY rank_total_pubs 
LIMIT  0.01 * (SELECT COUNT(*) FROM author) / 100;
</pre>

[PIC1]

### 5.1.2. Proportionally, in which journals have the top 0.01% of scientists (in terms of publication count) published their work the most?

<pre>
SELECT final.author_id, final.rank, final.publications, final.journal_title as top_journal,  TO_CHAR((final.number * 100 / final.publications), 'fm99%') as percentage_of_all_publications
FROM (select a.author_id, rank, publications, mode() within group (order by j.journal_title) AS journal_title, COUNT(j.journal_title) as number
      from (SELECT author_id, rank_total_pubs as rank, total_pubs as publications
      FROM author 
      ORDER BY rank_total_pubs 
      LIMIT  0.01 * (SELECT COUNT(*) FROM author) / 100) AS a
      INNER JOIN authorship au ON a.author_id = au.author_id
      INNER JOIN article ar ON au.article_id = ar.article_id
      INNER JOIN journal j ON ar.journal_issn = j.journal_issn
      group by a.author_id, rank, publications,j.journal_title
      having j.journal_title = mode() within group (order by j.journal_title)) as final
LEFT JOIN (select a.author_id, rank, publications, mode() within group (order by j.journal_title) AS journal_title, COUNT(j.journal_title) as number
      from (SELECT author_id, rank_total_pubs as rank, total_pubs as publications
      FROM author 
      ORDER BY rank_total_pubs 
      LIMIT  0.01 * (SELECT COUNT(*) FROM author) / 100) AS a
      INNER JOIN authorship au ON a.author_id = au.author_id
      INNER JOIN article ar ON au.article_id = ar.article_id
      INNER JOIN journal j ON ar.journal_issn = j.journal_issn
      group by a.author_id, rank, publications,j.journal_title
      having j.journal_title = mode() within group (order by j.journal_title)) as final1 ON 
    final.author_id = final1.author_id AND final.number < final1.number
WHERE final1.author_id IS NULL
ORDER BY final.rank 
LIMIT  0.01 * (SELECT COUNT(*) FROM author) / 100;
</pre>

[PIC2]

### 5.1.3. What was the most productive year (N publications) for top 0.01% scientists?

<pre>
SELECT final.author_id, final.rank, final.publications, final.most_productive_year as most_productive_year, final.number as count_of_pub
FROM (SELECT a.author_id, rank, publications, mode() within group (order by ar.year) AS most_productive_year, sum(publications) as number
    FROM (SELECT author_id, rank_total_pubs as rank, total_pubs as publications
    FROM author 
    ORDER BY rank_total_pubs 
    LIMIT  0.01 * (SELECT COUNT(*) FROM author) / 100) AS a
    INNER JOIN authorship au ON a.author_id = au.author_id
    INNER JOIN article ar ON au.article_id = ar.article_id
    GROUP BY a.author_id, rank, publications, ar.year
    having ar.year = mode() within group (order by ar.year)) as final
LEFT JOIN (SELECT a.author_id, rank, publications, mode() within group (order by ar.year) AS most_productive_year, sum(publications) as number 
    FROM (SELECT author_id, rank_total_pubs as rank, total_pubs as publications
    FROM author 
    ORDER BY rank_total_pubs 
    LIMIT  0.01 * (SELECT COUNT(*) FROM author) / 100) AS a
    INNER JOIN authorship au ON a.author_id = au.author_id
    INNER JOIN article ar ON au.article_id = ar.article_id
    GROUP BY a.author_id, rank, publications, ar.year
    having ar.year = mode() within group (order by ar.year)) as final1 ON 
    final.author_id = final1.author_id AND final.number < final1.number
WHERE final1.author_id IS NULL
ORDER BY final.rank 
LIMIT  0.01 * (SELECT COUNT(*) FROM author) / 100;
</pre>

[pic3]

### 5.1.4. What was the most influential (in terms of N citations/ N publications) year for top 3% scientists?

<pre>
SELECT final.author_id, final.rank, final.hindex, final.pub, final.avg_cites, final.year
FROM (SELECT a.author_id, rank, sum(hindex::DECIMAL) as hindex, sum(publications::DECIMAL) as pub, sum(avg_cites::DECIMAL) as avg_cites, ar.year
    FROM (SELECT author_id, rank_total_pubs as rank, total_pubs as publications, hindex, avg_cites
    FROM author 
    ORDER BY rank_total_pubs 
    LIMIT  0.01 * (SELECT COUNT(*) FROM author) / 100) AS a
    INNER JOIN authorship au ON a.author_id = au.author_id
    INNER JOIN article ar ON au.article_id = ar.article_id
    GROUP BY a.author_id, rank, ar.year) as final
LEFT JOIN (SELECT a.author_id, rank, sum(hindex::DECIMAL) as hindex, sum(publications::DECIMAL) as pub, sum(avg_cites::DECIMAL) as avg_cites, ar.year 
    FROM (SELECT author_id, rank_total_pubs as rank, total_pubs as publications, hindex, avg_cites
    FROM author 
    ORDER BY rank_total_pubs 
    LIMIT  0.01 * (SELECT COUNT(*) FROM author) / 100) AS a
    INNER JOIN authorship au ON a.author_id = au.author_id
    INNER JOIN article ar ON au.article_id = ar.article_id
    GROUP BY a.author_id, rank, ar.year) as final1 ON 
    final.author_id = final1.author_id AND final.hindex < final1.hindex
WHERE final1.author_id IS NULL
ORDER BY final.rank 
LIMIT  0.01 * (SELECT COUNT(*) FROM author) / 100;
</pre>

<PIC>

## 5.2. Graph Database Queries
Using the graph database, the aim of the queries was to provide information about a particular author's research activity. Specifically, we wanted to see with whom and on what a given author (e.g., based on name) has collaborated. Querying graph database allows to gain insights into the ego-network of a particualr scientist. To that end, we can see the total network (with the scientist) as well as gain a first insight into how modularized is the network (when exploring the network qithout including the ego-node).

## 5.2.1. 
