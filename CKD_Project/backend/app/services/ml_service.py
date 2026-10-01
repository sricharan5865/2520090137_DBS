import os
import sys
import joblib
import pandas as pd
import numpy as np
from typing import Dict, Any, Tuple

# Ensure ml package is on path
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '../../..'))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from ml.preprocessing.pipeline import CKDPreprocessor, ALL_FEATURES
from ml.explainability.explainer import CKDExplainer

class MLInferenceService:
    def __init__(self):
        self.models_dir = os.path.join(project_root, 'ml/models')
        self.best_model_path = os.path.join(self.models_dir, 'best_model.joblib')
        self.xgb_model_path = os.path.join(self.models_dir, 'xgboost_model.joblib')
        self.lgb_model_path = os.path.join(self.models_dir, 'lightgbm_model.joblib')
        
        self.loaded_artifact = joblib.load(self.best_model_path)
        self.preprocessor: CKDPreprocessor = self.loaded_artifact['preprocessor']
        self.model = self.loaded_artifact['model']
        self.model_name = self.loaded_artifact.get('model_name', 'XGBoost')
        self.model_version = self.loaded_artifact.get('model_version', '1.0.0')
        
        # Initialize SHAP explainer
        self.explainer = CKDExplainer(self.best_model_path)
        print(f"[ML Service] Loaded {self.model_name} v{self.model_version} with SHAP Explainer successfully.")

    def run_prediction(self, clinical_data: Dict[str, Any], model_choice: str = "XGBoost") -> Dict[str, Any]:
        """
        Executes prediction pipeline on given dictionary of features.
        Returns:
            dict containing prediction_result, probability, risk_level, top_factors, and shap_explanation.
        """
        # Convert dictionary to 1-row DataFrame
        input_row = {}
        for feat in ALL_FEATURES:
            input_row[feat] = clinical_data.get(feat, None)
            
        df_input = pd.DataFrame([input_row])
        
        # Determine active model
        model_to_use = self.model
        active_model_name = self.model_name
        
        if model_choice.lower() == "lightgbm" and os.path.exists(self.lgb_model_path):
            lgb_art = joblib.load(self.lgb_model_path)
            model_to_use = lgb_art['model']
            active_model_name = "LightGBM"
        elif model_choice.lower() == "xgboost" and os.path.exists(self.xgb_model_path):
            xgb_art = joblib.load(self.xgb_model_path)
            model_to_use = xgb_art['model']
            active_model_name = "XGBoost"
            
        # Transform features
        X_trans = self.preprocessor.transform(df_input)
        
        # Predict class & probability
        pred_class = int(model_to_use.predict(X_trans)[0])
        probabilities = model_to_use.predict_proba(X_trans)[0]
        prob_ckd = float(probabilities[1])
        
        result_label = "CKD Detected" if pred_class == 1 else "No CKD Detected"
        
        # Determine risk stratification
        if prob_ckd >= 0.80:
            risk_level = "Critical Risk" if prob_ckd >= 0.90 else "High Risk"
        elif prob_ckd >= 0.40:
            risk_level = "Moderate Risk"
        else:
            risk_level = "Low Risk"
            
        # Calculate SHAP explainability
        explanation = self.explainer.explain_instance(df_input, top_k=6)
        
        return {
            "model_name": active_model_name,
            "model_version": self.model_version,
            "prediction_result": result_label,
            "probability": round(prob_ckd, 4),
            "risk_level": risk_level,
            "top_factors": explanation["top_factors"],
            "shap_explanation": {
                "base_value": explanation["base_value"],
                "all_contributions": explanation["all_contributions"]
            },
            "clinical_disclaimer": "ML prediction is intended for decision support and should be interpreted by a qualified healthcare professional."
        }

ml_service = MLInferenceService()
