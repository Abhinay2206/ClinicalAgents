"""
Mock Enrollment Predictor

Provides mock predictions for 10 common diseases without loading BioBERT.
This is a lightweight alternative to the full ML model for development/testing.
"""

from typing import Dict, List, Optional, Union
import random


class MockEnrollmentPredictor:
    """
    Mock predictor that returns hardcoded predictions for 10 common diseases
    """
    
    # Mock predictions for 10 diseases
    DISEASE_PREDICTIONS = {
        "diabetes": {
            "predicted_class": "success",
            "confidence_scores": {"success": 0.78, "delayed": 0.15, "fail": 0.07},
            "top_risk_drivers": [
                {"feature": "target_enrollment", "impact": 0.65, "direction": "positive", "value": 100},
                {"feature": "site_count", "impact": 0.48, "direction": "positive", "value": 5},
                {"feature": "recruitment_duration", "impact": 0.32, "direction": "negative", "value": 12},
                {"feature": "phase", "impact": 0.21, "direction": "positive", "value": 2}
            ]
        },
        "cancer": {
            "predicted_class": "delayed",
            "confidence_scores": {"success": 0.35, "delayed": 0.52, "fail": 0.13},
            "top_risk_drivers": [
                {"feature": "phase", "impact": 0.72, "direction": "negative", "value": 3},
                {"feature": "target_enrollment", "impact": 0.58, "direction": "negative", "value": 200},
                {"feature": "recruitment_duration", "impact": 0.44, "direction": "negative", "value": 18},
                {"feature": "site_count", "impact": 0.35, "direction": "positive", "value": 10}
            ]
        },
        "alzheimer": {
            "predicted_class": "fail",
            "confidence_scores": {"success": 0.12, "delayed": 0.23, "fail": 0.65},
            "top_risk_drivers": [
                {"feature": "recruitment_duration", "impact": 0.81, "direction": "negative", "value": 24},
                {"feature": "phase", "impact": 0.69, "direction": "negative", "value": 3},
                {"feature": "target_enrollment", "impact": 0.57, "direction": "negative", "value": 300},
                {"feature": "site_count", "impact": 0.28, "direction": "positive", "value": 15}
            ]
        },
        "hypertension": {
            "predicted_class": "success",
            "confidence_scores": {"success": 0.82, "delayed": 0.12, "fail": 0.06},
            "top_risk_drivers": [
                {"feature": "site_count", "impact": 0.71, "direction": "positive", "value": 8},
                {"feature": "target_enrollment", "impact": 0.53, "direction": "positive", "value": 150},
                {"feature": "phase", "impact": 0.39, "direction": "positive", "value": 2},
                {"feature": "recruitment_duration", "impact": 0.24, "direction": "positive", "value": 12}
            ]
        },
        "asthma": {
            "predicted_class": "success",
            "confidence_scores": {"success": 0.76, "delayed": 0.18, "fail": 0.06},
            "top_risk_drivers": [
                {"feature": "recruitment_duration", "impact": 0.62, "direction": "positive", "value": 10},
                {"feature": "site_count", "impact": 0.55, "direction": "positive", "value": 6},
                {"feature": "target_enrollment", "impact": 0.41, "direction": "positive", "value": 120},
                {"feature": "phase", "impact": 0.29, "direction": "positive", "value": 2}
            ]
        },
        "parkinson": {
            "predicted_class": "delayed",
            "confidence_scores": {"success": 0.28, "delayed": 0.58, "fail": 0.14},
            "top_risk_drivers": [
                {"feature": "phase", "impact": 0.68, "direction": "negative", "value": 3},
                {"feature": "target_enrollment", "impact": 0.54, "direction": "negative", "value": 180},
                {"feature": "recruitment_duration", "impact": 0.47, "direction": "negative", "value": 20},
                {"feature": "site_count", "impact": 0.33, "direction": "positive", "value": 12}
            ]
        },
        "covid-19": {
            "predicted_class": "success",
            "confidence_scores": {"success": 0.88, "delayed": 0.09, "fail": 0.03},
            "top_risk_drivers": [
                {"feature": "recruitment_duration", "impact": 0.79, "direction": "positive", "value": 6},
                {"feature": "site_count", "impact": 0.72, "direction": "positive", "value": 20},
                {"feature": "target_enrollment", "impact": 0.58, "direction": "positive", "value": 500},
                {"feature": "phase", "impact": 0.45, "direction": "positive", "value": 3}
            ]
        },
        "arthritis": {
            "predicted_class": "success",
            "confidence_scores": {"success": 0.71, "delayed": 0.21, "fail": 0.08},
            "top_risk_drivers": [
                {"feature": "site_count", "impact": 0.64, "direction": "positive", "value": 7},
                {"feature": "target_enrollment", "impact": 0.49, "direction": "positive", "value": 140},
                {"feature": "phase", "impact": 0.36, "direction": "positive", "value": 2},
                {"feature": "recruitment_duration", "impact": 0.27, "direction": "positive", "value": 14}
            ]
        },
        "depression": {
            "predicted_class": "delayed",
            "confidence_scores": {"success": 0.38, "delayed": 0.48, "fail": 0.14},
            "top_risk_drivers": [
                {"feature": "recruitment_duration", "impact": 0.59, "direction": "negative", "value": 16},
                {"feature": "phase", "impact": 0.52, "direction": "negative", "value": 2},
                {"feature": "target_enrollment", "impact": 0.43, "direction": "negative", "value": 160},
                {"feature": "site_count", "impact": 0.31, "direction": "positive", "value": 9}
            ]
        },
        "obesity": {
            "predicted_class": "success",
            "confidence_scores": {"success": 0.74, "delayed": 0.19, "fail": 0.07},
            "top_risk_drivers": [
                {"feature": "target_enrollment", "impact": 0.66, "direction": "positive", "value": 200},
                {"feature": "site_count", "impact": 0.52, "direction": "positive", "value": 10},
                {"feature": "recruitment_duration", "impact": 0.38, "direction": "positive", "value": 12},
                {"feature": "phase", "impact": 0.25, "direction": "positive", "value": 2}
            ]
        }
    }
    
    def __init__(self, device: Optional[str] = None):
        """Initialize mock predictor"""
        self.device = device or 'cpu'
        print(f"✅ Mock Enrollment Predictor initialized (supports {len(self.DISEASE_PREDICTIONS)} diseases)")
        print(f"   Supported diseases: {', '.join(self.DISEASE_PREDICTIONS.keys())}")
    
    def predict_enrollment(
        self,
        disease: str,
        criteria_text: str = "",
        tabular_features: Optional[Dict[str, Union[int, float]]] = None
    ) -> Dict[str, any]:
        """
        Predict enrollment outcome for a clinical trial
        
        Args:
            disease: Disease name
            criteria_text: Optional eligibility criteria text (ignored in mock)
            tabular_features: Trial parameters (used to adjust risk drivers)
                
        Returns:
            Dict with predicted_class, confidence_scores, top_risk_drivers
        """
        # Normalize disease name
        disease_normalized = disease.lower().strip()
        
        # Check if we have a mock prediction for this disease
        if disease_normalized in self.DISEASE_PREDICTIONS:
            prediction = self.DISEASE_PREDICTIONS[disease_normalized].copy()
            
            # If tabular features provided, update risk drivers with actual values
            if tabular_features:
                for driver in prediction["top_risk_drivers"]:
                    feature_name = driver["feature"]
                    if feature_name in tabular_features:
                        driver["value"] = tabular_features[feature_name]
            
            return prediction
        
        # For unknown diseases, return a generic prediction with some randomness
        random.seed(hash(disease_normalized) % 2**32)
        outcome_choice = random.choice(["success", "delayed", "fail"])
        
        if outcome_choice == "success":
            scores = {"success": 0.65 + random.random() * 0.2, "delayed": 0.15, "fail": 0.05}
        elif outcome_choice == "delayed":
            scores = {"success": 0.30, "delayed": 0.50 + random.random() * 0.15, "fail": 0.10}
        else:
            scores = {"success": 0.15, "delayed": 0.25, "fail": 0.55 + random.random() * 0.15}
        
        # Normalize scores to sum to 1.0
        total = sum(scores.values())
        scores = {k: v/total for k, v in scores.items()}
        
        # Default tabular features
        if not tabular_features:
            tabular_features = {
                'phase': 2,
                'target_enrollment': 100,
                'site_count': 5,
                'recruitment_duration': 12
            }
        
        return {
            'predicted_class': outcome_choice,
            'confidence_scores': scores,
            'top_risk_drivers': [
                {"feature": "phase", "impact": 0.45, "direction": "positive", "value": tabular_features.get('phase', 2)},
                {"feature": "target_enrollment", "impact": 0.52, "direction": "positive", "value": tabular_features.get('target_enrollment', 100)},
                {"feature": "site_count", "impact": 0.38, "direction": "positive", "value": tabular_features.get('site_count', 5)},
                {"feature": "recruitment_duration", "impact": 0.31, "direction": "negative", "value": tabular_features.get('recruitment_duration', 12)}
            ]
        }
