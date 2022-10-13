# A data pipeline to analyze scientific publications data
### 'Data Engineering' (LTAT.02.007) course project

## Team
Dmitri Rozgonjuk <br>
Eerik Sven Puudist <br>
Lisanne Siniväli <br>
ChengHan Chung <br>

## Resources
- Google Drive: https://drive.google.com/drive/folders/1IDYaNn0kvyiB37LL9aF61I5tshlyzpCS
- Overleaf (write-up of the project): https://www.overleaf.com/project/6346e5ce25d48976778453a7

## Present Tasks
Below are the individual tasks regarding the projects that need to be completed. Legend:

:white_check_mark: - completed task; :large_orange_diamond: - in progress; :x: - not started/not completed

- :large_orange_diamond: Define the conceptual goal
    - all the subsequent tasks depend on this
- :x: Design a rough sketch of the pipeline
- :x: Access the data
- :large_orange_diamond: to be added ...

## Project Timeline :calendar:
As of today (13.10.2022), there are is no clear deadline information (other than 15.12). 
- **19.10**: data modeling goals are defined
- ...
- **15.12**: Project submission

## Project Requirements
Below is the information regarding the project requirements provided by the course instructors.

### Objective
To practice the different concepts and modeling techniques and build multi-faceted analytical views on scientific publications data. One view is to build a data cube that can answer BI queries, i.e., building a data warehouse or a data mart. The queries can be in the form of ranking authors in a scientific discipline, computing authors, journals, and publishers’ H-index. Another view is to utilize graph databases to query for, e.g., co-authorship prediction, and analyzing communities. Other views, e.g., using document databases, could serve as an intermediate stage to systematically load and extract the data for the other analytical views. Another objective is to make the process repeatable. That is, you rerun the pipeline to ingest new batches of the data, simulating what happens in reality.

### Dataset
You start from the ArXiv data set, https://www.kaggle.com/datasets/Cornell- University/arxiv?resource=download. **You don’t have to work with all the data**. You can select, e.g., 200K records. Furthermore, split them into partitions e.g., 50K each and then feed them on iterations to the pipeline to simulate an incremental update to the target DW and Graph database.

### DWH View
*It is recommended to use Postgres or MySQL as an RDBMS.*

You need to **build a start/snowflake schema** that stores the data about scientific publications. Example dimensions are authors, publication venues, scientific domain, year of publication, and authors’ affiliation. The fact table should store the records of the combinations of the different dimension values.

Queries could be to rank the authors of a given scientific discipline, compute the H-index, and Histograms the number of publications in a given topic over a given time period. You can come up with more queries. You also need to consider the attributes of the different dimension tables and your policy to handle changes in their values.

### Graph View
*It is recommended to use Neo4J as a graph database.*

You need to establish what constitutes nodes and relationships (edges) in this view. For example, authors, papers, and journals, or other publication venues are good candidates to act as nodes in the graph. Edges can represent authorship between an author and a paper, co-authorship among authors, works-for between author and affiliation, cites relationship among papers, etc. You need to come up with your proposal. 

For graph analytics tasks, you can find influential papers. You can use Page rank for this using the citation relation. Detecting communities by finding strongly connected components in relationships like co-authorship or being a member of the same scientific domain. There are readily available libraries for graph analytics in Neo4J.

### Data Transformations
#### Finding Citations
The limitation of the data set is that it does not contain references entry. We need this information and other information to enrich the data. One can use one of the following tools to enlarge the data set by first querying by the paper title. This can repeat for several cycles, two or three. We are not expecting you to do that for all the papers you have, we know that it is computation intensive. Samples from the Kaggle data set are sufficient. It is better to seed the search with papers from different domains, where each domain is a cluster of papers. You can use the "categories" in the input data set to pick 10 to 20 papers from each cluster.

The following are tools that you can query for citations:
- scholar.py — A Parser for Google Scholar (icir.org)
- REST API - Crossref
- citations - Retrieving the references in a publication automatically - Academia Stack Exchange
- Publish or Perish (harzing.com)
- DBLP for computer science publications

#### Data cleansing, enrichment, and augmentation
The following are suggestions. You need to explore the data and come up with other transformation rules.
- You can drop publications with very short titles, e.g. one word, with empty authors,
- You can drop the abstract as it is not required in the scope of this project,
- You can use the DOI key to resolve and retrieve more information about the paper and the
Crossref API's
- Defining the type of publication. The data set does not tell whether this is a conference,
workshop, symposium, article, or book. Retrieved information from CorssRef, DBLP, or Google scholar API, the BibTeX entry usually points to the publication type. For example:
  - @article means this is a journal article
  - @inproceedings, usually a conference or a workshop. You can check the booktitle entry and try to figure out whether it is a conference or a workshop
  - @book
  - Etc.
- Resolving ambiguous author names. You can use external systems like Google Scholar, DBLP, MS Research
  - We have in this repo some Python scripts that we used in a slightly similar context to resolve authors and refine their publications, https://github.com/DataSystemsGroupUT/Minaret. You can also read the paper of Minaret to help you search through the repository: https://openproceedings.org/2019/conf/edbt/EDBT19_paper_210.pdf
- Resolving ambiguous or abbreviated conference or journal names: You can use Google scholar or DBLP database
  - Google scholar APIs: https://serpapi.com/google-scholar-api
  - DBLP API: https://dblp.org/faq/How+to+use+the+dblp+search+API.html
  - You can use this also to resolve authors and publication type. Remember that this will be more costly computationally due to data transfer over the network. So, use only when no other means is helpful 
- Refining venues
  - For computer science-related publications, you can use DBLP APIs
  - You can also use Google Scholar APIs for other scientific disciplines
- Author gender: You can infer the gender from an author's first name. You can use an API like https://gender-api.com/ or can have a lookup table. 
- Normalization:
  - Field of study: In many of the papers, the attribute "categories" is defined. But the values seem ad-hoc. So, one way to pick relevant and normalized values for the field of study is to have the following classification, https://confluence.egi.eu/display/EGIG/Scientific+Disciplines, as a lookup table and match the paper's fos list to it and pick from the lookup table.
  
### Pipelines
The following figure is a suggestion of how the pipeline should look like, you can improve it or suggest more operations and pipes.

![Alt text](pipeline.png "A possible pipeline solution")

**You should implement the pipeline DAG using Airflow**
