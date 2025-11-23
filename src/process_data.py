import pandas as pd
import glob
import os
import sys

def process_data():
    print("🔄 Starting Data Processing...")

    # UPDATED: Paths are now relative to the root folder
    raw_path = os.path.join("data", "raw")
    processed_path = os.path.join("data", "processed")
    os.makedirs(processed_path, exist_ok=True)

    # 2. Load all CSV files from raw folder
    all_files = glob.glob(os.path.join(raw_path, "*.csv"))
    
    if not all_files:
        print(f"❌ No raw data found in {raw_path}. Please run the scraper first.")
        sys.exit(1)

    print(f"📂 Found {len(all_files)} CSV files. Merging...")
    
    df_list = []
    for filename in all_files:
        try:
            df = pd.read_csv(filename)
            df_list.append(df)
        except Exception as e:
            print(f"⚠️ Error reading {filename}: {e}")

    if not df_list:
        print("❌ No valid data extracted.")
        sys.exit(1)

    raw_df = pd.concat(df_list, ignore_index=True)
    
    # 3. Feature Engineering
    print("🛠️  Engineering Features...")
    
    # Clean duplicates based on URL Code
    raw_df.drop_duplicates(subset=['URL Code'], inplace=True)

    # Fill missing captions
    raw_df['Caption'] = raw_df['Caption'].fillna('')

    # Create Feature: Caption Length
    raw_df['caption_length'] = raw_df['Caption'].apply(len)

    # Create Feature: Hashtag Count (roughly)
    raw_df['hashtag_count'] = raw_df['Caption'].apply(lambda x: x.count('#'))

    # Convert Date to Datetime objects
    raw_df['Date'] = pd.to_datetime(raw_df['Date'])

    # Create Temporal Features
    raw_df['post_hour'] = raw_df['Date'].dt.hour
    raw_df['post_day_of_week'] = raw_df['Date'].dt.dayofweek

    # 4. Select Columns for ML
    ml_df = raw_df[['Likes', 'Comments', 'caption_length', 'hashtag_count', 'post_hour', 'post_day_of_week']]
    
    ml_df = ml_df.fillna(0)

    # 5. Save Processed Data
    output_file = os.path.join(processed_path, "training_data.csv")
    ml_df.to_csv(output_file, index=False)
    
    print(f"✅ Data processed successfully! Shape: {ml_df.shape}")
    print(f"📁 Saved to: {output_file}")

if __name__ == "__main__":
    process_data()