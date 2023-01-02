from neo4j import GraphDatabase
import time

class Neo4jConnection:
    # https://github.com/cj2001/bite_sized_data_science/blob/main/notebooks/part3.ipynb 
    def __init__(self, uri, user, pwd):
        self.__uri = uri
        self.__user = user
        self.__pwd = pwd
        self.__driver = None
        
        try:
            self.__driver = GraphDatabase.driver(self.__uri, auth=(self.__user, self.__pwd))
        except Exception as e:
            print("Failed to create the driver:", e)
        
    def close(self):
        
        if self.__driver is not None:
            self.__driver.close()
        
    def query(self, query, parameters=None, db=None):
        
        assert self.__driver is not None, "Driver not initialized!"
        session = None
        response = None
        
        try: 
            session = self.__driver.session(database=db) if db is not None else self.__driver.session() 
            response = list(session.run(query, parameters))
        except Exception as e:
            print("Query failed:", e)
        finally: 
            if session is not None:
                session.close()
        return response
    
# Data ingestion helper function (in batches)
def insert_data(conn, query, rows, batch_size = 1000):

    total = 0
    batch = 0
    start = time.time()
    result = None
    
    while batch * batch_size < len(rows):

        res = conn.query(query, 
                         parameters = {'rows': rows[batch*batch_size:(batch+1)*batch_size].to_dict('records')})
        total += res[0]['total']
        batch += 1
        result = {"total":total, 
                  "batches":batch, 
                  "time":time.time()-start}
        
    return result

# Add category nodes
def add_category(conn, rows):
    query = """UNWIND $rows AS row
               MERGE (:Category {id: row.category_id, superdom: row.superdom, subdom: row.subdom})
               RETURN COUNT(*) AS total
            """
    return insert_data(conn, query, rows)

# Add journal nodes
def add_journal(conn, rows):
    query = """UNWIND $rows AS row
               MERGE (:Journal {id: row.journal_issn, 
               title: row.journal_title, 
               snip: row.snip_latest})
               RETURN COUNT(*) AS total
            """
    return insert_data(conn, query, rows)

# Add author nodes
def add_author(conn, rows):
    query = """UNWIND $rows AS row
               MERGE (:Author {id: row.author_id, last_name: row.last_name, first_name: row.first_name,
            middle_name: row.middle_name, gender: row.gender, total_pubs: row.total_pubs,
            total_cites: row.total_cites, avg_cites: row.avg_cites, med_coauthors: row.med_coauthors,
            n_unique_coauthors: row.n_unique_coauthors, hindex:row.hindex,
            rank_total_pubs: row.rank_total_pubs, rank_total_cites: row.rank_total_cites,
            rank_avg_cites: row.rank_avg_cites,rank_hindex: row.rank_hindex})
               RETURN COUNT(*) AS total
            """
    return insert_data(conn, query, rows)

# Add article nodes
def add_article(conn, rows):
    query = """UNWIND $rows AS row
               MERGE (:Article {id: row.article_id, 
               title: row.title, 
               doi: row.doi,
               journal_issn: row.journal_issn,
               n_authors: row.n_authors,
               n_cites: row.n_cites, 
               year: row.year})
               RETURN COUNT(*) AS total
            """
    return insert_data(conn, query, rows)

# Add article-category relationship
def add_article_category(conn, rows):
    
    query = """UNWIND $rows AS row
               MATCH (source:Article {id: row.article_id})
               MATCH (target:Category {id: row.category_id})
               MERGE (source)-[r:BELONGS_TO]->(target)
               RETURN COUNT(r) AS total
            """
    return insert_data(conn, query, rows)

# Add authorship (author-article relation)
def add_authorship(conn, rows):
    
    query = """UNWIND $rows AS row
               MATCH (source:Author {id: row.author_id})
               MATCH (target:Article {id: row.article_id})
               MERGE (source)-[r:AUTHORED]->(target)
               RETURN COUNT(r) AS total
            """
    return insert_data(conn, query, rows)

