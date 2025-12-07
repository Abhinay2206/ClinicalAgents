"""
Enrollment Prediction Model Architecture

BioBERT-based fusion model for predicting clinical trial enrollment outcomes.
Combines text encoding (BioBERT) with structured numeric features (MLP).
"""

import torch
import torch.nn as nn
from transformers import AutoModel, AutoTokenizer
from typing import Dict, Optional


class BioBERTEncoder(nn.Module):
    """
    BioBERT encoder for clinical text (disease name + criteria)
    Uses dmis-lab/biobert-base-cased-v1.1 pretrained model
    """
    
    def __init__(self, model_name: str = "dmis-lab/biobert-base-cased-v1.1", freeze_bert: bool = False):
        super(BioBERTEncoder, self).__init__()
        self.bert = AutoModel.from_pretrained(model_name)
        
        # Optionally freeze BERT parameters for faster training
        if freeze_bert:
            for param in self.bert.parameters():
                param.requires_grad = False
        
        self.hidden_size = self.bert.config.hidden_size  # 768 for BERT-base
    
    def forward(self, input_ids: torch.Tensor, attention_mask: torch.Tensor) -> torch.Tensor:
        """
        Forward pass through BioBERT
        
        Args:
            input_ids: Token IDs [batch_size, seq_len]
            attention_mask: Attention mask [batch_size, seq_len]
            
        Returns:
            CLS token embedding [batch_size, hidden_size]
        """
        outputs = self.bert(input_ids=input_ids, attention_mask=attention_mask)
        # Use [CLS] token representation (first token)
        cls_embedding = outputs.last_hidden_state[:, 0, :]
        return cls_embedding


class StructuredFeaturesMLP(nn.Module):
    """
    MLP for processing structured numeric trial parameters
    Features: phase, target_enrollment, site_count, recruitment_duration
    """
    
    def __init__(self, input_dim: int = 4, hidden_dims: list = [64, 32], dropout: float = 0.3):
        super(StructuredFeaturesMLP, self).__init__()
        
        layers = []
        prev_dim = input_dim
        
        for hidden_dim in hidden_dims:
            layers.append(nn.Linear(prev_dim, hidden_dim))
            layers.append(nn.ReLU())
            layers.append(nn.Dropout(dropout))
            prev_dim = hidden_dim
        
        self.mlp = nn.Sequential(*layers)
        self.output_dim = hidden_dims[-1]
    
    def forward(self, features: torch.Tensor) -> torch.Tensor:
        """
        Forward pass through MLP
        
        Args:
            features: Structured features [batch_size, input_dim]
            
        Returns:
            Encoded features [batch_size, output_dim]
        """
        return self.mlp(features)


class EnrollmentFusionModel(nn.Module):
    """
    Fusion model combining BioBERT text encoding and structured features MLP
    Predicts enrollment outcome: success (0) / delayed (1) / fail (2)
    """
    
    def __init__(
        self,
        biobert_model_name: str = "dmis-lab/biobert-base-cased-v1.1",
        structured_input_dim: int = 4,
        structured_hidden_dims: list = [64, 32],
        fusion_hidden_dim: int = 128,
        num_classes: int = 3,
        dropout: float = 0.3,
        freeze_bert: bool = False
    ):
        super(EnrollmentFusionModel, self).__init__()
        
        # Text encoder
        self.text_encoder = BioBERTEncoder(biobert_model_name, freeze_bert)
        
        # Structured features encoder
        self.structured_encoder = StructuredFeaturesMLP(
            input_dim=structured_input_dim,
            hidden_dims=structured_hidden_dims,
            dropout=dropout
        )
        
        # Fusion layer
        fusion_input_dim = self.text_encoder.hidden_size + self.structured_encoder.output_dim
        self.fusion = nn.Sequential(
            nn.Linear(fusion_input_dim, fusion_hidden_dim),
            nn.ReLU(),
            nn.Dropout(dropout),
            nn.Linear(fusion_hidden_dim, num_classes)
        )
        
        self.num_classes = num_classes
    
    def forward(
        self,
        input_ids: torch.Tensor,
        attention_mask: torch.Tensor,
        structured_features: torch.Tensor
    ) -> torch.Tensor:
        """
        Forward pass through fusion model
        
        Args:
            input_ids: Token IDs for text [batch_size, seq_len]
            attention_mask: Attention mask [batch_size, seq_len]
            structured_features: Numeric features [batch_size, structured_dim]
            
        Returns:
            Logits for 3 classes [batch_size, num_classes]
        """
        # Encode text
        text_embedding = self.text_encoder(input_ids, attention_mask)
        
        # Encode structured features
        structured_embedding = self.structured_encoder(structured_features)
        
        # Concatenate embeddings
        fused = torch.cat([text_embedding, structured_embedding], dim=1)
        
        # Final classification
        logits = self.fusion(fused)
        
        return logits
    
    def predict_proba(
        self,
        input_ids: torch.Tensor,
        attention_mask: torch.Tensor,
        structured_features: torch.Tensor
    ) -> torch.Tensor:
        """
        Get probability predictions
        
        Returns:
            Probabilities for each class [batch_size, num_classes]
        """
        logits = self.forward(input_ids, attention_mask, structured_features)
        probabilities = torch.softmax(logits, dim=1)
        return probabilities


def create_model(
    num_classes: int = 3,
    freeze_bert: bool = False,
    device: Optional[str] = None
) -> EnrollmentFusionModel:
    """
    Factory function to create and initialize the enrollment prediction model
    
    Args:
        num_classes: Number of outcome classes (default: 3 for success/delayed/fail)
        freeze_bert: Whether to freeze BioBERT parameters
        device: Device to load model on ('cuda' or 'cpu')
        
    Returns:
        Initialized EnrollmentFusionModel
    """
    if device is None:
        device = 'cuda' if torch.cuda.is_available() else 'cpu'
    
    model = EnrollmentFusionModel(
        num_classes=num_classes,
        freeze_bert=freeze_bert
    )
    
    model = model.to(device)
    return model
