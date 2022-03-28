import configparser


# CONFIG
config = configparser.ConfigParser()
config.read('dwh.cfg')
ARN = config.get("IAM_ROLE", "ARN")
LOG_DATA = config.get("S3", "LOG_DATA") 
LOG_JSONPATH = config.get("S3", "LOG_JSONPATH") 
SONG_DATA = config.get("S3", "SONG_DATA") 

# DROP TABLES

staging_events_table_drop = "DROP TABLE IF EXISTS stg_events ;"
staging_songs_table_drop = "DROP TABLE IF EXISTS stg_songs ;"
songplay_table_drop = "DROP TABLE IF EXISTS songplays ;"
user_table_drop = "DROP TABLE IF EXISTS users CASCADE;"
song_table_drop = "DROP TABLE IF EXISTS songs ;"
artist_table_drop = "DROP TABLE IF EXISTS artists ;"
time_table_drop = "DROP TABLE IF EXISTS time CASCADE;"

# CREATE TABLES

staging_events_table_create= ("""
    CREATE TABLE IF NOT EXISTS stg_events 
    (
      artist VARCHAR,
      auth VARCHAR,
      firstName VARCHAR,
      gender VARCHAR,
      itemInSession INT,
      lastName VARCHAR,
      length NUMERIC,
      level VARCHAR,
      location VARCHAR,
      method VARCHAR,
      page VARCHAR,
      registration NUMERIC,
      sessionId INT,
      song VARCHAR,
      status INT,
      ts NUMERIC,
      userAgent VARCHAR,
      userId INT
    );
""")

staging_songs_table_create = ("""
    CREATE TABLE IF NOT EXISTS stg_songs
    (       
        num_songs INT,
        artist_id VARCHAR,
        artist_latitude NUMERIC,
        artist_longitude NUMERIC,
        artist_location VARCHAR,
        artist_name VARCHAR,
        song_id VARCHAR,
        title VARCHAR,
        duration NUMERIC,
        year INT
    )
""")

songplay_table_create = ("""
    CREATE TABLE IF NOT EXISTS songplays  
    (
        songplay_id INT GENERATED BY DEFAULT AS IDENTITY(0,1) PRIMARY KEY sortkey distkey, 
        start_time TIMESTAMP NOT NULL REFERENCES time (start_time), 
        user_id INT NOT NULL REFERENCES users (user_id), 
        level VARCHAR, 
        song_id VARCHAR, 
        artist_id VARCHAR, 
        session_id INT, 
        location VARCHAR, 
        user_agent VARCHAR
    ) ;
;""")

user_table_create = ("""
    CREATE TABLE IF NOT EXISTS users 
    (
        user_id INT PRIMARY KEY sortkey distkey, 
        first_name VARCHAR, 
        last_name VARCHAR, 
        gender VARCHAR, 
        level VARCHAR
    ) ;
;""")

song_table_create = ("""
    CREATE TABLE IF NOT EXISTS songs 
    (
        song_id VARCHAR PRIMARY KEY sortkey distkey, 
        title VARCHAR, 
        artist_id VARCHAR NOT NULL, 
        year INT, 
        duration NUMERIC
    ) ;
""")

artist_table_create = ("""
    CREATE TABLE IF NOT EXISTS artists 
    (
        artist_id VARCHAR PRIMARY KEY sortkey distkey, 
        name VARCHAR, 
        location VARCHAR, 
        latitude NUMERIC, 
        longitude NUMERIC
    );
""")

time_table_create = ("""
    CREATE TABLE IF NOT EXISTS time 
    (
        start_time TIMESTAMP PRIMARY KEY sortkey distkey, 
        hour INT, 
        day INT, 
        week INT, 
        month INT, 
        year INT, 
        weekday INT
    ) ;
""")

# STAGING TABLES

staging_events_copy = ("""
    COPY stg_events FROM {} 
    CREDENTIALS 'aws_iam_role={}' 
    JSON {} 
    COMPUPDATE ON REGION 'us-west-2';
""").format(LOG_DATA, ARN, LOG_JSONPATH)

staging_songs_copy = ("""
    COPY stg_songs FROM {} 
    CREDENTIALS 'aws_iam_role={}' 
    JSON 'auto' 
    COMPUPDATE ON REGION 'us-west-2';
""").format(SONG_DATA, ARN)

# FINAL TABLES

songplay_table_insert = ("""
    INSERT INTO songplays (start_time, user_id, level, song_id, artist_id, session_id, location, user_agent) 
    SELECT TIMESTAMP WITHOUT TIME ZONE 'epoch' + (stg_events.ts / 1000)  * INTERVAL '1 second' AS start_time, stg_events.userId, stg_events.level, stg_songs.song_id, stg_songs.artist_id, stg_events.sessionId, stg_events.location, stg_events.userAgent 
    FROM stg_events 
    JOIN stg_songs ON stg_events.song = stg_songs.title
    WHERE stg_events.page = 'NextSong'
;""")

user_table_insert = ("""
    INSERT INTO users (user_id, first_name, last_name, gender, level) 
    SELECT DISTINCT userId, firstName, lastName, gender, level FROM stg_events WHERE userId IS NOT NULL
;""")

song_table_insert = ("""
    INSERT INTO songs (song_id, title, artist_id, year, duration) 
    SELECT DISTINCT song_id, title, artist_id, year, duration FROM stg_songs
;""")

artist_table_insert = ("""
    INSERT INTO artists (artist_id, name, location, latitude, longitude) 
    SELECT DISTINCT artist_id, artist_name, artist_location, artist_latitude, artist_longitude FROM stg_songs
;""")

time_table_insert = ("""
    INSERT INTO time (start_time, hour, day, week, month, year, weekday) 
    SELECT DISTINCT
        TIMESTAMP WITHOUT TIME ZONE 'epoch' + (ts / 1000)  * INTERVAL '1 second' AS start_time, 
        EXTRACT(HOUR FROM TIMESTAMP WITHOUT TIME ZONE 'epoch' + (ts / 1000)  * INTERVAL '1 second') AS hour,
        EXTRACT(DAY FROM TIMESTAMP WITHOUT TIME ZONE 'epoch' + (ts / 1000)  * INTERVAL '1 second') AS day,
        EXTRACT(WEEK FROM TIMESTAMP WITHOUT TIME ZONE 'epoch' + (ts / 1000)  * INTERVAL '1 second') AS week,
        EXTRACT(MONTH FROM TIMESTAMP WITHOUT TIME ZONE 'epoch' + (ts / 1000)  * INTERVAL '1 second') AS month,
        EXTRACT(YEAR FROM TIMESTAMP WITHOUT TIME ZONE 'epoch' + (ts / 1000)  * INTERVAL '1 second') AS year,
        EXTRACT(DOW FROM TIMESTAMP WITHOUT TIME ZONE 'epoch' + (ts / 1000)  * INTERVAL '1 second') AS weekday
    FROM stg_events WHERE page = 'NextSong' 
;""")

# Summary All Tables

count_all_tables = ("""
    SELECT 'songplays' AS Tablename, COUNT(*) AS CNT FROM songplays
    UNION 
    SELECT 'users' AS Tablename, COUNT(*) AS CNT FROM users
    UNION 
    SELECT 'songs' AS Tablename, COUNT(*) AS CNT FROM songs
    UNION 
    SELECT 'artists' AS Tablename, COUNT(*) AS CNT FROM artists
    UNION 
    SELECT 'time' AS Tablename, COUNT(*) AS CNT FROM time; 
""")

# QUERY LISTS

create_table_queries = [staging_events_table_create, staging_songs_table_create, user_table_create, song_table_create, artist_table_create, time_table_create, songplay_table_create]
drop_table_queries = [staging_events_table_drop, staging_songs_table_drop, user_table_drop, song_table_drop, artist_table_drop, time_table_drop, songplay_table_drop]
copy_table_queries = [staging_events_copy, staging_songs_copy]
insert_table_queries = [songplay_table_insert, user_table_insert, song_table_insert, artist_table_insert, time_table_insert]

staging_table_list = ["stg_events", "stg_songs"]
dwh_table_list = ["songplays", "users", "songs", "artists", "time"]
