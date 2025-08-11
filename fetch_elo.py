import pandas as pd
import requests
from io import StringIO
from const import CLUBS

def fetch_elo_data():
    """Fetch ELO data for all clubs and return as DataFrame"""
    # Initialize list to store results
    print("Fetching the latest ELO data from ClubELO API...")
    results = []
    
    for clubs in CLUBS.values():
        try:
            # Remove spaces from club name for the API URL
            club_name_no_spaces = clubs[0].replace(" ", "")
            r = requests.get(f"http://api.clubelo.com/{club_name_no_spaces}")
            club_data = StringIO(r.text)
            df_club = pd.read_csv(club_data, sep=",")
            
            # Check if dataframe is empty
            if df_club.empty:
                continue
                
            # Convert dates to datetime for proper sorting
            df_club['From'] = pd.to_datetime(df_club['From'])
            df_club['To'] = pd.to_datetime(df_club['To'])
            
            # Sort by date to ensure chronological order
            df_club = df_club.sort_values('From')
            
            # Get the latest ELO score (last row)
            latest_elo = df_club.iloc[-1]['Elo']
            club_name = df_club.iloc[-1]['Club']
            
            # Find the first time this ELO score appeared
            first_occurrence = df_club[df_club['Elo'] == latest_elo].iloc[0]
            first_date = first_occurrence['From']
            
            # Add to results
            results.append({
                'Club': club_name,
                'Elo': latest_elo,
                'EloDate': first_date
            })
            
        except Exception as e:
            print(f"Error processing club {clubs[0]}: {e}")
            continue
    
    # Convert results to DataFrame
    df_elo = pd.DataFrame(results)
    
    # Standardise club names
    variant_to_standard = {
        variant: standard for standard, variants in CLUBS.items() for variant in variants
    }
    df_elo["Club"] = df_elo["Club"].apply(lambda x: variant_to_standard.get(x, x))

    print("ELO data fetched successfully.")
    
    return df_elo

# Optional: Create the DataFrame when script is run directly
if __name__ == "__main__":
    df_elo = fetch_elo_data()
    print(df_elo)