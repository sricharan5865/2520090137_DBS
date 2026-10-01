import os
import sys
import json
import datetime
import pandas as pd
import numpy as np
import joblib
from sklearn.model_selection import train_test_split, StratifiedKFold, cross_validate
from sklearn.metrics import (
    accuracy_score, precision_score, recall_score, f1_score, roc_auc_score, confusion_matrix
)
import xgboost as xgb
import lightgbm as lgb

# Ensure project path is accessible
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))
from ml.preprocessing.pipeline import CKDPreprocessor, clean_raw_dataframe, ALL_FEATURES

def load_data(csv_path: str):
    df = pd.read_csv(csv_path)
    df_clean = clean_raw_dataframe(df)
    
    # Target encoding
    y = df_clean['classification'].map({'ckd': 1, 'notckd': 0})
    X = df_clean.drop(columns=['classification'])
    
    # Drop any row where target is missing if any
    valid_idx = y.dropna().index
    X = X.loc[valid_idx]
    y = y.loc[valid_idx].astype(int)
    
    return X, y

def evaluate_model(model, X_test_trans, y_test):
    y_pred = model.predict(X_test_trans)
    y_proba = model.predict_proba(X_test_trans)[:, 1] if hasattr(model, 'predict_proba') else y_pred
    
    acc = float(accuracy_score(y_test, y_pred))
    prec = float(precision_score(y_test, y_pred, zero_division=0))
    rec = float(recall_score(y_test, y_pred, zero_division=0))
    f1 = float(f1_score(y_test, y_pred, zero_division=0))
    roc_auc = float(roc_auc_score(y_test, y_proba))
    cm = confusion_matrix(y_test, y_pred).tolist()
    
    return {
        'accuracy': round(acc, 4),
        'precision': round(prec, 4),
        'recall': round(rec, 4),
        'f1_score': round(f1, 4),
        'roc_auc': round(roc_auc, 4),
        'confusion_matrix': cm
    }

def train_and_evaluate():
    data_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '../data/kidney_disease.csv'))
    print(f"Loading official CKD dataset from: {data_path}")
    X, y = load_data(data_path)
    print(f"Total dataset shape: X={X.shape}, y={y.shape} (CKD: {sum(y==1)}, NotCKD: {sum(y==0)})")
    
    # Stratified Train/Test Split (80/20)
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.20, random_state=42, stratify=y
    )
    print(f"Train split: {X_train.shape[0]} samples, Test split: {X_test.shape[0]} samples")
    
    # Fit preprocessor exclusively on training data
    preprocessor = CKDPreprocessor()
    preprocessor.fit(X_train)
    
    X_train_trans = preprocessor.transform(X_train)
    X_test_trans = preprocessor.transform(X_test)
    
    # 1. XGBoost Classifier
    print("\n--- Training Model 1: XGBoost ---")
    xgb_model = xgb.XGBClassifier(
        n_estimators=100,
        max_depth=4,
        learning_rate=0.08,
        subsample=0.8,
        colsample_bytree=0.8,
        random_state=42,
        eval_metric='logloss'
    )
    xgb_model.fit(X_train_trans, y_train)
    xgb_metrics = evaluate_model(xgb_model, X_test_trans, y_test)
    print("XGBoost Test Metrics:", xgb_metrics)
    
    # 2. LightGBM Classifier
    print("\n--- Training Model 2: LightGBM ---")
    lgb_model = lgb.LGBMClassifier(
        n_estimators=100,
        max_depth=4,
        learning_rate=0.08,
        subsample=0.8,
        random_state=42,
        verbose=-1
    )
    lgb_model.fit(X_train_trans, y_train)
    lgb_metrics = evaluate_model(lgb_model, X_test_trans, y_test)
    print("LightGBM Test Metrics:", lgb_metrics)
    
    # Comparison summary
    comparison = {
        'training_date': datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        'dataset_instances': len(X),
        'dataset_features': len(ALL_FEATURES),
        'train_samples': len(X_train),
        'test_samples': len(X_test),
        'models': {
            'XGBoost': {
                'version': xgb.__version__,
                'metrics': xgb_metrics,
                'hyperparameters': {
                    'n_estimators': 100,
                    'max_depth': 4,
                    'learning_rate': 0.08
                }
            },
            'LightGBM': {
                'version': lgb.__version__,
                'metrics': lgb_metrics,
                'hyperparameters': {
                    'n_estimators': 100,
                    'max_depth': 4,
                    'learning_rate': 0.08
                }
            }
        }
    }
    
    # Select winning model based on F1-Score & ROC-AUC
    if (xgb_metrics['f1_score'] + xgb_metrics['roc_auc']) >= (lgb_metrics['f1_score'] + lgb_metrics['roc_auc']):
        best_name = 'XGBoost'
        best_model = xgb_model
        best_metrics = xgb_metrics
    else:
        best_name = 'LightGBM'
        best_model = lgb_model
        best_metrics = lgb_metrics
        
    comparison['selected_model'] = best_name
    print(f"\n>>> Selected Deployment Model: {best_name} (F1: {best_metrics['f1_score']}, ROC-AUC: {best_metrics['roc_auc']})")
    
    # Save comparison artifacts
    eval_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '../evaluation'))
    models_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '../models'))
    os.makedirs(eval_dir, exist_ok=True)
    os.makedirs(models_dir, exist_ok=True)
    
    json_path = os.path.join(eval_dir, 'model_comparison.json')
    with open(json_path, 'w') as f:
        json.dump(comparison, f, indent=2)
        
    md_path = os.path.join(eval_dir, 'model_comparison.md')
    with open(md_path, 'w') as f:
        f.write("# Chronic Kidney Disease ML Model Comparison\n\n")
        f.write(f"**Training Date:** {comparison['training_date']}\n\n")
        f.write(f"**Dataset:** UCI Chronic Kidney Disease ({len(X)} records, {len(ALL_FEATURES)} features)\n\n")
        f.write("| Metric | XGBoost | LightGBM |\n")
        f.write("| :--- | :---: | :---: |\n")
        f.write(f"| **Accuracy** | {xgb_metrics['accuracy'] * 100:.2f}% | {lgb_metrics['accuracy'] * 100:.2f}% |\n")
        f.write(f"| **Precision** | {xgb_metrics['precision'] * 100:.2f}% | {lgb_metrics['precision'] * 100:.2f}% |\n")
        f.write(f"| **Recall** | {xgb_metrics['recall'] * 100:.2f}% | {lgb_metrics['recall'] * 100:.2f}% |\n")
        f.write(f"| **F1-Score** | {xgb_metrics['f1_score'] * 100:.2f}% | {lgb_metrics['f1_score'] * 100:.2f}% |\n")
        f.write(f"| **ROC-AUC** | {xgb_metrics['roc_auc']:.4f} | {lgb_metrics['roc_auc']:.4f} |\n\n")
        f.write(f"**Selected Model for Production:** `{best_name}`\n")
        
    # Save Pipeline and models
    pipeline_artifact = {
        'preprocessor': preprocessor,
        'model': best_model,
        'model_name': best_name,
        'model_version': '1.0.0',
        'metrics': best_metrics,
        'features': ALL_FEATURES,
        'training_date': comparison['training_date']
    }
    
    # Save both models for interchangeable runtime prediction if desired
    joblib.dump(pipeline_artifact, os.path.join(models_dir, 'best_model.joblib'))
    joblib.dump({'preprocessor': preprocessor, 'model': xgb_model, 'name': 'XGBoost'}, os.path.join(models_dir, 'xgboost_model.joblib'))
    joblib.dump({'preprocessor': preprocessor, 'model': lgb_model, 'name': 'LightGBM'}, os.path.join(models_dir, 'lightgbm_model.joblib'))
    
    # Metadata for API fast read
    with open(os.path.join(models_dir, 'metadata.json'), 'w') as f:
        json.dump({
            'model_name': best_name,
            'version': '1.0.0',
            'training_date': comparison['training_date'],
            'features': ALL_FEATURES,
            'metrics': best_metrics
        }, f, indent=2)
        
    print("All ML artifacts saved successfully in ml/models/ and ml/evaluation/.")

if __name__ == '__main__':
    train_and_evaluate()
