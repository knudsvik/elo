"""
Simulation analysis for Eliteserien ELO analysis.

This module provides functionality to create comprehensive tables and
visualizations combining ELO ratings, expected points, European competition
probabilities, and performance metrics for Eliteserien teams.
"""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt


def create_comprehensive_table(table_mean, position_probs, stats_tracker,
                               current_table, elo_df):
    """
    Create a comprehensive table with all requested metrics.

    Args:
        table_mean: DataFrame with expected final table (Team, Position,
                   Exp Points)
        position_probs: DataFrame with position probabilities for each team
        stats_tracker: Dict with simulation statistics for each team
        current_table: DataFrame with current league table
        elo_df: DataFrame with ELO ratings (Club, Elo columns)

    Returns:
        DataFrame: Comprehensive table with all metrics
    """
    # Start with the expected points table
    summary_df = table_mean[['Team', 'Exp Points']].copy()
    
    # Rename columns to Norwegian
    summary_df = summary_df.rename(columns={
        'Team': 'Lag',
        'Exp Points': 'Forventede poeng'
    })

    # Add current ELO ratings
    elo_ratings = []
    for team in summary_df['Lag']:
        team_elo_query = elo_df[elo_df['Club'] == team]['Elo']
        team_elo = team_elo_query.iloc[0] if len(team_elo_query) > 0 else 0
        elo_ratings.append(team_elo)
    summary_df['Current ELO'] = elo_ratings

    # Add probabilities for different positions
    # Champion (1st place only)
    if 1 in position_probs.columns:
        champion_prob = position_probs[1].reindex(summary_df['Lag'],
                                                  fill_value=0).values
    else:
        champion_prob = pd.Series(0.0, index=summary_df.index)
    summary_df['Vinner (%)'] = champion_prob

    # Champions League (1st and 2nd place)
    cl_prob = pd.Series(0.0, index=summary_df.index)
    for pos in [1, 2]:
        if pos in position_probs.columns:
            reindexed = position_probs[pos].reindex(summary_df['Lag'],
                                                    fill_value=0)
            cl_prob += reindexed.values
    summary_df['CL (%)'] = cl_prob

    # Europe League (1st, 2nd, or 3rd place - cumulative)
    europe_prob = pd.Series(0.0, index=summary_df.index)
    for pos in [1, 2, 3]:
        if pos in position_probs.columns:
            reindexed = position_probs[pos].reindex(summary_df['Lag'],
                                                    fill_value=0)
            europe_prob += reindexed.values
    summary_df['Europa League (%)'] = europe_prob

    # Conference League (1st, 2nd, 3rd, or 4th place - cumulative)
    conference_prob = pd.Series(0.0, index=summary_df.index)
    for pos in [1, 2, 3, 4]:
        if pos in position_probs.columns:
            reindexed = position_probs[pos].reindex(summary_df['Lag'],
                                                    fill_value=0)
            conference_prob += reindexed.values
    summary_df['Conference League (%)'] = conference_prob

    # Relegation (15th and 16th place)
    rel_prob = pd.Series(0.0, index=summary_df.index)
    for pos in [15, 16]:
        if pos in position_probs.columns:
            reindexed = position_probs[pos].reindex(summary_df['Lag'],
                                                    fill_value=0)
            rel_prob += reindexed.values
    summary_df['Nedrykk (%)'] = rel_prob

    # Calculate under/overperformance (expected final position vs ELO ranking)
    # First, create ELO ranking for ONLY Eliteserien teams
    eliteserien_teams = summary_df['Lag'].tolist()
    elo_subset = elo_df[elo_df['Club'].isin(eliteserien_teams)]
    elo_ranking = elo_subset[['Club', 'Elo']].copy()
    elo_ranking = elo_ranking.sort_values('Elo', ascending=False)
    elo_ranking = elo_ranking.reset_index(drop=True)
    elo_ranking['ELO_Rank'] = range(1, len(elo_ranking) + 1)

    # Merge to get ELO ranking for each team
    elo_rank_dict = dict(zip(elo_ranking['Club'], elo_ranking['ELO_Rank']))

    # Calculate position difference (ELO rank - expected final position)
    # Positive = expected to finish better than ELO ranking suggests
    # Negative = expected to finish worse than ELO ranking suggests
    position_diff_data = []
    for team in summary_df['Lag']:
        elo_rank = elo_rank_dict.get(team, 16)  # Default to last if not found
        team_data = table_mean[table_mean['Team'] == team]['Position']
        expected_pos = team_data.iloc[0]
        diff = elo_rank - expected_pos  # Positive = outperforming ELO
        position_diff_data.append(diff)

    summary_df['Posisjon diff'] = position_diff_data

    # Calculate uncertainty (standard deviation of points)
    uncertainty_data = []
    for team in summary_df['Lag']:
        if team in stats_tracker and len(stats_tracker[team]['Points']) > 0:
            points_std = np.std(stats_tracker[team]['Points'])
            uncertainty_data.append(points_std)
        else:
            uncertainty_data.append(0.0)

    summary_df['Usikkerhet'] = uncertainty_data

    # Round all percentage columns and ensure no NaN values
    prob_columns = ['Vinner (%)', 'CL (%)',
                    'Europa League (%)', 'Conference League (%)',
                    'Nedrykk (%)']
    for col in prob_columns:
        summary_df[col] = summary_df[col].fillna(0).round(1)

    # Round other numeric columns and handle NaN
    summary_df['Forventede poeng'] = (summary_df['Forventede poeng']
                                      .fillna(0).round(1))
    elo_series = pd.Series(elo_ratings).fillna(0).round(0).astype(int)
    summary_df['Nåværende ELO'] = elo_series
    pos_diff_series = pd.Series(position_diff_data).fillna(0)
    summary_df['Posisjon diff'] = pos_diff_series.round(0).astype(int)
    summary_df['Usikkerhet'] = pd.Series(uncertainty_data).fillna(0).round(2)

    # Sort by expected points (descending)
    summary_df = summary_df.sort_values('Forventede poeng', ascending=False)
    summary_df = summary_df.reset_index(drop=True)

    # Add rank column
    summary_df.insert(0, 'Plass', range(1, len(summary_df) + 1))

    # Reorder columns: Rank, Team, Current ELO, Exp Points,
    # then probabilities, then performance metrics
    column_order = [
        'Plass', 'Lag', 'Nåværende ELO', 'Forventede poeng',
        'Vinner (%)', 'CL (%)', 'Europa League (%)',
        'Conference League (%)', 'Nedrykk (%)',
        'Posisjon diff', 'Usikkerhet'
    ]
    summary_df = summary_df[column_order]

    return summary_df


def create_season_dashboard(table_mean, position_probs, stats_tracker,
                            current_table, elo_df, season=2025):
    """
    Create a simplified dashboard with just position uncertainty and
    current vs expected position comparison.

    Args:
        table_mean: DataFrame with expected final table
        position_probs: DataFrame with position probabilities
        stats_tracker: Dict with simulation statistics
        current_table: DataFrame with current league table
        elo_df: DataFrame with ELO ratings
        season: Season year for title

    Returns:
        matplotlib.figure.Figure: Dashboard figure
    """
    # Set up the figure with 2 subplots side by side
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(16, 8))

    # 1. Current vs Expected Position Comparison (Left)
    plot_table_comparison(ax1, current_table, table_mean, elo_df)

    # 2. Position Uncertainty (Right)
    plot_position_uncertainty(ax2, stats_tracker)

    plt.tight_layout()
    plt.suptitle(f'Eliteserien {season} - ELO Analysis',
                 fontsize=16, fontweight='bold', y=0.95)

    return fig


def plot_table_comparison(ax, current_table, expected_table, elo_df):
    """Compare current standings with ELO-predicted final table."""
    # Merge current and expected positions
    current_table = current_table.copy()
    expected_table = expected_table.copy()

    current_table['Current_Pos'] = range(1, len(current_table) + 1)
    current_cols = ['Team', 'Current_Pos', 'Points']
    current_renamed = current_table[current_cols].rename(
        columns={'Points': 'Current_Points'})

    expected_cols = ['Team', 'Position', 'Exp Points']
    expected_renamed = expected_table[expected_cols].rename(
        columns={'Position': 'Expected_Pos', 'Exp Points': 'Expected_Points'})

    comparison = pd.merge(current_renamed, expected_renamed, on='Team')

    # Add ELO ratings
    comparison = pd.merge(comparison, elo_df[['Club', 'Elo']],
                          left_on='Team', right_on='Club', how='left')

    pos_change = comparison['Current_Pos'] - comparison['Expected_Pos']
    comparison['Position_Change'] = pos_change
    pts_diff = comparison['Current_Points'] - comparison['Expected_Points']
    comparison['Points_Above_Expected'] = pts_diff

    # Sort by expected position
    comparison = comparison.sort_values('Expected_Pos')

    # Create the plot
    y_pos = np.arange(len(comparison))

    # Plot current vs expected position
    colors = ['green' if x > 0 else 'red' if x < 0 else 'grey'
              for x in comparison['Position_Change']]
    ax.barh(y_pos, comparison['Position_Change'], color=colors)

    ax.set_yticks(y_pos)
    ax.set_yticklabels(comparison['Team'])
    ax.set_xlabel('Positions Above Expected (Current vs ELO Prediction)')
    ax.set_title('Current Position vs ELO Expectation')
    ax.axvline(0, color='black', linestyle='-', alpha=0.3)
    ax.grid(True, alpha=0.3)


def plot_position_uncertainty(ax, stats_tracker):
    """Show how certain the model is about each team's final position."""
    uncertainties = []
    for team, stats in stats_tracker.items():
        points_std = np.std(stats['Points'])
        uncertainties.append({'Team': team, 'Points_Std': points_std})

    uncertainty_df = pd.DataFrame(uncertainties)
    uncertainty_df = uncertainty_df.sort_values('Points_Std', ascending=True)

    y_pos = np.arange(len(uncertainty_df))
    bars = ax.barh(y_pos, uncertainty_df['Points_Std'])

    # Color bars based on uncertainty level
    for i, bar in enumerate(bars):
        std_val = uncertainty_df.iloc[i]['Points_Std']
        q75 = uncertainty_df['Points_Std'].quantile(0.75)
        q25 = uncertainty_df['Points_Std'].quantile(0.25)
        if std_val > q75:
            bar.set_color('red')
        elif std_val < q25:
            bar.set_color('green')
        else:
            bar.set_color('orange')

    ax.set_yticks(y_pos)
    ax.set_yticklabels(uncertainty_df['Team'])
    ax.set_xlabel('Points Standard Deviation')
    ax.set_title('Position Uncertainty')
    ax.grid(True, alpha=0.3)


def create_social_media_chart(position_probs, table_mean,
                              chart_type="simplified_dashboard",
                              stats_tracker=None, current_table=None,
                              elo_df=None):
    """
    Create social media friendly charts.

    Args:
        position_probs: DataFrame with position probabilities
        table_mean: DataFrame with expected final table
        chart_type: Type of chart to create
        stats_tracker: Dict with simulation statistics (optional)
        current_table: DataFrame with current league table (optional)
        elo_df: DataFrame with ELO ratings (optional)

    Returns:
        matplotlib.figure.Figure: Chart figure
    """
    if chart_type == "simplified_dashboard":
        # Create the simplified 2-panel dashboard
        if stats_tracker is None or current_table is None or elo_df is None:
            raise ValueError("For simplified_dashboard, need stats_tracker, "
                             "current_table, and elo_df")

        fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 6))

        plot_table_comparison(ax1, current_table, table_mean, elo_df)
        plot_position_uncertainty(ax2, stats_tracker)

        plt.tight_layout()
        title = 'Eliteserien 2025 - Current vs Expected & Position Uncertainty'
        plt.suptitle(title, fontsize=14, fontweight='bold', y=0.95)
        return fig

    elif chart_type == "position_comparison":
        # Just the position comparison chart
        if current_table is None or elo_df is None:
            raise ValueError("For position_comparison, need current_table "
                             "and elo_df")

        fig, ax = plt.subplots(figsize=(10, 8))
        plot_table_comparison(ax, current_table, table_mean, elo_df)
        plt.tight_layout()
        return fig

    elif chart_type == "position_uncertainty":
        # Just the uncertainty chart
        if not stats_tracker:
            raise ValueError("For position_uncertainty, need stats_tracker")

        fig, ax = plt.subplots(figsize=(10, 8))
        plot_position_uncertainty(ax, stats_tracker)
        plt.tight_layout()
        return fig

    else:
        raise ValueError(f"Unknown chart_type: {chart_type}")


def create_dashboard_figures(table_mean, position_probs, stats_tracker,
                             current_table, elo_df):
    """
    Create all dashboard figures for easy access.

    Args:
        table_mean: DataFrame with expected final table
        position_probs: DataFrame with position probabilities
        stats_tracker: Dict with simulation statistics
        current_table: DataFrame with current league table
        elo_df: DataFrame with ELO ratings

    Returns:
        dict: Dictionary with all figure objects
    """
    figures = {}

    # Main dashboard
    figures['dashboard'] = create_season_dashboard(
        table_mean, position_probs, stats_tracker, current_table, elo_df
    )

    # Social media friendly version
    figures['social_media'] = create_social_media_chart(
        position_probs, table_mean,
        chart_type="simplified_dashboard",
        stats_tracker=stats_tracker,
        current_table=current_table,
        elo_df=elo_df
    )

    # Individual charts
    figures['position_comparison'] = create_social_media_chart(
        position_probs, table_mean,
        chart_type="position_comparison",
        current_table=current_table,
        elo_df=elo_df
    )

    figures['uncertainty'] = create_social_media_chart(
        position_probs, table_mean,
        chart_type="position_uncertainty",
        stats_tracker=stats_tracker
    )

    return figures


def setup_logos(fetch_logos=False):
    """
    Setup team logos, optionally fetching from Football API.
    
    Args:
        fetch_logos: Whether to actually fetch logos from API
                    (False by default)
    
    Returns:
        bool: True if logos are available, False otherwise
    """
    try:
        from logo_manager import download_all_logos
        logo_paths = download_all_logos(fetch_logos=fetch_logos)
        return len(logo_paths) > 0
            
    except Exception as e:
        print(f"Could not set up logos: {e}")
        return False


def display_comprehensive_analysis(comprehensive_table,
                                   iterations=None,
                                   fetch_logos=False):
    """
    Display the comprehensive table with logos and clean formatting.

    Args:
        comprehensive_table: DataFrame from create_comprehensive_table()
        iterations: Number of iterations used in simulation (optional)
        fetch_logos: Whether to fetch logos from API (False by default)
    """
    from IPython.display import display, HTML

    # Try to set up logos
    logos_available = setup_logos(fetch_logos=fetch_logos)

    if iterations:
        title = (f"ELITESERIEN 2025 - SIMULERING "
                 f"({iterations} iterasjoner)")
    else:
        title = "ELITESERIEN 2025 - SIMULERING"

    print(title)
    print("=" * len(title))

    if logos_available:
        # Create a copy of the table with logos
        display_table = comprehensive_table.copy()

        try:
            from logo_manager import create_logo_html

            # Replace team names with logo + name HTML
            display_table['Lag'] = display_table['Lag'].apply(
                lambda team: create_logo_html(team, size=20)
            )

            # Create minimal CSS to prevent wrapping in team column
            html_table = display_table.to_html(index=False, escape=False)
            styled_html = f"""
            <style>
            table {{
                table-layout: auto;
                border-collapse: collapse;
            }}
            table td:nth-child(2) {{
                white-space: nowrap;
                padding-left: 8px;
            }}
            table td {{
                padding: 4px 8px;
            }}
            </style>
            {html_table}
            """

            # Display table with minimal styling to prevent wrapping
            display(HTML(styled_html))
            
        except Exception as e:
            print(f"Could not display with logos: {e}")
            # Fallback to regular display
            display(HTML(comprehensive_table.to_html(index=False)))
    else:
        # Fallback to regular display without logos
        display(HTML(comprehensive_table.to_html(index=False)))

    pos_diff_explanation = ("- Posisjon diff: ELO-rangering vs forventet "
                            "sluttposisjon (positivt = bedre enn ELO)")
    print(pos_diff_explanation)
    print("- Usikkerhet: Standardavvik av simulerte sluttpoeng")
