### --- DROP TABLES --- ###
article_drop = "DROP TABLE IF EXISTS article;"
author_drop = "DROP TABLE IF EXISTS author;"
authorship_drop = "DROP TABLE IF EXISTS authorship;"
category_drop = "DROP TABLE IF EXISTS category;"
article_category_drop = "DROP TABLE IF EXISTS article_category;"
journal_drop = "DROP TABLE IF EXISTS journal;"

drop_tables = [article_drop, author_drop,
               authorship_drop, category_drop, 
               article_category_drop, journal_drop]


### --- CREATE TABLES --- ###
## article
article_create =  ("""
CREATE TABLE IF NOT EXISTS article
(article_id VARCHAR,
title VARCHAR,
doi VARCHAR,
n_authors INT,
journal_issn VARCHAR,
type VARCHAR,
n_cites VARCHAR,
year INT,
PRIMARY KEY (article_id) 
);
""")

## author
author_create =  ("""
CREATE TABLE IF NOT EXISTS author
(author_id VARCHAR,
last_name VARCHAR,
first_name VARCHAR,
middle_name VARCHAR,
gender VARCHAR,
total_pubs INT,
total_cites INT,
avg_cites FLOAT,
med_coauthors FLOAT,
n_unique_coauthors INT,
hindex INT,
rank_total_pubs INT,
rank_total_cites INT,
rank_avg_cites INT,
rank_hindex INT,
PRIMARY KEY (author_id) 
);
""")

## authorship
authorship_create = ("""
CREATE TABLE IF NOT EXISTS authorship
(article_id VARCHAR, 
author_id VARCHAR, 
PRIMARY KEY (article_id, author_id) 
);
""")

## category
category_create =  ("""
CREATE TABLE IF NOT EXISTS category
(category_id VARCHAR, 
superdom VARCHAR,
subdom VARCHAR,
PRIMARY KEY (category_id) 
);
""")

## article_category
article_category_create = ("""
CREATE TABLE IF NOT EXISTS article_category
(article_id VARCHAR,  
category_id VARCHAR,
PRIMARY KEY (article_id, category_id) 
);
""")



## journal
journal_create =  ("""
CREATE TABLE IF NOT EXISTS journal
(journal_issn VARCHAR,
journal_title VARCHAR,
snip_latest FLOAT,
PRIMARY KEY (journal_issn) 
);
""")

create_tables = [article_create, author_create, 
                 authorship_create, category_create, 
                 article_category_create, journal_create]

### --- INSERT INTO TABLES --- ###
## article
article_insert = ("""
INSERT INTO article (article_id, title, doi, n_authors, journal_issn, type, n_cites, year)
VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
ON CONFLICT (article_id) DO NOTHING
""")

## author
author_insert = ("""
INSERT INTO author (author_id, last_name, first_name, middle_name, \
gender, total_pubs, total_cites, avg_cites, med_coauthors, n_unique_coauthors, \
hindex, rank_total_pubs, rank_total_cites, rank_avg_cites, rank_hindex)
VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
ON CONFLICT (author_id) DO NOTHING
""")

## authorship
authorship_insert = ("""
INSERT INTO authorship (article_id, author_id)
VALUES (%s, %s)
ON CONFLICT (article_id, author_id) DO NOTHING
""") ## ON CONFLICT (article_id) DO NOTHING <-- might need to add to the end

## article_category
article_category_insert = ("""
INSERT INTO article_category (article_id, category_id)
VALUES (%s, %s)
""")

## category
category_insert = ("""
INSERT INTO category (category_id, superdom, subdom)
VALUES (%s, %s, %s)
ON CONFLICT (category_id) DO NOTHING
""")

## journal
journal_insert = ("""
INSERT INTO journal (journal_issn, journal_title, snip_latest)
VALUES (%s, %s, %s)
ON CONFLICT (journal_issn) DO NOTHING
""")

insert_tables = [article_insert, author_insert, 
                 authorship_insert, category_insert, 
                 article_category_insert, journal_insert]
