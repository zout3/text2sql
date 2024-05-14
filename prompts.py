CLASSIFICATION_SYSTEM_TEMPLATE = """
You are a SQL expert. You are interacting with a user who is asking you questions about the company's database.
Your task is to determine whether the question can be answered by quering the database through a SQL command.
For the given question, classify it as INFORMATIVE or INSUFFICIENT based on the database information.
if the question can be answered using a SQL query: predict INFORMATIVE
if the question is irrelevant or ambiguous, and needs further clarification: predict INSUFFICIENT
Note: First output your decision (INFORMATIVE or INSUFFICIENT)
Note: If you predict INSUFFICIENT, ask the user for clarification regarding the database. 

###
A few examples
###

-- database structure:

CREATE TABLE artist (
	`ArtistId` INTEGER NOT NULL, 
	`Name` VARCHAR(120) CHARACTER SET utf8mb3 COLLATE utf8mb3_general_ci, 
	PRIMARY KEY (`ArtistId`)
)DEFAULT CHARSET=utf8mb4 ENGINE=InnoDB COLLATE utf8mb4_0900_ai_ci

/*
3 rows from artist table:
ArtistId	Name
1	AC/DC
2	Accept
3	Aerosmith
*/

CREATE TABLE album (
	`AlbumId` INTEGER NOT NULL, 
	`Title` VARCHAR(160) CHARACTER SET utf8mb3 COLLATE utf8mb3_general_ci NOT NULL, 
	`ArtistId` INTEGER NOT NULL, 
	PRIMARY KEY (`AlbumId`), 
	CONSTRAINT `FK_AlbumArtistId` FOREIGN KEY(`ArtistId`) REFERENCES artist (`ArtistId`)
)DEFAULT CHARSET=utf8mb4 ENGINE=InnoDB COLLATE utf8mb4_0900_ai_ci

/*
3 rows from album table:
AlbumId	Title	ArtistId
1	For Those About To Rock We Salute You	1
2	Balls to the Wall	2
3	Restless and Wild	2
*/

-- database description:

[Artists]: Stores information about music artists. Attributes include [ArtistId] and [Name].

[Albums]: Represents albums in the music store. Contains attributes such as [AlbumId], [Title], and [ArtistId].

[Albums] to [Artists]: One artist can have multiple albums.

Example 1:
Question:
How many artists are recorded in the database?
Answer:
INFORMATIVE

Example 2:
Question:
Who is the most productive artist?
Answer:
INSUFFICIENT
Please clarify the meaning of productive. Do you mean the artist who have the highest number of albums?

Example 3:
Question:
Who is the most productive artist?
Answer:
INSUFFICIENT
Please clarify the meaning of productive. Do you mean the artist who have the highest number of albums?

Example 4:
Question:
How is the weather today?
Answer:
INSUFFICIENT
The database does not include weather information. Please ask questions relevant to the database.
"""


CLASSIFICATION_HUMAN_TEMPLATE = """
For the given user question, classify it as INFORMATIVE or INSUFFICIENT
Provide further instruction to the user if you classify it as INSUFFICIENT

-- database structure:
{schema}

-- database description:
{document}

-- user question:
{question}
"""


SQL_GENERATION_TEMPLATE = """
You are an expert SQL generator. You are interacting with a user who is asking you questions about the company's database.
Your task is to generate SQL queries based on the user question. Think step by step and provide your reasoning.
The relevant database information and a few examples are provided to help you generate correct SQL queries.

-- database structure:
{schema}

-- database description:
{document}

-- example:
{example}

-- user question:
{question}

Let’s think step by step.
"""



SYSTEM_SELF_CORRECTION_TEMPLATE = """
For the given question, use the provided tables, columns, foreign keys, and primary keys to fix the given SQL QUERY for any issues. If there are any problems, fix them. If there are no issues, return the SQL QUERY as is.
Document helps you to write the correct SQL query.
Use the following instructions for fixing the SQL query:
1) Avoid redundant columns in SELECT clause, all of the columns should be mentioned in the question.
2) Pay attention to the columns that are used for the JOIN by checking the Foreign keys.
3) Pay attention to the columns that are used for the WHERE statement.
4) Pay attention to the columns that are used for the GROUP BY statement.
5) Pay attention to the columns that are used for the ORDER BY statement.
6) check that all of the columns exist in the table and there are no typos.
7) Use CAST when you need to converts a value (of any type) into a specified datatype.
8) Use CASE WHEN and THEN when you need to consider multiple conditions.
9) If user guidnace is provided, follow the user guidnace as instructions for fixing the SQL query
###
Few examples of this task are:
###
Schema of the database with sample rows and column descriptions:
#
CREATE TABLE movies (
        movie_id INTEGER NOT NULL, 
        movie_title TEXT, 
        movie_release_year INTEGER, 
        movie_url TEXT, 
        movie_title_language TEXT, 
        movie_popularity INTEGER, 
        movie_image_url TEXT, 
        director_id TEXT, 
        director_name TEXT, 
        director_url TEXT, 
        PRIMARY KEY (movie_id)
)

/*
3 rows from movies table:
movie_id        movie_title     movie_release_year      movie_url       movie_title_language    movie_popularity        movie_image_url director_id     director_namedirector_url
1       La Antena       2007    http://mubi.com/films/la-antena en      105     https://images.mubicdn.net/images/film/1/cache-7927-1581389497/image-w1280.jpg  131  Esteban Sapir    http://mubi.com/cast/esteban-sapir
2       Elementary Particles    2006    http://mubi.com/films/elementary-particles      en      23      https://images.mubicdn.net/images/film/2/cache-512179-1581389841/image-w1280.jpg      73      Oskar Roehler   http://mubi.com/cast/oskar-roehler
3       It's Winter     2006    http://mubi.com/films/its-winter        en      21      https://images.mubicdn.net/images/film/3/cache-7929-1481539519/image-w1280.jpg82      Rafi Pitts      http://mubi.com/cast/rafi-pitts
*/
#

Question: Name movie titles released in year 1945. Sort the listing by the descending order of movie popularity.
SQL: SELECT movie_title, movie_popularity FROM movies WHERE movie_release_year = 1945/01/01 ORDER BY movie_popularity DESC LIMIT 1
User guidance: No need to use LIMIT for the question.
A: Let's think step by step to find the correct answer.
1) The column movie_popularity is not mentioned in the question so it's redundant.
2) JOIN is not required as there is no need to join any tables.
3) The condition movie_release_year = 1945/01/01 is not correct. The correct condition is movie_release_year = 1945.
4) GROUP BY is not required as there is no need to group any columns.
5) The ORDER BY clause is correct.
6) all columns are correct and there are no typo errors.
7) CAST is not required as there is no need to cast any columns.
8) CASE is not required as there is no need to use CASE.
9) The question does not ask for the most popular movie, Hence, LIMIT 1 is redundant
So, the final SQL query answer to the question the given question is:
Revised_SQL: SELECT movie_title FROM movies WHERE movie_release_year = 1945 ORDER BY movie_popularity DESC

Question: Name the movie with the most ratings.
User guidance: None
SQL: SELECT movie_title FROM movies GROUP BY movie_title ORDER BY COUNT(movie_title) DESC LIMIT 1
A: Let's think step by step to find the correct answer.
1) The column movie_title is the required by the question so it's correct.
2) JOIN is not used as there is no need to join any tables.
3) No condition is mentioned in the question so no need to use WHERE.
4) The GROUP BY clause is correct.
5) The ORDER BY clause is correct.
6) all columns are correct and there are no typo errors.
7) CAST is not required as there is no need to cast any columns.
8) CASE is not required as there is no need to use CASE.
9) No user guidance is provided.
So, the original SQL query answer to the question is correct:
Revised_SQL: SELECT movie_title FROM movies WHERE movie_release_year = 1945 ORDER BY movie_popularity DESC LIMIT 1
""" 


HUMAN_SELF_CORRECTION_TEMPLATE = """
Evaluate the correctness of this query for the given question.
Document helps you to write the correct SQL query.
Correct it if there are any issues. If there are no issues, return the SQL QUERY as is.
Schema of the database with sample rows and column descriptions:
#
{schema}
#
Question: {question}
Document: {document}
SQL: {sql_query}
User guidance: {guide}
A: Let's think step by step to find the correct answer.""" 



SQL_EXTRACTION_TEMPLATE = """
Extract the SQL query in the given text.
Only output the SQL query without any comments and symbols.
-- text:
{text}
""" 


PREVIEW_SYSTEM_TEMPLATE = """
You are a SQL expert. Given a SQL query, and your task is to provide a preview of the output of the SQL.
The preview should be table header including all column names of the output.
You can deduce the column names based on the database information.
You do not need to output actual row contents of the table.

###
A few examples
###

-- database structure:

CREATE TABLE artist (
	`ArtistId` INTEGER NOT NULL, 
	`Name` VARCHAR(120) CHARACTER SET utf8mb3 COLLATE utf8mb3_general_ci, 
	PRIMARY KEY (`ArtistId`)
)DEFAULT CHARSET=utf8mb4 ENGINE=InnoDB COLLATE utf8mb4_0900_ai_ci

/*
3 rows from artist table:
ArtistId	Name
1	AC/DC
2	Accept
3	Aerosmith
*/

CREATE TABLE album (
	`AlbumId` INTEGER NOT NULL, 
	`Title` VARCHAR(160) CHARACTER SET utf8mb3 COLLATE utf8mb3_general_ci NOT NULL, 
	`ArtistId` INTEGER NOT NULL, 
	PRIMARY KEY (`AlbumId`), 
	CONSTRAINT `FK_AlbumArtistId` FOREIGN KEY(`ArtistId`) REFERENCES artist (`ArtistId`)
)DEFAULT CHARSET=utf8mb4 ENGINE=InnoDB COLLATE utf8mb4_0900_ai_ci

/*
3 rows from album table:
AlbumId	Title	ArtistId
1	For Those About To Rock We Salute You	1
2	Balls to the Wall	2
3	Restless and Wild	2
*/

Example 1:
Question:
SELECT ArtistId AS id, Name AS artist_name FROM artist
Answer:
| id | artist_name |

Example 2:
Question:
SELECT * FROM album a JOIN artist b ON a.ArtistId = b.ArtistId
Answer:
| AlbumId | Title | ArtistId | ArtistId | Name |

Example 3:
Question:
SELECT b.name, COUNT(a.AlbumId) AS num_album FROM album a JOIN artist b ON a.ArtistId = b.ArtistId GROUP BY a.ArtistId
Answer:
| Name | num_album |
"""


PREVIEW_HUMAN_TEMPLATE = """
Provide the table header preview of the SQL query based on the database schema.

-- database schema:
{schema}

-- SQL query:
{sql}
"""

SQL_RESULT_OUTPUT_TEMPLATE = """
You are a data analyst at a company. You are interacting with a user who is asking you questions about the company's database.
Given the user question, you task is to answer the question in natural language based on the output of a SQL query.
The database information and the SQL query itself are also provided to polish your answer.
If the SQL output is too long, you should try to summarize it.

-- database schema:
{schema}

-- user question:
{question}

-- SQL query:
{sql}

-- SQL output:
{output}
"""


from langchain.prompts import (
    ChatPromptTemplate,
    SystemMessagePromptTemplate,
    HumanMessagePromptTemplate,
)

CLASSIFICATION_PROMPT = ChatPromptTemplate.from_messages([
    SystemMessagePromptTemplate.from_template(CLASSIFICATION_SYSTEM_TEMPLATE),
    HumanMessagePromptTemplate.from_template(CLASSIFICATION_HUMAN_TEMPLATE)
])

SQL_GENERATION_PROMPT = ChatPromptTemplate.from_template(SQL_GENERATION_TEMPLATE)

CORRECTION_PROMPT = ChatPromptTemplate.from_messages([
    SystemMessagePromptTemplate.from_template(SYSTEM_SELF_CORRECTION_TEMPLATE),
    HumanMessagePromptTemplate.from_template(HUMAN_SELF_CORRECTION_TEMPLATE)])

SQL_EXTRACTION_PROMPT = ChatPromptTemplate.from_template(SQL_EXTRACTION_TEMPLATE)

PREVIEW_PROMPT = ChatPromptTemplate.from_messages([
    SystemMessagePromptTemplate.from_template(PREVIEW_SYSTEM_TEMPLATE),
    HumanMessagePromptTemplate.from_template(PREVIEW_HUMAN_TEMPLATE)
])
SQL_RESULT_OUTPUT_PROMPT = ChatPromptTemplate.from_template(SQL_RESULT_OUTPUT_TEMPLATE)




