
import json
import time # tracking time
import opendatasets as od # Kaggle datasets
import pandas as pd # Dataframes
import numpy as np # Vector operations
from unidecode import unidecode
import os # accessing directories, make directory
from math import floor
from tqdm import tqdm
import shutil # for rmeoving a non-empty directory


### --- DATA INGESTION --- ###
def ingest_and_extract(force = False):
    """Download the data from Kaggle URL (or use an instance from local machine)
    and exclude the not needed data
    Args:
        force (bool): download a file (again) if the same file found on local machine?
    Returns:
        df_raw (pd.DataFrame): pandas dataframe extracted from json format
    """

    start_time = time.time()
    # Download the data
    od.download("https://www.kaggle.com/datasets/Cornell-University/arxiv", 
                     force = force # force = True downloads the file even if it finds a file with the same name
                    )
    
    print('Data Downloaded and unzipped!')
    print('Extracting to tables...')
    # Solution from here: https://stackoverflow.com/questions/54124504/read-only-specific-fields-from-large-json-and-import-into-a-pandas-dataframe
    # Keep only relevant features to be used later
    cols = ['id', 'authors', 'title', 'doi',
            'categories', 'update_date', 'authors_parsed']
    data = []

    with open('arxiv/arxiv-metadata-oai-snapshot.json', encoding='latin-1') as f:
        for line in tqdm(f):
            doc = json.loads(line)

            lst = [doc['id'], doc['title'], doc['doi'], 
                   doc['categories'], doc['update_date'], 
                   doc['authors_parsed']]
            data.append(lst)

    df_raw = pd.DataFrame(data=data)
    df_raw.columns = ['article_id', 'title', 'doi', 'categories', 'date', 'authors_parsed']

    print('Columns extracted!')
    print('Preparing the data...')

    # Remove records with a DOI
    df_raw = df_raw[~df_raw['doi'].isnull()]
    print(f'Dimensions of the df with valid DOIs: {df_raw.shape}')

    # Drop duplicates
    df_raw = df_raw.drop_duplicates(subset=['article_id'])
    print(f'Dimensions of the df with dropped duplicates: {df_raw.shape}')

    # Include only Computer Science papers
    df_raw = df_raw[(df_raw['categories'].str.contains('cs.')) & 
                    (~df_raw['categories'].str.contains('physics'))].reset_index(drop = True)

    # Remove records with very short titles
    df_raw = df_raw[(df_raw['title'].map(len) > 10)]
    print(f'Dimensions of the df with short titles removed: {df_raw.shape}')

    # Reset the index
    df_raw = df_raw.reset_index(drop = True)

    # Delete the .arxiv directory to save space
    shutil.rmtree('./arxiv')

    end_time = time.time()

    print(f'Dimensions of the df with only CS papers: {df_raw.shape}')
    print()
    print(f'Data Ingestion Time elapsed: {end_time - start_time} seconds.')
    print(f'Memory usage of raw df: {df_raw.memory_usage(deep = True).sum()/1024/1024/1024} GB.')
    
    return df_raw

### --- FACTS AND DIMENSIONS TABLES --- ###

###### --- authorship & author tables --- ######
def authorship_author_extract(df):
    
     #--- AUTHORSHIP TABLE ---#
    # Create the table fro article id and authors list
    ## NB! Creating `authorship_raw` - for later authors extraction
    authorship_raw = df[['article_id', 'authors_parsed']].set_index('article_id')
    authorship_raw['n_authors'] = authorship_raw['authors_parsed'].str.len()
    authorship_raw = pd.DataFrame(authorship_raw['authors_parsed'].explode()).reset_index()
    
    # Create additional columns: last_name, first_name, middle_name
    authorship_raw['last_name'] = authorship_raw['authors_parsed'].str[0]
    authorship_raw[['first_name','middle_name']] = authorship_raw['authors_parsed'].str[1].str.split(' ', expand = True).loc[:,0:1]
    # Drop the redundant column
    authorship_raw = authorship_raw.drop(columns = 'authors_parsed')

    # Clean up names (remove interpunctuation)
    ## Also apply international encoding
    authorship_raw['last_name'] = authorship_raw['last_name'].apply(unidecode)
    authorship_raw['first_name'] = authorship_raw['first_name'].apply(unidecode)
    authorship_raw['middle_name'] = authorship_raw['middle_name'].str.replace("[,.;-]", '', regex=True)
    
    authorship_raw['last_name'] = authorship_raw['last_name'].str.replace('[^a-zA-Z0-9]', '', regex=True).str.strip()
    authorship_raw['first_name'] = authorship_raw['first_name'].str.replace('[^a-zA-Z0-9]', '', regex=True).str.strip()
    authorship_raw['middle_name'] = authorship_raw['middle_name'].str.replace('[^a-zA-Z0-9]', '', regex=True).str.strip()
    
    # Author_identifier
    authorship_raw['author_id'] = authorship_raw['last_name'] + authorship_raw['first_name'].str[0]
    
    #### --- AUTHORSHIP TABLE --- ####
    # Final authorship table
    authorship = authorship_raw.drop(columns = ['last_name', 'first_name', 'middle_name'])
    
    #### --- AUTHOR TABLE --- ####
    # Create the table from the `authorship` table and drop duplicates based on ID
    author = authorship_raw[['author_id', 'last_name', 'first_name', 'middle_name']]

    # Sort alphabetically by last name
    author = author.sort_values('author_id').reset_index(drop = True)
    
    return authorship, author

###### --- article_category and category tables --- ######
def article_category_category_extract(df):
    # Article-category factless fact table
    article_category = df[['article_id', 'categories']].set_index('article_id')
    article_category = pd.DataFrame(article_category['categories'].str.split(' ').explode()) # extract category codes for articles in long-df
    article_category = article_category.reset_index()
    article_category = article_category.rename(columns = {'categories':'category_id'})
    
    # Category table
    category = pd.DataFrame(article_category['category_id'].copy().reset_index(drop = True))
    category[['superdom', 'subdom']] = category['category_id'].str.split('.', expand = True) # exract supr- and subdomain
    category = category.drop_duplicates() # drop duplicate rows
    category = category.sort_values('category_id').reset_index(drop = True) # sort values, reset index
    
    return article_category, category

###### --- article table --- ######
def article_extract(df):
    # Article table
    article = pd.DataFrame(columns = ['article_id', 'title', 'doi', 'n_authors', 'journal_issn', 'type', 'n_cites', 'year'])
    article['article_id'] = df['article_id']
    article['title'] = df['title']
    article['doi'] = df['doi']
    article['n_authors'] = df['authors_parsed'].str.len() # get the number of authors
    article['year'] = df['date'].str.split('-').map(lambda x: x[0]).astype(int)
    return article

###### --- journal table --- ######
def journal_extract():
    # Journal table
    journal = pd.DataFrame(columns = ['journal_issn', 'journal_title', 'snip_latest'])
    return journal

##### 
def ingest_and_prepare():
    start_pipe = time.time() # Initialize the time of pipeline
    start_etl = time.time() # Initialize the time of ETL
    print(f'Time of pipeline start: {time.ctime(start_pipe)}')
    print()
    # Data ingestion
    df = ingest_and_extract(force = False)

    # Prepare Pandas dataframes
    authorship, author = authorship_author_extract(df)
    article_category, category = article_category_category_extract(df)
    article = article_extract(df)
    journal = journal_extract()
    
    # Clean the data last time: remove all authors with NaNs or too short names
    ## NaNs
    author = author[~author['author_id'].isnull()]
    nan_authors = authorship[authorship['author_id'].isnull()]['article_id'].values
    article = article.loc[~article['article_id'].isin(nan_authors)]
    authorship = authorship.loc[~authorship['article_id'].isin(nan_authors)]

    ## Too short (< 4) names
    author = author[~(author['author_id'].str.len() < 4)].reset_index(drop = True)
    short_authors = authorship[(authorship['author_id'].str.len() < 4)]['article_id'].values
    article = article.loc[~article['article_id'].isin(short_authors)].reset_index(drop = True)
    authorship = authorship.loc[~authorship['article_id'].isin(short_authors)].reset_index(drop = True)
    
    ## Write .csv-s to 'tables' directory
    ### Create the 'tables' directory
    try:
        os.mkdir('dags/tables')
        print("Created directory 'tables'.")
    except:
        # It may happen that the dir already exists...
        print("Directory 'tables' exists.")
    finally:
        print('Writing pandas tables to .csv-files.')
    
    ### Write the tables as csv
   # authorship.to_csv('dags/tables/authorship.csv', index = False, sep = ';')
   # article_category.to_csv('dags/tables/article_category.csv', index = False, sep = ';')
   # category.to_csv('dags/tables/category.csv', index = False, sep = ';')
   # journal.to_csv('dags/tables/journal.csv', index = False, sep = ';')
   # article.to_csv('dags/tables/article.csv', index = False, sep = ';')
   # author.to_csv('dags/tables/author.csv', index = False, sep = ';')

    print('Pandas tables to .csv-files successfully written!')
    
    end_etl = time.time() # Endtime of ETL
    
    print()
    print(f'Initial Data Ingestion and Preparation Runtime: {round(end_etl - start_etl, 6)} sec.')
    return 

# Main function
def main():
    if os.path.exists('dags/tables') and len(os.listdir('dags/tables')) == 8: # directory + 7 tables
        print('Tables exist...')
        author = pd.read_csv('dags/tables/author.csv', error_bad_lines=False)
        authorshiphip = pd.read_csv('dags/tables/authorship.csv', error_bad_lines=False)
        article = pd.read_csv('dags/tables/article.csv', error_bad_lines=False)
        article_category = pd.read_csv('dags/tables/article_category.csv', error_bad_lines=False)
        category = pd.read_csv('dags/tables/category.csv', error_bad_lines=False)
        journal = pd.read_csv('dags/tables/journal.csv', error_bad_lines=False)
        print('Tables are in the working directory!')

    ## If tables do not exist, pull from kaggle (or local machine), proprocess to tables
    else: 
        print('Preparing tables...')
        print()
        ingest_and_prepare()
        print("Ingested and tables are in the 'dags/tables' directory!")

if __name__ == '__main__':
    main()