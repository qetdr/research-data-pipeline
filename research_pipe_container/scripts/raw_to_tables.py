
import time # tracking time
import opendatasets as od # Kaggle datasets
import pandas as pd # Dataframes
import numpy as np # Vector operations

### --- DATA INGESTION --- ###
def ingest_data(n_rows = 1000, force = False):
    """Download the data from Kaggle URL (or use an instance from local machine)
    Args:
        n_rows (int OR str; default 1000): unumber of rows to be read. If 'all', entire file is read
        force (bool): download a file (again) if the same file found on local machine?
    Returns:
        df_raw (pd.DataFrame): pandas dataframe extracted from json format
    """
    
    # Download the data
    od.download("https://www.kaggle.com/datasets/Cornell-University/arxiv", 
                     force = force # force = True downloads the file even if it finds a file with the same name
                    )

    # Check if a number of rows is specified
    start_time = time.time()
    if n_rows == "all":
        df_raw = pd.read_json("arxiv/arxiv-metadata-oai-snapshot.json", lines = True)

    else:
        df_raw  = pd.read_json("arxiv/arxiv-metadata-oai-snapshot.json", lines = True, nrows = n_rows)

    end_time = time.time()

    print(f'Data Ingestion Time elapsed: {end_time - start_time} seconds.')
    print(f'Memory usage of raw df: {df_raw.memory_usage(deep = True).sum()/1024/1024/1024} GB.')
    print(f'Raw df dimensions: {df_raw.shape}')
    print()
    return df_raw

### --- DATA PREPROCESSING --- ###
def raw_to_df(df):
    """Data preprocessing
    """
    # Keep only relevant features
    # Drop the abstract, submitter, comments, report-no, versions, journal-ref, and license, as these features are not used in this project
        ## Of note, journal name will be retrieved later with a more standard label
    start_time = time.time()
    df_r = df.drop(['abstract', 'submitter', 'comments', 
                          'report-no', 'license', 'versions', 'journal-ref'], 
                         axis = 1)
    # Drop duplicates
    df_r = df_r.drop_duplicates(subset=['id'])
    
    # Drop publications without DOIs
    df_r = df_r[~df_r['doi'].isnull()]
    
    # Drop the publications with very short titles (less than 3 words)
    df_r = df_r[(df_r['title'].map(len) > 10)]
    df_r = df_r.reset_index(drop = True)
    
    end_time = time.time()
    
    print(f'Initial preprocessing time elapsed: {end_time - start_time} seconds.')
    print(f'Memory usage of cleaned df: {df_r.memory_usage(deep = True).sum()/1024/1024/1024} GB.')
    print(f'Cleaned df dimensions: {df_r.shape}')
    print()
    return df_r

### --- FACTS AND DIMENSIONS TABLES --- ###

###### --- authorship & author tables --- ######
def authorship_author_extract(df):
    
     #--- AUTHORSHIP TABLE ---#
    # Create the table fro article id and authors list
    ## NB! Creating `authorship_raw` - for later authors extraction
    authorship_raw = df[['id', 'authors_parsed']].set_index('id')
    authorship_raw['n_authors'] = authorship_raw['authors_parsed'].str.len()
    authorship_raw = pd.DataFrame(authorship_raw['authors_parsed'].explode()).reset_index()
    
    # Create additional columns
    authorship_raw['last_name'] = np.nan
    authorship_raw['first_name'] = np.nan
    authorship_raw['middle_name'] = np.nan

    # Update the last, first, and middle names
    for i in range(len(authorship_raw)):
        authorship_raw['last_name'][i] = authorship_raw['authors_parsed'][i][0]
        authorship_raw['first_name'][i] = authorship_raw['authors_parsed'][i][1]
        authorship_raw['middle_name'][i] = authorship_raw['authors_parsed'][i][2]

    # Drop the redundant column
    authorship_raw = authorship_raw.drop(columns = 'authors_parsed')

    # Author_identifier
    authorship_raw['author_id'] = authorship_raw['last_name'] + authorship_raw['first_name'].str[0]
    # Rename article id column
    authorship_raw = authorship_raw.rename({'id':'article_id'}, axis = 1)

    # Final table
    authorship = authorship_raw.drop(columns = ['last_name', 'first_name', 'middle_name'])
    
    #--- AUTHOR TABLE ---#
    
    # Create the table from the `authorship` table
    author = authorship_raw[['author_id', 'last_name', 'first_name', 'middle_name']]
    del authorship_raw

    # Drop duplicates
    author.drop_duplicates(keep=False,inplace=True)

    # Add the `gender` column to be augmented
    author['gender'] = np.nan
    author['affiliation'] = np.nan
    author['hindex'] = np.nan

    # Sort alphabetically by last name
    author = author.sort_values('author_id').reset_index(drop = True)
    
    return authorship, author

###### --- article_category and category tables --- ######
def article_category_category_extract(df):
    # Article-category factless fact table
    article_category = df[['id', 'categories']].set_index('id')
    article_category = pd.DataFrame(article_category['categories'].str.split(' ').explode()) # extract category codes for articles in long-df
    article_category = article_category.reset_index()
    article_category = article_category.rename(columns = {'id':'article_id', 'categories':'category_id'})
    
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
    article['article_id'] = df['id']
    article['title'] = df['title']
    article['doi'] = df['doi']
    article['n_authors'] = df['authors_parsed'].str.len() # get the number of authors
    article['year'] = df['update_date'].str.split('-').map(lambda x: x[0]).astype(int)
    return article

###### --- journal table --- ######
def journal_extract():
    # Journal table
    journal = pd.DataFrame(columns = ['journal_id', 'issn', 'title', 'if_latest'])
    return journal
