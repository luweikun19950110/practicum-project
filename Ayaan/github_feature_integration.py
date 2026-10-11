"""
GitHub Pipeline Integration Script: Multi-Pathogen SEIR Engine to ML Feature Matrix
-----------------------------------------------------------------------------------
This script connects the multi-pathogen SEIR compartmental engine (`seir_model_v2.py`)
and data connector (`seir_data_connector.py`) directly to your repository's directory layout:
  - Input:  cleaning_outputs/, njny_commute_outputs/, population_outputs/, regional_attributes_outputs/
  - Process: Calibrates pathogen dynamics (COVID-19, Flu, Measles, Disease X) across zip codes
  - Output: Exports final ML-ready feature tables to regional_attributes_outputs/final_ml_feature_matrix.csv
"""

import os
import sys
import numpy as np
import pandas as pd

# Import local SEIR modules
from seir_model_v2 import SEIRModel, SpatialSEIRModel, PATHOGEN_PROFILES
from seir_data_connector import run_single_zip_calibration


def setup_github_directory_structure(base_dir: str = '.'):
    """Ensures expected output directories from your GitHub repo exist."""
    dirs = [
        os.path.join(base_dir, 'cleaning_outputs'),
        os.path.join(base_dir, 'njny_commute_outputs'),
        os.path.join(base_dir, 'population_outputs'),
        os.path.join(base_dir, 'regional_attributes_outputs'),
    ]
    for d in dirs:
        os.makedirs(d, exist_ok=True)
    return dirs


def generate_mock_github_data(base_dir: str = '.'):
    """
    Creates mock sample data files matching your GitHub folder schema if real files 
    are not present, allowing immediate testing and demonstration in JupyterLab.
    """
    setup_github_directory_structure(base_dir)
    
    # 1. population_outputs/zip_populations.csv
    pop_path = os.path.join(base_dir, 'population_outputs', 'zip_populations.csv')
    if not os.path.exists(pop_path):
        pop_df = pd.DataFrame({
            'zip_code': ['07102', '07302', '10001'],
            'city': ['Newark', 'Jersey City', 'New York'],
            'state': ['NJ', 'NJ', 'NY'],
            'population': [60000, 75000, 45000],
            'land_area_sqmi': [3.5, 2.1, 0.6],
            'pop_density_sqmi': [17142.8, 35714.2, 75000.0]
        })
        pop_df.to_csv(pop_path, index=False)
    
    # 2. cleaning_outputs/cleaned_cases.csv
    cases_path = os.path.join(base_dir, 'cleaning_outputs', 'cleaned_cases.csv')
    if not os.path.exists(cases_path):
        dates = pd.date_range(start='2026-01-01', periods=60, freq='D')
        records = []
        for zip_code, base_p in [('07102', 15), ('07302', 20), ('10001', 30)]:
            t = np.arange(60)
            # Simulated wave trajectory
            counts = (base_p * np.exp(0.08 * t) * (1 / (1 + np.exp(0.1 * (t - 30)))) + np.random.poisson(3, 60)).astype(int)
            counts = np.maximum(counts, 1)
            for d, c in zip(dates, counts):
                records.append({'date': d.strftime('%Y-%m-%d'), 'zip_code': zip_code, 'cases': c})
        pd.DataFrame(records).to_csv(cases_path, index=False)
        
    # 3. njny_commute_outputs/commuter_mobility_matrix.csv
    commute_path = os.path.join(base_dir, 'njny_commute_outputs', 'commuter_mobility_matrix.csv')
    if not os.path.exists(commute_path):
        # 3x3 commuter flow between Newark, Jersey City, NYC
        comm_df = pd.DataFrame([
            [0.82, 0.12, 0.06],
            [0.08, 0.78, 0.14],
            [0.03, 0.07, 0.90]
        ], index=['07102', '07302', '10001'], columns=['07102', '07302', '10001'])
        comm_df.to_csv(commute_path)

    # 4. regional_attributes_outputs/svi_demographics.csv
    svi_path = os.path.join(base_dir, 'regional_attributes_outputs', 'svi_demographics.csv')
    if not os.path.exists(svi_path):
        svi_df = pd.DataFrame({
            'zip_code': ['07102', '07302', '10001'],
            'svi_score': [0.82, 0.45, 0.28],
            'poverty_rate': [0.24, 0.11, 0.09],
            'uninsured_rate': [0.15, 0.08, 0.05],
            'crowded_housing_pct': [0.12, 0.06, 0.04]
        })
        svi_df.to_csv(svi_path, index=False)


def build_integrated_ml_feature_matrix(base_dir: str = '.', pathogen_key: str = 'covid19_omicron') -> pd.DataFrame:
    """
    Connects your GitHub folder outputs, runs SEIR feature extraction for a target pathogen,
    and merges everything into a unified dataset ready for Random Forest, XGBoost, and Dynamic Panel Models.
    """
    print(f"--- Integrating SEIR Features for Pathogen: [{pathogen_key}] ---")
    
    # Ensure sample/mock structure exists if needed
    generate_mock_github_data(base_dir)
    
    # 1. Read input files from your GitHub folders
    cases_df = pd.read_csv(os.path.join(base_dir, 'cleaning_outputs', 'cleaned_cases.csv'), dtype={'zip_code': str})
    pop_df = pd.read_csv(os.path.join(base_dir, 'population_outputs', 'zip_populations.csv'), dtype={'zip_code': str})
    svi_df = pd.read_csv(os.path.join(base_dir, 'regional_attributes_outputs', 'svi_demographics.csv'), dtype={'zip_code': str})
    
    pathogen_profile = PATHOGEN_PROFILES.get(pathogen_key, PATHOGEN_PROFILES['covid19_omicron'])
    
    # 2. Process SEIR calibration and feature engineering per zip code
    all_zip_features = []
    unique_zips = cases_df['zip_code'].unique()
    
    for z in unique_zips:
        zip_cases = cases_df[cases_df['zip_code'] == z].sort_values('date').copy()
        zip_pop_row = pop_df[pop_df['zip_code'] == z]
        pop_val = float(zip_pop_row['population'].iloc[0]) if len(zip_pop_row) > 0 else 50000.0
        
        # Extract dynamic SEIR features (R_t, velocity, acceleration, inflection point)
        seir_features = run_single_zip_calibration(
            zip_data=zip_cases, 
            zip_code=z, 
            incubation_days=1.0 / pathogen_profile.sigma, 
            infectious_days=1.0 / pathogen_profile.gamma
        )
        
        # Calculate clinical hospital demand projections
        seir_features['pathogen_name'] = pathogen_profile.name
        seir_features['est_ed_visits'] = seir_features['cases'] * pathogen_profile.ed_visit_rate
        seir_features['est_hospitalizations'] = seir_features['cases'] * pathogen_profile.hospitalization_rate
        
        all_zip_features.append(seir_features)
        
    merged_seir_df = pd.concat(all_zip_features, ignore_index=True)
    
    # 3. Merge with static geographic attributes (Population Density & SVI)
    final_df = merged_seir_df.merge(pop_df, on='zip_code', how='left')
    final_df = final_df.merge(svi_df, on='zip_code', how='left')
    
    # 4. Save feature matrix to regional_attributes_outputs/
    output_path = os.path.join(base_dir, 'regional_attributes_outputs', f'final_ml_feature_matrix_{pathogen_key}.csv')
    final_df.to_csv(output_path, index=False)
    
    print(f"Successfully generated integrated ML feature matrix ({len(final_df)} rows across {len(unique_zips)} zip codes).")
    print(f"Saved to: {output_path}")
    
    return final_df


if __name__ == '__main__':
    base_workspace = '/workspace/scratch/github_pipeline'
    
    # Run integration pipeline for COVID-19 Omicron
    covid_matrix = build_integrated_ml_feature_matrix(base_workspace, pathogen_key='covid19_omicron')
    
    # Run integration pipeline for Influenza
    flu_matrix = build_integrated_ml_feature_matrix(base_workspace, pathogen_key='seasonal_flu')
    
    print("\n--- Pipeline Sample Output Head ---")
    cols_to_show = ['date', 'zip_code', 'cases', 'seir_R_t', 'case_velocity', 'is_inflection_point', 'est_ed_visits', 'svi_score']
    print(covid_matrix[cols_to_show].head())
