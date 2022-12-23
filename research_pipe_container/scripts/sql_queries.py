### --- DROP TABLES --- ###
authorship_drop = "DROP TABLE IF EXISTS authorship;"
article_category_drop = "DROP TABLE IF EXISTS article_category;"
category_drop = "DROP TABLE IF EXISTS category;"
journal_drop = "DROP TABLE IF EXISTS journal;"
article_drop = "DROP TABLE IF EXISTS article;"
author_drop = "DROP TABLE IF EXISTS author;"

drop_tables = [authorship_drop, article_category_drop, 
               category_drop, article_drop, author_drop,
               journal_drop]


### --- CREATE TABLES --- ###
## authorship
authorship_create = ("""
CREATE TABLE IF NOT EXISTS authorship
(article_id VARCHAR, 
author_id VARCHAR,
PRIMARY KEY (article_id, author_id) 
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

## category
category_create =  ("""
CREATE TABLE IF NOT EXISTS category
(category_id VARCHAR,
superdom VARCHAR,
subdom VARCHAR,
PRIMARY KEY (category_id) 
);
""")

## article
article_create =  ("""
CREATE TABLE IF NOT EXISTS article
(article_id VARCHAR,
title VARCHAR,
doi VARCHAR,
n_authors INT,
journal_issn VARCHAR,
n_cites VARCHAR,
year VARCHAR,
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
affiliation VARCHAR,
hindex VARCHAR,
gender VARCHAR,
PRIMARY KEY (author_id) 
);
""")

## journal
journal_create =  ("""
CREATE TABLE IF NOT EXISTS journal
(journal_issn VARCHAR,
title VARCHAR,
snip_latest FLOAT,
PRIMARY KEY (journal_issn) 
);
""")

create_tables = [authorship_create, article_category_create, 
                 category_create, article_create, author_create, 
                 journal_create]

### --- INSERT INTO TABLES --- ###
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

## article
article_insert = ("""
INSERT INTO article (article_id, title, doi, n_authors, journal_issn, n_cites, year)
VALUES (%s, %s, %s, %s, %s, %s, %s)
ON CONFLICT (article_id) DO NOTHING
""")

## author
author_insert = ("""
INSERT INTO author (author_id, last_name, first_name, middle_name, affiliation, hindex, gender)
VALUES (%s, %s, %s, %s, %s, %s, %s)
ON CONFLICT (author_id) DO NOTHING
""")

## journal
journal_insert = ("""
INSERT INTO journal (journal_issn, journal_title, snip_latest)
VALUES (%s, %s, %s)
ON CONFLICT (journal_issn) DO NOTHING
""")

insert_tables = [authorship_insert, article_category_insert, 
                 category_insert, article_insert, author_insert, 
                 journal_insert]