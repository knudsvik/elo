"""
Logo management for Eliteserien teams.

This module handles downloading and managing club logos for use in tables
and visualizations.
"""

import os
import base64
import requests
from pathlib import Path
import urllib.parse


def get_logo_urls():
    """
    Get logo URLs for all Eliteserien teams from Football API.
    """
    from api_logo_fetcher import get_team_logos_from_api
    api_logos = get_team_logos_from_api()
    if api_logos:
        print(f"Using {len(api_logos)} logos from football API")
        return api_logos
    else:
        raise Exception("Could not fetch logos from Football API")


def download_logo(team_name, url, logos_dir='logos'):
    """
    Download a team logo from URL and save it locally.
    
    Args:
        team_name: Name of the team
        url: URL to download logo from
        logos_dir: Directory to save logos in
    
    Returns:
        str: Path to the downloaded logo file, or None if failed
    """
    try:
        # Create safe filename
        safe_name = urllib.parse.quote(team_name, safe='')
        extension = url.split('.')[-1].lower()
        if extension not in ['png', 'jpg', 'jpeg', 'svg']:
            extension = 'png'
        
        filename = f"{safe_name}.{extension}"
        filepath = os.path.join(logos_dir, filename)
        
        # Download the logo
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        
        # Save to file
        with open(filepath, 'wb') as f:
            f.write(response.content)
        
        print(f"Downloaded logo for {team_name}")
        return filepath
        
    except Exception as e:
        print(f"Failed to download logo for {team_name}: {e}")
        return None


def download_all_logos(fetch_logos=False, logos_dir='logos'):
    """
    Download all Eliteserien team logos.
    
    Args:
        fetch_logos: Whether to actually fetch logos (False by default)
        logos_dir: Directory to save logos in
    
    Returns:
        dict: Mapping of team names to local logo file paths
    """
    # Create logos directory if it doesn't exist
    Path(logos_dir).mkdir(exist_ok=True)
    
    if not fetch_logos:
        print("⏭️  Skipping logo download (fetch_logos=False)")
        # Return existing logos if available
        existing_logos = {}
        team_names = [
            'Bodø/Glimt', 'Viking', 'Brann', 'Tromsø', 'Rosenborg',
            'Molde', 'Sandefjord', 'KFUM Oslo', 'Vålerenga',
            'Fredrikstad', 'Kristiansund', 'Sarpsborg 08',
            'Ham-Kam', 'Bryne', 'Strømsgodset', 'Haugesund'
        ]
        for team_name in team_names:
            safe_name = urllib.parse.quote(team_name, safe='')
            for ext in ['svg', 'png', 'jpg', 'jpeg']:
                filepath = os.path.join(logos_dir, f"{safe_name}.{ext}")
                if os.path.exists(filepath):
                    existing_logos[team_name] = filepath
                    break
        return existing_logos
    
    print("🔄 Fetching logos from Football API...")
    logo_urls = get_logo_urls()
    logo_paths = {}
    
    for team_name, url in logo_urls.items():
        path = download_logo(team_name, url, logos_dir)
        if path:
            logo_paths[team_name] = path
    
    return logo_paths


def get_logo_base64(team_name, logos_dir='logos'):
    """
    Get a team logo as base64 encoded string for HTML embedding.
    
    Args:
        team_name: Name of the team
        logos_dir: Directory containing logo files
    
    Returns:
        str: Base64 encoded logo data, or None if not found
    """
    try:
        # Try different extensions
        safe_name = urllib.parse.quote(team_name, safe='')
        for ext in ['svg', 'png', 'jpg', 'jpeg']:
            filepath = os.path.join(logos_dir, f"{safe_name}.{ext}")
            if os.path.exists(filepath):
                with open(filepath, 'rb') as f:
                    encoded = base64.b64encode(f.read()).decode()
                    if ext == 'svg':
                        return f"data:image/svg+xml;base64,{encoded}"
                    else:
                        return f"data:image/{ext};base64,{encoded}"
        return None
    except Exception as e:
        print(f"Error getting logo for {team_name}: {e}")
        return None


def create_logo_html(team_name, size=20, logos_dir='logos'):
    """
    Create HTML img tag for a team logo.
    
    Args:
        team_name: Name of the team
        size: Size of the logo in pixels
        logos_dir: Directory containing logo files
    
    Returns:
        str: HTML img tag, or team name if logo not found
    """
    logo_data = get_logo_base64(team_name, logos_dir)
    if logo_data:
        # Add white-space: nowrap to prevent wrapping
        style = ("vertical-align: middle; margin-right: 5px; "
                 "white-space: nowrap; display: inline-block;")
        return (f'<span style="white-space: nowrap;">'
                f'<img src="{logo_data}" width="{size}" height="{size}" '
                f'style="{style}">{team_name}</span>')
    else:
        return team_name
