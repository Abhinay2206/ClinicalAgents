"""
Training Pipeline for Enrollment Prediction Model

Handles data loading from ChromaDB with batched loading, training with 
class-weighted loss, early stopping, and model checkpointing.
"""

import os
import torch
import torch.nn as nn
import numpy as np
from torch.utils.data import Dataset, DataLoader
from transformers import AutoTokenizer
from typing import Dict, List, Tuple, Optional
from tqdm import tqdm
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score, f1_score
import chromadb

from .enrollment_predictor import EnrollmentFusionModel


class EnrollmentDataset(Dataset):
    """PyTorch Dataset for enrollment prediction"""
    
    def __init__(
        self,
        texts: List[str],
        structured_features: np.ndarray,
        labels: np.ndarray,
        tokenizer,
        max_length: int = 512
    ):
        self.texts = texts
        self.structured_features = torch.FloatTensor(structured_features)
        self.labels = torch.LongTensor(labels)
        self.tokenizer = tokenizer
        self.max_length = max_length
    
    def __len__(self):
        return len(self.texts)
    
    def __getitem__(self, idx):
        text = self.texts[idx]
        encoding = self.tokenizer(
            text,
            max_length=self.max_length,
            padding='max_length',
            truncation=True,
            return_tensors='pt'
        )
        
        return {
            'input_ids': encoding['input_ids'].squeeze(0),
            'attention_mask': encoding['attention_mask'].squeeze(0),
            'structured_features': self.structured_features[idx],
            'labels': self.labels[idx]
        }


def load_data_from_chromadb(
    collection_name: str = 'clinical_trials',
    api_key: Optional[str] = None,
    tenant: Optional[str] = None,
    database: str = 'ClinicalAgents',
    max_samples: Optional[int] = None
) -> Tuple[List[str], np.ndarray, np.ndarray]:
    """
    Load training data from ChromaDB in batches to avoid quota limits
    
    Returns:
        Tuple of (texts, structured_features, labels)
    """
    if api_key is None:
        api_key = os.getenv('CHROMA_API_KEY')
    if tenant is None:
        tenant = os.getenv('CHROMA_TENANT')
    
    client = chromadb.CloudClient(api_key=api_key, tenant=tenant, database=database)
    collection = client.get_collection(collection_name)
    
    total_count = collection.count()
    num_samples = min(max_samples, total_count) if max_samples else total_count
    
    print(f"Loading {num_samples} samples from ChromaDB...")
    
    # Load in batches (ChromaDB limit ~300 per request)
    batch_size = 250
    texts = []
    structured_features_list = []
    labels = []
    
    num_batches = (num_samples + batch_size - 1) // batch_size
    
    for batch_idx in range(num_batches):
        offset = batch_idx * batch_size
        limit = min(batch_size, num_samples - offset)
        
        results = collection.get(limit=limit, offset=offset, include=['metadatas'])
        
        for metadata in results['metadatas']:
            # Extract text
            disease = metadata.get('disease', 'Unknown')
            criteria = metadata.get('eligibility_criteria', '')
            texts.append(f"Disease: {disease}. Eligibility Criteria: {criteria}")
            
            # Extract structured features
            phase_str = metadata.get('phase', 'N/A').lower()
            if 'phase 1' in phase_str or 'phase i' in phase_str:
                phase = 1
            elif 'phase 2' in phase_str or 'phase ii' in phase_str:
                phase = 2
            elif 'phase 3' in phase_str or 'phase iii' in phase_str:
                phase = 3
            elif 'phase 4' in phase_str or 'phase iv' in phase_str:
                phase = 4
            else:
                phase = 0
            
            # Handle missing numeric values
            try:
                target_enrollment = float(metadata.get('target_enrollment', 100) or 100)
            except (ValueError, TypeError):
                target_enrollment = 100
            
            try:
                site_count = float(metadata.get('site_count', 5) or 5)
            except (ValueError, TypeError):
                site_count = 5
            
            try:
                recruitment_duration = float(metadata.get('recruitment_duration_months', 12) or 12)
            except (ValueError, TypeError):
                recruitment_duration = 12
            
            structured_features_list.append([phase, target_enrollment, site_count, recruitment_duration])
            
            # Map status to label
            status = metadata.get('status', '').lower()
            if any(s in status for s in ['completed', 'recruiting', 'active']):
                label = 0  # success
            elif any(s in status for s in ['delayed', 'suspended']):
                label = 1  # delayed
            elif any(s in status for s in ['terminated', 'withdrawn']):
                label = 2  # fail
            else:
                label = 0
            
            labels.append(label)
    
    return texts, np.array(structured_features_list, dtype=np.float32), np.array(labels, dtype=np.int64)


def compute_class_weights(labels: np.ndarray, num_classes: int = 3, smoothing: str = 'sqrt') -> torch.Tensor:
    """
    Compute class weights with smoothing to prevent overfitting
    
    Args:
        labels: Array of labels
        num_classes: Number of classes
        smoothing: 'sqrt' for square root, 'log' for logarithmic, 'none' for raw
    """
    class_counts = np.bincount(labels, minlength=num_classes)
    total_samples = len(labels)
    raw_weights = total_samples / (num_classes * class_counts + 1e-6)
    
    if smoothing == 'sqrt':
        class_weights = np.sqrt(raw_weights)
    elif smoothing == 'log':
        class_weights = np.log1p(raw_weights)
    else:
        class_weights = raw_weights
    
    return torch.FloatTensor(class_weights)


def train_enrollment_model(
    collection_name: str = 'clinical_trials',
    api_key: Optional[str] = None,
    tenant: Optional[str] = None,
    database: str = 'ClinicalAgents',
    epochs: int = 10,
    batch_size: int = 16,
    learning_rate: float = 2e-5,
    validation_split: float = 0.2,
    max_samples: Optional[int] = None,
    save_dir: str = 'ml_models/saved_models',
    device: Optional[str] = None,
    freeze_bert: bool = False,
    freeze_layers: int = 8
) -> Dict[str, any]:
    """
    Main training function with anti-overfitting measures
    
    Args:
        collection_name: ChromaDB collection name
        api_key: ChromaDB API key
        tenant: ChromaDB tenant
        database: ChromaDB database name
        epochs: Number of training epochs
        batch_size: Batch size
        learning_rate: Learning rate
        validation_split: Fraction for validation
        max_samples: Max samples to use (None for all)
        save_dir: Directory to save model
        device: Device to train on
        freeze_bert: Freeze all BERT parameters
        freeze_layers: Number of bottom BERT layers to freeze (0-12, recommended: 8)
        
    Returns:
        Training history dict
    """
    if device is None:
        device = 'cuda' if torch.cuda.is_available() else 'cpu'
    
    print(f"🚀 Starting training on {device}")
    
    # Load data
    texts, structured_features, labels = load_data_from_chromadb(
        collection_name, api_key, tenant, database, max_samples
    )
    
    print(f"✓ Loaded {len(texts)} samples")
    print(f"  Class distribution: {np.bincount(labels)}")
    
    # Normalize features
    feature_mean = structured_features.mean(axis=0)
    feature_std = structured_features.std(axis=0) + 1e-6
    structured_features = (structured_features - feature_mean) / feature_std
    
    # Train/val split
    train_texts, val_texts, train_features, val_features, train_labels, val_labels = train_test_split(
        texts, structured_features, labels,
        test_size=validation_split,
        random_state=42,
        stratify=labels
    )
    
    print(f"✓ Train: {len(train_texts)}, Validation: {len(val_texts)}")
    
    # Initialize model
    print("🔧 Initializing model...")
    tokenizer = AutoTokenizer.from_pretrained("dmis-lab/biobert-base-cased-v1.1")
    model = EnrollmentFusionModel(freeze_bert=freeze_bert, freeze_layers=freeze_layers).to(device)
    
    # Create datasets
    train_dataset = EnrollmentDataset(train_texts, train_features, train_labels, tokenizer)
    val_dataset = EnrollmentDataset(val_texts, val_features, val_labels, tokenizer)
    
    train_loader = DataLoader(train_dataset, batch_size=batch_size, shuffle=True)
    val_loader = DataLoader(val_dataset, batch_size=batch_size)
    
    # Compute class weights with sqrt smoothing
    class_weights = compute_class_weights(train_labels, smoothing='sqrt').to(device)
    print(f"✓ Class weights (sqrt smoothed): {class_weights.cpu().numpy()}")
    
    # Loss and optimizer
    criterion = nn.CrossEntropyLoss(weight=class_weights)
    optimizer = torch.optim.AdamW(model.parameters(), lr=learning_rate)
    
    # Training loop with early stopping
    history = {'train_loss': [], 'val_loss': [], 'val_accuracy': [], 'val_f1': []}
    best_val_f1 = 0.0
    best_val_loss = float('inf')
    patience = 3
    patience_counter = 0
    
    for epoch in range(epochs):
        print(f"\n📈 Epoch {epoch + 1}/{epochs}")
        
        # Training
        model.train()
        train_loss = 0.0
        
        for batch in tqdm(train_loader, desc="Training"):
            input_ids = batch['input_ids'].to(device)
            attention_mask = batch['attention_mask'].to(device)
            structured_features = batch['structured_features'].to(device)
            labels = batch['labels'].to(device)
            
            optimizer.zero_grad()
            logits = model(input_ids, attention_mask, structured_features)
            loss = criterion(logits, labels)
            loss.backward()
            optimizer.step()
            
            train_loss += loss.item()
        
        avg_train_loss = train_loss / len(train_loader)
        history['train_loss'].append(avg_train_loss)
        
        # Validation
        model.eval()
        val_loss = 0.0
        all_preds = []
        all_labels = []
        
        with torch.no_grad():
            for batch in tqdm(val_loader, desc="Validation"):
                input_ids = batch['input_ids'].to(device)
                attention_mask = batch['attention_mask'].to(device)
                structured_features = batch['structured_features'].to(device)
                labels = batch['labels'].to(device)
                
                logits = model(input_ids, attention_mask, structured_features)
                loss = criterion(logits, labels)
                val_loss += loss.item()
                
                preds = torch.argmax(logits, dim=1).cpu().numpy()
                all_preds.extend(preds)
                all_labels.extend(labels.cpu().numpy())
        
        avg_val_loss = val_loss / len(val_loader)
        val_accuracy = accuracy_score(all_labels, all_preds)
        val_f1 = f1_score(all_labels, all_preds, average='weighted')
        
        history['val_loss'].append(avg_val_loss)
        history['val_accuracy'].append(val_accuracy)
        history['val_f1'].append(val_f1)
        
        print(f"  Train Loss: {avg_train_loss:.4f}")
        print(f"  Val Loss: {avg_val_loss:.4f}, Accuracy: {val_accuracy:.4f}, F1: {val_f1:.4f}")
        
        # Overfitting warning
        if avg_val_loss > avg_train_loss * 1.5:
            print(f"  ⚠️ Warning: Validation loss is {avg_val_loss/avg_train_loss:.2f}x training loss (possible overfitting)")
        
        # Early stopping
        if avg_val_loss < best_val_loss:
            best_val_loss = avg_val_loss
            patience_counter = 0
        else:
            patience_counter += 1
            print(f"  ⏳ No improvement in val loss for {patience_counter}/{patience} epochs")
        
        # Save best model
        if val_f1 > best_val_f1:
            best_val_f1 = val_f1
            os.makedirs(save_dir, exist_ok=True)
            
            torch.save({
                'model_state_dict': model.state_dict(),
                'feature_mean': feature_mean,
                'feature_std': feature_std,
                'class_weights': class_weights.cpu().numpy(),
                'num_classes': 3
            }, os.path.join(save_dir, 'enrollment_model.pt'))
            
            tokenizer.save_pretrained(os.path.join(save_dir, 'tokenizer'))
            print(f"  ✓ Saved best model (F1: {best_val_f1:.4f}, Val Loss: {avg_val_loss:.4f})")
        
        # Early stopping trigger
        if patience_counter >= patience:
            print(f"\n🛑 Early stopping triggered! No improvement for {patience} epochs.")
            print(f"   Best F1: {best_val_f1:.4f}, Best Val Loss: {best_val_loss:.4f}")
            break
    
    print(f"\n✨ Training complete! Best validation F1: {best_val_f1:.4f}")
    print(f"📁 Model saved to: {save_dir}")
    
    return history
