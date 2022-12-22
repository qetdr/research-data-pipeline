
import json
import time # tracking time
import opendatasets as od # Kaggle datasets
import pandas as pd # Dataframes
import numpy as np # Vector operations

### --- DATA INGESTION --- ###
def ingest_and_process(force = False):
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
    
    # Solution from here: https://stackoverflow.com/questions/54124504/read-only-specific-fields-from-large-json-and-import-into-a-pandas-dataframe
    
    # Keep only relevant features to be used later
    cols = ['id', 'authors', 'title', 'doi',
            'categories', 'update_date', 'authors_parsed']
    data = []

    with open('arxiv/arxiv-metadata-oai-snapshot.json', encoding='latin-1') as f:
        for line in f:
            doc = json.loads(line)

            lst = [doc['id'], doc['title'], doc['doi'], 
                   doc['categories'], doc['update_date'], 
                   doc['authors_parsed']]
            data.append(lst)

    df_raw = pd.DataFrame(data=data)
    df_raw.columns = ['article_id', 'title', 'doi', 'categories', 'date', 'authors_parsed']


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
    authorship_raw['last_name'] = authorship_raw['last_name'].str.replace("[,.;-]'", '', regex=True) 
    authorship_raw['first_name'] = authorship_raw['first_name'].str.replace("[,.;-]'", '', regex=True) 
    authorship_raw['middle_name'] = authorship_raw['middle_name'].str.replace("[,.;-]'", '', regex=True) 

    # Author_identifier
    authorship_raw['author_id'] = authorship_raw['last_name'] + authorship_raw['first_name'].str[0]
    
    #### --- AUTHORSHIP TABLE --- ####
    # Final authorship table
    authorship = authorship_raw.drop(columns = ['last_name', 'first_name', 'middle_name'])
    
    #### --- AUTHOR TABLE --- ####
    # Create the table from the `authorship` table
    author = authorship_raw[['author_id', 'last_name', 'first_name', 'middle_name']]

    # Drop duplicates
    author.drop_duplicates(keep=False,inplace=True)

    # Add the `gender` column to be augmented
    author['affiliation'] = np.nan
    author['hindex'] = np.nan

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
    article = pd.DataFrame(columns = ['article_id', 'title', 'doi', 'n_authors', 'journal_issn', 'n_cites', 'year'])
    article['article_id'] = df['article_id']
    article['title'] = df['title']
    article['doi'] = df['doi']
    article['n_authors'] = df['authors_parsed'].str.len() # get the number of authors
    article['year'] = df['date'].str.split('-').map(lambda x: x[0]).astype(int)
    return article

###### --- journal table --- ######
def journal_extract():
    # Journal table
    journal = pd.DataFrame(columns = ['journal_issn', 'journal_title', 'if_latest'])
    return journal
