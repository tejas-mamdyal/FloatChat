import pandas as pd
import sys

file_path = "downloads/parquet/D20250601_prof_0.parquet"
try:
    df = pd.read_parquet(file_path)
    print("=== DTYPES ===")
    print(df.dtypes)
    print("\n=== HEAD ===")
    print(df[['profile_id', 'level_id', 'latitude', 'longitude', 'juld']].head())
    print("\n=== UNIQUE PROFILES ===")
    print(df['profile_id'].unique())
    print(df.groupby('profile_id')[['latitude', 'longitude', 'juld']].first())
except Exception as e:
    print(f"Error: {e}")
