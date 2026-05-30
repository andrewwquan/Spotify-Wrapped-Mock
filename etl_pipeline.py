import pandas as pd
import glob
import os
from sqlalchemy import create_engine
from dotenv import load_dotenv

load_dotenv()  # Load environment variables from .env file

# --- CONFIGURATION ---
DB_USER = 'postgres'
DB_PASSWORD = os.getenv('DB_PASSWORD')
DB_HOST = 'localhost'
DB_PORT = '5432'
DB_NAME = 'postgres'
TABLE_NAME = 'spotify_streaming_history'

# Folder where your JSON files are stored
DATA_FOLDER = 'data' 

def process_data():
    # 1. ESTABLISH CONNECTION
    connection_string = f'postgresql+psycopg2://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}'
    engine = create_engine(connection_string)
    print("✅ Database connection established.")

    # 2. EXTRACT (Find and read all JSON files)
    # Spotify splits data into multiple files (StreamingHistory0.json, StreamingHistory1.json, etc.)
    json_pattern = os.path.join(DATA_FOLDER, 'StreamingHistory*.json')
    file_list = glob.glob(json_pattern)
    
    if not file_list:
        print("❌ No files found! Check your 'data' folder path.")
        return

    dfs = []
    for file in file_list:
        print(f"   -> Reading file: {file}")
        data = pd.read_json(file)
        dfs.append(data)

    # Combine all files into one DataFrame
    df = pd.concat(dfs, ignore_index=True)
    print(f"✅ Extracted {len(df)} rows of raw data.")

    # 3. TRANSFORM (Clean and Standardize)
    # Rename columns to snake_case for better SQL compatibility
    df.rename(columns={
        'endTime': 'end_time',
        'artistName': 'artist_name',
        'trackName': 'track_name',
        'msPlayed': 'ms_played'
    }, inplace=True)

    # Convert 'end_time' to a proper datetime format
    df['end_time'] = pd.to_datetime(df['end_time'])

    # Add a 'minutes_played' column for easier analysis
    df['minutes_played'] = df['ms_played'] / 60000

# 4. LOAD (Push to PostgreSQL)
    print("⏳ Loading data into PostgreSQL...")
    
    from sqlalchemy import text
    
    # This block forces PostgreSQL to drop the table AND any dependent views (CASCADE)
    with engine.begin() as conn:
        conn.execute(text(f"DROP TABLE IF EXISTS {TABLE_NAME} CASCADE"))
        
    # Now load the fresh data safely
    df.to_sql(TABLE_NAME, engine, if_exists='replace', index=False)
    
    print("✅ Data successfully loaded into the database!")


if __name__ == "__main__":
    process_data()