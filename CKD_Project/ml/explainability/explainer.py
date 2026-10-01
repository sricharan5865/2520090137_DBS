import os
import sys

# Ensure project root is in sys.path before joblib load
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

import joblib
import pandas as pd
import numpy as np
import shap
from ml.preprocessing.pipeline import CKDPreprocessor, ALL_FEATURES

class CKDExplainer:
    def __init__(self, model_path: str = None):
        if model_path is None:
            model_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '../models/best_model.joblib'))
        
        artifact = joblib.load(model_path)
        self.model = artifact['model']
        self.preprocessor = artifact['preprocessor']
        self.feature_names = artifact['features']
        
        # Initialize TreeExplainer
        self.explainer = shap.TreeExplainer(self.model)

    def explain_instance(self, input_df: pd.DataFrame, top_k: int = 6):
        """
        Takes raw clinical feature DataFrame (1 row), transforms it,
        and computes SHAP feature importance for explainability.
        """
        transformed_df = self.preprocessor.transform(input_df)
        shap_values = self.explainer.shap_values(transformed_df)
        
        # In XGBoost binary classification, shap_values can be 1D array or 2D array
        if isinstance(shap_values, list):
            sv = shap_values[1][0] if len(shap_values) > 1 else shap_values[0][0]
        elif len(shap_values.shape) == 2:
            sv = shap_values[0]
        else:
            sv = shap_values
            
        feature_contributions = []
        for feat, val, s_val in zip(self.feature_names, transformed_df.iloc[0], sv):
            feature_contributions.append({
                'feature': feat,
                'transformed_value': round(float(val), 3),
                'shap_value': round(float(s_val), 4),
                'risk_impact': 'Increases CKD Risk' if s_val > 0 else 'Decreases CKD Risk',
                'magnitude': abs(float(s_val))
            })
            
        # Sort by absolute SHAP magnitude descending
        feature_contributions.sort(key=lambda x: x['magnitude'], reverse=True)
        top_factors = feature_contributions[:top_k]
        
        # Human readable clinical descriptions
        clinical_labels = {
            'hemo': 'Hemoglobin Level',
            'sc': 'Serum Creatinine',
            'sg': 'Specific Gravity',
            'al': 'Albuminuria (Urine Protein)',
            'bu': 'Blood Urea',
            'bgr': 'Blood Glucose Random',
            'htn': 'Hypertension Status',
            'dm': 'Diabetes Mellitus Status',
            'pcv': 'Packed Cell Volume',
            'rbc': 'Red Blood Cells',
            'rc': 'Red Blood Cell Count',
            'wc': 'White Blood Cell Count',
            'age': 'Patient Age',
            'bp': 'Blood Pressure',
            'pe': 'Pedal Edema',
            'ane': 'Anemia Status',
            'appet': 'Appetite Status',
            'sod': 'Sodium Level',
            'pot': 'Potassium Level',
            'su': 'Sugar Level',
            'pc': 'Pus Cell',
            'pcc': 'Pus Cell Clumps',
            'ba': 'Bacteria Presence',
            'cad': 'Coronary Artery Disease'
        }
        
        for item in top_factors:
            item['friendly_name'] = clinical_labels.get(item['feature'], item['feature'].upper())
            
        return {
            'top_factors': top_factors,
            'all_contributions': feature_contributions,
            'base_value': float(self.explainer.expected_value) if hasattr(self.explainer.expected_value, '__float__') else float(self.explainer.expected_value[0])
        }

if __name__ == '__main__':
    explainer = CKDExplainer()
    sample = pd.DataFrame([{
        'age': 55.0, 'bp': 90.0, 'sg': 1.010, 'al': 3.0, 'su': 0.0,
        'rbc': 'abnormal', 'pc': 'abnormal', 'pcc': 'present', 'ba': 'notpresent',
        'bgr': 160.0, 'bu': 65.0, 'sc': 3.2, 'sod': 130.0, 'pot': 5.5,
        'hemo': 9.2, 'pcv': 28.0, 'wc': 9800.0, 'rc': 3.4,
        'htn': 'yes', 'dm': 'yes', 'cad': 'no', 'appet': 'poor', 'pe': 'yes', 'ane': 'yes'
    }])
    explanation = explainer.explain_instance(sample)
    print("SHAP Explanation Top Factors successfully generated:")
    for f in explanation['top_factors']:
        print(f" - {f['friendly_name']} ({f['feature']}): SHAP {f['shap_value']} -> {f['risk_impact']}")
