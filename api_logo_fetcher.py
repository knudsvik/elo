"""
Fetch team logos from the football API.

This module fetches team logos directly from the API-Football service
and integrates with the existing logo management system.
"""

import os
import requests
from dotenv import load_dotenv
from const import CLUBS


def get_team_logos_from_api():
    """
    Fetch team logos from API-Football.
    
    Returns:
        dict: Mapping of team names to logo URLs
    """
    load_dotenv()
    api_key = os.getenv("RAPID_API_KEY")
    
    if not api_key:
        print("No API key found. Please set RAPID_API_KEY in .env file")
        return {}
    
    url = "https://api-football-v1.p.rapidapi.com/v3/teams"
    headers = {
        "X-RapidAPI-Key": api_key,
        "X-RapidAPI-Host": "api-football-v1.p.rapidapi.com",
    }
    
    # Eliteserien league ID is 103
    querystring = {"league": "103", "season": "2025"}
    
    try:
        response = requests.get(url, headers=headers, params=querystring)
        response.raise_for_status()
        data = response.json()
        
        team_logos = {}
        
        for team_data in data["response"]:
            team_name = team_data["team"]["name"]
            logo_url = team_data["team"]["logo"]
            
            # Map API team name to our standard name
            standard_name = None
            for standard, variants in CLUBS.items():
                if team_name in variants:
                    standard_name = standard
                    break
            
            if standard_name:
                team_logos[standard_name] = logo_url
                print(f"Found logo for {standard_name}: {logo_url}")
            else:
                print(f"Could not map team: {team_name}")
        
        return team_logos
        
    except Exception as e:
        print(f"Error fetching team logos from API: {e}")
        return {}


def update_logo_manager_with_api_logos():
    """
    Update the logo_manager.py with logos from the football API.
    
    Returns:
        dict: Updated logo URLs
    """
    api_logos = get_team_logos_from_api()
    
    if not api_logos:
        print("No logos fetched from API, using existing URLs")
        return {}
    
    # Update the existing logo_manager.py get_logo_urls function
    try:
        from logo_manager import get_logo_urls
        existing_urls = get_logo_urls()
        
        # Merge API logos with existing ones (API takes priority)
        updated_urls = {**existing_urls, **api_logos}
        
        print(f"Updated {len(api_logos)} team logos from API")
        return updated_urls
        
    except Exception as e:
        print(f"Error updating logo manager: {e}")
        return api_logos


if __name__ == "__main__":
    # Test the function
    logos = get_team_logos_from_api()
    print(f"Fetched {len(logos)} team logos from API")
    for team, url in logos.items():
        print(f"{team}: {url}")
