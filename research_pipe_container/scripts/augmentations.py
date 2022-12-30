from tqdm import tqdm
import pandas as pd # Dataframes
import numpy as np # Vector operations
from math import floor

# Crossref API 
def fetch_article_augments(start_range, end_range):
    """Helper function for fetching article data based by DOI
    From the Crossref API. 'article' table must exist.
    Args:
        start_range (int): the start row index of the batch
        end_range (int): the end row index of the batch
    """    
    start_crossref = time.time()
    print(time.ctime())
    print(f'Processing batch {start_range}-{end_range}')
    print()
    
    # Use Base URL for DOI query
    base_url = 'http://api.crossref.org/works/'
    
    for i in range(start_range, end_range, 1): # don't use tqdm if range specified like that...
        try:
            # Check if the value in work type is of len 3 ('NaN')
            if len(article['type'].astype(str)[i]) == 3:
                doi = base_url + article.loc[i, 'doi'] # append the doi for the base URL
                rqst = requests.get(doi) # request by URL
                qr_result = rqst.json() # get the json

                if qr_result['status'] == 'ok': # if request successful, make the queries, update fields
                    msg = qr_result['message']
                    work_type = msg['type']

                    article.loc[i, 'type'] = work_type # add work type
                    article.loc[i, 'n_cites'] =  qr_result['message']['is-referenced-by-count'] # add reference count

                    try: 
                        article.loc[i, 'journal_issn'] =  qr_result['message']['ISSN'][0] # add journal ISSN
                    except:
                        pass
                else:
                    pass
        except:
            print(f'There was somekind of error at request nr {i}')
            print(f'Continuing with next iterations...')
            print()
            continue
   
    end_crossref = time.time()
    
    # Overwrite the csv
    print(f'Batch ({start_range}-{end_range}) processing complete, writing to csv...')
    print(f'Time taken for the batch: {round((end_crossref - start_crossref)/60,4)} minutes.')
    article.to_csv('tables/article.csv', index = False)
    print(f'New data written to .csv')

# Journal augmentations
def find_journal_stats(journal_table, ext_data):
    """Find the title and impact metric of a journal based on ISSN
    The present script is for CWTS journal dataset
    Args: 
        journal_table (pd.DataFrame): name of the 'journal' table
        ext_data (pd.DataFrame): the data which includes journal information
    """
    print('Matching journal ISSNs with names and SNIPs...')
    
    for i in tqdm(range(len(journal_table))):
        journal_issn = journal_table.loc[i, 'journal_issn']

        if pd.isna(journal_table.loc[i,'journal_title']):

            if journal_issn in ext_data['print_issn'].values or journal_issn in ext_data['electronic_issn'].values:
                idx = ext_data[ext_data['print_issn'] == journal_issn].index

                if len(idx) == 0:
                        pass
                else:
                    idx = idx.values[0]
                    journal_table.loc[i, 'journal_title'] = ext_data.loc[idx, 'source_title'] # get the gender
                    journal_table.loc[i, 'snip_latest'] = ext_data.loc[idx, 'snip'] # get the gender
               #     print(journal.iloc[i])
                    pass
        else:
            pass
    
    print('Removing ISSNs with missing data...')
    journal = journal_table[~journal_table['journal_title'].isnull()]
    
    return journal


# Compute h-index
def hindex(citations_list, npubs):
    """Using binary search to compute h-index
    Inspiration from here: 
    https://www.geeksforgeeks.org/find-h-index-for-sorted-citations-using-binary-search/
    Args:
        citations_list (np.array): sorted (descendending) array with citations
        npubs (int): number of papers in total 
    Returns:
        hindex (int): h-index
    """
    
    hindex = 0
    
    # setting the range for binary search
    low = 0; high = npubs - 1
    
    while (low <= high):
        mid = floor((low + high)/2)
        
        if (citations_list[mid] >= (mid + 1)):
            low = mid + 1
            hindex = mid + 1
        else:
            high = mid - 1
    return int(hindex)