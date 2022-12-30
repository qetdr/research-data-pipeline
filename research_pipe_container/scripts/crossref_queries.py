from habanero import Crossref # CrossRef API

def get_doi(doi_list):
    
    # Create a df to store DOIs, cites, journal ISSNs and journal titles
    df_doi = DOI
    
    cr = Crossref()
    
    for i in tqdm(range(len(doi_list))):
        doi = DOIs[i]
        ref_obj = cr.works(query= doi)['message']['items'][0]
        pub_type = ref_obj['type']
        print(f'Publication type: {pub_type}')

        if pub_type == 'journal-article':

            print(f'Fetching... {doi}')

            article.loc[i, 'n_cites'] = ref_obj['reference-count']

            journal_issn = ref_obj['ISSN'][0]
            journal_title = ref_obj['container-title'][0]
            print(f'Journal name: {journal_title}')
            article.loc[i, 'journal_issn'] = journal_issn

            # Update the journal dictionary
            if journal_issn not in journal_dict.keys():
                journal_dict[journal_issn] = journal_title
            else:
                pass

            print(f'DOI {doi} Fetched!')
            print()
        else:
            print('Not a journal article, passed')
            print()
            pass
