"""
Explainability Module using SHAP

Provides SHAP-based explanations for enrollment predictions.
"""

import torch
import numpy as np
import shap
from typing import Dict, List, Optional, Union

from .enrollment_predictor import EnrollmentFusionModel


class SHAPExplainer:
    """
    SHAP-based explainer for enrollment prediction model
    """
    
    def __init__(
        self,
        model: EnrollmentFusionModel,
        background_data: Optional[torch.Tensor] = None,
        device: str = 'cpu'
    ):
        """
        Initialize SHAP explainer
        
        Args:
            model: Trained EnrollmentFusionModel
            background_data: Background dataset for SHAP (optional)
            device: Device to run on
        """
        self.model = model
        self.device = device
        self.model.eval()
        
        # Create a wrapper function for SHAP
        def model_predict(structured_features):
            """Wrapper for SHAP that only takes structured features"""
            # Convert to tensor if needed
            if not isinstance(structured_features, torch.Tensor):
                structured_features = torch.FloatTensor(structured_features)
            
            structured_features = structured_features.to(self.device)
            
            # For SHAP, we need dummy text inputs (use zeros)
            batch_size = structured_features.shape[0]
            dummy_input_ids = torch.zeros((batch_size, 512), dtype=torch.long).to(self.device)
            dummy_attention_mask = torch.zeros((batch_size, 512), dtype=torch.long).to(self.device)
            
            with torch.no_grad():
                logits = self.model(dummy_input_ids, dummy_attention_mask, structured_features)
                probs = torch.softmax(logits, dim=1)
            
            return probs.cpu().numpy()
        
        self.model_predict = model_predict
        
        # Initialize SHAP explainer
        if background_data is None:
            # Create simple background data (mean values)
            background_data = np.zeros((10, 4), dtype=np.float32)
        
        self.explainer = shap.KernelExplainer(
            self.model_predict,
            background_data
        )
    
    def explain_prediction(
        self,
        structured_features: np.ndarray,
        feature_names: List[str] = None
    ) -> Dict[str, any]:
        """
        Generate SHAP explanation for a prediction
        
        Args:
            structured_features: Normalized feature array [4]
            feature_names: Names of features
            
        Returns:
            Dict with SHAP values and explanations
        """
        if feature_names is None:
            feature_names = ['phase', 'target_enrollment', 'site_count', 'recruitment_duration']
        
        # Compute SHAP values
        shap_values = self.explainer.shap_values(structured_features.reshape(1, -1))
        
        # shap_values is a list (one per class), shape: [num_classes, 1, num_features]
        # Get SHAP values for predicted class
        predicted_class = np.argmax(self.model_predict(structured_features.reshape(1, -1))[0])
        
        class_shap_values = shap_values[predicted_class][0]  # Shape: [num_features]
        
        # Create explanation dict
        explanations = []
        for i, (name, shap_val) in enumerate(zip(feature_names, class_shap_values)):
            explanations.append({
                'feature': name,
                'shap_value': float(shap_val),
                'impact': 'positive' if shap_val > 0 else 'negative',
                'magnitude': float(abs(shap_val))
            })
        
        # Sort by magnitude
        explanations.sort(key=lambda x: x['magnitude'], reverse=True)
        
        return {
            'shap_values': shap_values,
            'explanations': explanations,
            'predicted_class': predicted_class
        }
    
    def get_top_drivers(
        self,
        structured_features: np.ndarray,
        top_k: int = 5
    ) -> List[Dict[str, any]]:
        """
        Get top feature drivers for a prediction
        
        Args:
            structured_features: Feature array
            top_k: Number of top features to return
            
        Returns:
            List of top driver dicts
        """
        explanation = self.explain_prediction(structured_features)
        return explanation['explanations'][:top_k]


def create_shap_explainer(
    model: EnrollmentFusionModel,
    background_samples: Optional[np.ndarray] = None,
    device: str = 'cpu'
) -> SHAPExplainer:
    """
    Factory function to create SHAP explainer
    
    Args:
        model: Trained model
        background_samples: Background data for SHAP
        device: Device to run on
        
    Returns:
        Initialized SHAPExplainer
    """
    return SHAPExplainer(model, background_samples, device)
