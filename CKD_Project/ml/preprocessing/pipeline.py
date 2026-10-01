import pandas as pd
import numpy as np
from sklearn.base import BaseEstimator, TransformerMixin
from sklearn.impute import SimpleImputer
from sklearn.preprocessing import StandardScaler

NUMERICAL_FEATURES = [
    'age', 'bp', 'sg', 'al', 'su', 'bgr', 'bu', 'sc', 'sod', 'pot',
    'hemo', 'pcv', 'wc', 'rc'
]

CATEGORICAL_FEATURES = [
    'rbc', 'pc', 'pcc', 'ba', 'htn', 'dm', 'cad', 'appet', 'pe', 'ane'
]

ALL_FEATURES = NUMERICAL_FEATURES + CATEGORICAL_FEATURES

def clean_raw_dataframe(df: pd.DataFrame) -> pd.DataFrame:
    """Cleans whitespace, tabs, and unknown symbols in raw UCI CKD data."""
    df_clean = df.copy()
    
    # Drop 'id' if present
    if 'id' in df_clean.columns:
        df_clean = df_clean.drop(columns=['id'])
        
    for col in df_clean.columns:
        if df_clean[col].dtype == object or isinstance(df_clean[col].dtype, pd.StringDtype):
            df_clean[col] = df_clean[col].astype(str).str.strip().str.replace('\t', '').str.replace("'", "")
            df_clean[col] = df_clean[col].replace({'?': np.nan, 'nan': np.nan, 'None': np.nan, '': np.nan})
            
    # Clean specific categorical anomalies
    if 'dm' in df_clean.columns:
        df_clean['dm'] = df_clean['dm'].replace({'yes': 'yes', 'no': 'no'})
    if 'cad' in df_clean.columns:
        df_clean['cad'] = df_clean['cad'].replace({'yes': 'yes', 'no': 'no'})
    if 'classification' in df_clean.columns:
        df_clean['classification'] = df_clean['classification'].replace({'ckd': 'ckd', 'notckd': 'notckd'})
        
    # Cast numerical columns to float
    for num_col in NUMERICAL_FEATURES:
        if num_col in df_clean.columns:
            df_clean[num_col] = pd.to_numeric(df_clean[num_col], errors='coerce')
            
    return df_clean

class CKDPreprocessor(BaseEstimator, TransformerMixin):
    """
    Scikit-learn compatible preprocessor for CKD clinical dataset.
    Ensures that imputers and encodings are fitted strictly on training data.
    """
    def __init__(self):
        self.num_imputer = SimpleImputer(strategy='median')
        self.scaler = StandardScaler()
        self.cat_mappings = {
            'rbc': {'normal': 0, 'abnormal': 1},
            'pc': {'normal': 0, 'abnormal': 1},
            'pcc': {'notpresent': 0, 'present': 1},
            'ba': {'notpresent': 0, 'present': 1},
            'htn': {'no': 0, 'yes': 1},
            'dm': {'no': 0, 'yes': 1},
            'cad': {'no': 0, 'yes': 1},
            'appet': {'good': 0, 'poor': 1},
            'pe': {'no': 0, 'yes': 1},
            'ane': {'no': 0, 'yes': 1}
        }
        self.cat_modes = {}
        self.feature_names = NUMERICAL_FEATURES + CATEGORICAL_FEATURES

    def fit(self, X: pd.DataFrame, y=None):
        X_clean = clean_raw_dataframe(X)
        
        # Fit numerical imputer and scaler
        X_num = X_clean[NUMERICAL_FEATURES]
        self.num_imputer.fit(X_num)
        X_num_imp = self.num_imputer.transform(X_num)
        self.scaler.fit(X_num_imp)
        
        # Fit categorical mode replacements
        for cat_col in CATEGORICAL_FEATURES:
            mode_val = X_clean[cat_col].mode()
            self.cat_modes[cat_col] = mode_val.iloc[0] if not mode_val.empty else 'no'
            
        return self

    def transform(self, X: pd.DataFrame) -> pd.DataFrame:
        X_clean = clean_raw_dataframe(X)
        
        # Transform numericals
        X_num = X_clean[NUMERICAL_FEATURES]
        X_num_imp = self.num_imputer.transform(X_num)
        X_num_scaled = self.scaler.transform(X_num_imp)
        df_num = pd.DataFrame(X_num_scaled, columns=NUMERICAL_FEATURES, index=X_clean.index)
        
        # Transform categoricals
        df_cat = pd.DataFrame(index=X_clean.index)
        for cat_col in CATEGORICAL_FEATURES:
            series = X_clean[cat_col].fillna(self.cat_modes.get(cat_col, 'no'))
            mapping = self.cat_mappings[cat_col]
            default_code = mapping.get(self.cat_modes.get(cat_col, 'no'), 0)
            df_cat[cat_col] = series.map(mapping).fillna(default_code).astype(int)
            
        # Combine in exact feature order
        df_transformed = pd.concat([df_num, df_cat], axis=1)[self.feature_names]
        return df_transformed
