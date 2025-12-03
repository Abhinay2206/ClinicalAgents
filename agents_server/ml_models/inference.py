"""
Inference Module for Enrollment Prediction

Provides easy-to-use interface for making predictions with trained model.
"""

import os
import torch
import numpy as np
from transformers import AutoTokenizer
from typing import Dict, List, Optional, Union

from .enrollment_predictor import EnrollmentFusionModel


class EnrollmentPredictor:
    """
    Main inference class for enrollment outcome prediction
    Loads trained model and provides prediction interface
    """
    
    def __init__(
        self,
        model_dir: str = 'ml_models/saved_models',
        device: Optional[str] = None
    ):
        """
        Initialize predictor with trained model
        
        Args:
            model_dir: Directory containing saved model and tokenizer
            device: Device to run inference on ('cuda' or 'cpu')
        """
        if device is None:
            self.device = 'cuda' if torch.cuda.is_available() else 'cpu'
        else:
            self.device = device
        
        # Construct paths
        base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        model_path = os.path.join(base_dir, model_dir, 'enrollment_model.pt')
        tokenizer_path = os.path.join(base_dir, model_dir, 'tokenizer')
        
        # Check if model exists
        if not os.path.exists(model_path):
            raise FileNotFoundError(
                f"Model not found at {model_path}. "
                "Please train the model first using ml_models.training.train_enrollment_model()"
            )
        
        # Load tokenizer
        self.tokenizer = AutoTokenizer.from_pretrained(tokenizer_path)
        
        # Load model checkpoint - use weights_only=False to load numpy arrays
        # This is safe because we trust our own trained model
        try:
            checkpoint = torch.load(model_path, map_location=self.device, weights_only=False)
        except TypeError:
            # Fallback for older PyTorch versions
            checkpoint = torch.load(model_path, map_location=self.device)
        
        # Initialize model
        self.model = EnrollmentFusionModel(
            num_classes=checkpoint.get('num_classes', 3)
        )
        self.model.load_state_dict(checkpoint['model_state_dict'])
        self.model.to(self.device)
        self.model.eval()
        
        # Load normalization parameters
        self.feature_mean = checkpoint.get('feature_mean', np.zeros(4))
        self.feature_std = checkpoint.get('feature_std', np.ones(4))
        
        # Class labels
        self.class_labels = ['success', 'delayed', 'fail']
        
        print(f"✓ Enrollment predictor loaded on {self.device}")
    
    def _prepare_text(self, disease: str, criteria_text: str = "") -> str:
        """
        Prepare text input from disease and criteria
        
        Args:
            disease: Disease name
            criteria_text: Eligibility criteria text
            
        Returns:
            Formatted text string
        """
        if criteria_text:
            return f"Disease: {disease}. Eligibility Criteria: {criteria_text}"
        else:
            return f"Disease: {disease}."
    
    def _prepare_features(self, tabular_features: Dict[str, Union[int, float]]) -> np.ndarray:
        """
        Prepare and normalize structured features
        
        Args:
            tabular_features: Dict with keys: phase, target_enrollment, site_count, recruitment_duration
            
        Returns:
            Normalized feature array
        """
        # Extract features with defaults
        phase = tabular_features.get('phase', 0)
        target_enrollment = tabular_features.get('target_enrollment', 100)
        site_count = tabular_features.get('site_count', 1)
        recruitment_duration = tabular_features.get('recruitment_duration', 12)
        
        # Create feature array
        features = np.array([phase, target_enrollment, site_count, recruitment_duration], dtype=np.float32)
        
        # Normalize
        features = (features - self.feature_mean) / self.feature_std
        
        return features
    
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
            criteria_text: Optional eligibility criteria text
            tabular_features: Dict with trial parameters:
                - phase: Trial phase (0-4)
                - target_enrollment: Target number of participants
                - site_count: Number of trial sites
                - recruitment_duration: Recruitment duration in months
                
        Returns:
            Dict with:
                - predicted_class: Predicted outcome ('success', 'delayed', 'fail')
                - confidence_scores: Dict of probabilities for each class
                - top_risk_drivers: List of influential features (from explainability)
        """
        # Default tabular features if not provided
        if tabular_features is None:
            tabular_features = {
                'phase': 2,
                'target_enrollment': 100,
                'site_count': 5,
                'recruitment_duration': 12
            }
        
        # Prepare inputs
        text = self._prepare_text(disease, criteria_text)
        features = self._prepare_features(tabular_features)
        
        # Tokenize text
        encoding = self.tokenizer(
            text,
            max_length=512,
            padding='max_length',
            truncation=True,
            return_tensors='pt'
        )
        
        input_ids = encoding['input_ids'].to(self.device)
        attention_mask = encoding['attention_mask'].to(self.device)
        structured_features = torch.FloatTensor(features).unsqueeze(0).to(self.device)
        
        # Make prediction
        with torch.no_grad():
            probabilities = self.model.predict_proba(
                input_ids,
                attention_mask,
                structured_features
            )
        
        # Get predictions
        probs = probabilities.cpu().numpy()[0]
        predicted_class_idx = np.argmax(probs)
        predicted_class = self.class_labels[predicted_class_idx]
        
        # Build confidence scores dict
        confidence_scores = {
            label: float(prob)
            for label, prob in zip(self.class_labels, probs)
        }
        
        # Simple feature importance (gradient-based approximation)
        top_risk_drivers = self._get_feature_importance(
            input_ids, attention_mask, structured_features, tabular_features
        )
        
        return {
            'predicted_class': predicted_class,
            'confidence_scores': confidence_scores,
            'top_risk_drivers': top_risk_drivers
        }
    
    def _get_feature_importance(
        self,
        input_ids: torch.Tensor,
        attention_mask: torch.Tensor,
        structured_features: torch.Tensor,
        original_features: Dict[str, Union[int, float]]
    ) -> List[Dict[str, any]]:
        """
        Compute feature importance using gradient-based method
        
        Returns:
            List of feature importance dicts
        """
        # Enable gradients for structured features
        structured_features.requires_grad = True
        
        # Forward pass
        logits = self.model(input_ids, attention_mask, structured_features)
        predicted_class = torch.argmax(logits, dim=1)
        
        # Backward pass to get gradients
        self.model.zero_grad()
        logits[0, predicted_class].backward()
        
        # Get gradients
        gradients = structured_features.grad.cpu().numpy()[0]
        feature_values = structured_features.detach().cpu().numpy()[0]
        
        # Compute importance (gradient * value)
        importance = np.abs(gradients * feature_values)
        
        # Feature names
        feature_names = ['phase', 'target_enrollment', 'site_count', 'recruitment_duration']
        
        # Create importance list
        drivers = []
        for i, (name, imp, grad) in enumerate(zip(feature_names, importance, gradients)):
            drivers.append({
                'feature': name,
                'impact': float(imp),
                'direction': 'positive' if grad > 0 else 'negative',
                'value': original_features.get(name, 0)
            })
        
        # Sort by impact
        drivers.sort(key=lambda x: x['impact'], reverse=True)
        
        return drivers[:5]  # Return top 5


def predict_enrollment(
    disease: str,
    criteria_text: str = "",
    tabular_features: Optional[Dict[str, Union[int, float]]] = None,
    model_dir: str = 'ml_models/saved_models'
) -> Dict[str, any]:
    """
    Convenience function for one-off predictions
    
    Args:
        disease: Disease name
        criteria_text: Optional eligibility criteria text
        tabular_features: Trial parameters dict
        model_dir: Directory containing saved model
        
    Returns:
        Prediction dict with predicted_class, confidence_scores, top_risk_drivers
    """
    predictor = EnrollmentPredictor(model_dir=model_dir)
    return predictor.predict_enrollment(disease, criteria_text, tabular_features)
