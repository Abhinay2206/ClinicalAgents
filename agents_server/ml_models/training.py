"""
Training Pipeline for Enrollment Prediction Model

Handles data loading from ChromaDB with batched loading to avoid quota limits,
training with class-weighted loss, and model checkpointing.
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
    """
    PyTorch Dataset for enrollment prediction
    Loads data from ChromaDB and prepares it for training
    """
    
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
        
        # Tokenize text
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
    
    Args:
        collection_name: ChromaDB collection name
        api_key: ChromaDB API key
        tenant: ChromaDB tenant
        database: ChromaDB database name
        max_samples: Maximum number of samples to load (None for all)
        
    Returns:
        Tuple of (texts, structured_features, labels)
    """
    # Load environment variables if not provided
    if api_key is None:
        api_key = os.getenv('CHROMA_API_KEY')
    if tenant is None:
        tenant = os.getenv('CHROMA_TENANT')
    
    # Connect to ChromaDB
    client = chromadb.CloudClient(
        api_key=api_key,
        tenant=tenant,
        database=database
    )
    
    collection = client.get_collection(collection_name)
    
    # Get total count
    total_count = collection.count()
    print(f"Total documents in collection: {total_count}")
    
    # Determine how many samples to load
    if max_samples:
        num_samples = min(max_samples, total_count)
    else:
        num_samples = total_count
    
    print(f"Loading {num_samples} samples in batches...")
    
    # Load data in batches to avoid quota limits (ChromaDB limit is ~300 per request)
    batch_size = 250  # Stay under limit
    texts = []
    structured_features_list = []
    labels = []
    
    num_batches = (num_samples + batch_size - 1) // batch_size
    
    for batch_idx in range(num_batches):
        offset = batch_idx * batch_size
        limit = min(batch_size, num_samples - offset)
        
        print(f"  Batch {batch_idx + 1}/{num_batches} (offset={offset}, limit={limit})...")
        
        # Fetch batch
        results = collection.get(
            limit=limit,
            offset=offset,
            include=['metadatas']
        )
        
        # Process batch
        for metadata in results['metadatas']:
            # Extract text features
            disease = metadata.get('disease', 'Unknown')
            criteria = metadata.get('eligibility_criteria', '')
            text = f"Disease: {disease}. Eligibility Criteria: {criteria}"
            texts.append(text)
            
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
            
            target_enrollment = metadata.get('target_enrollment', 100)
            site_count = metadata.get('site_count', 5)
            recruitment_duration = metadata.get('recruitment_duration_months', 12)
            
            # Handle missing or invalid numeric values
            try:
                target_enrollment = float(target_enrollment) if target_enrollment else 100
            except (ValueError, TypeError):
                target_enrollment = 100
            
            try:
                site_count = float(site_count) if site_count else 5
            except (ValueError, TypeError):
                site_count = 5
            
            try:
                recruitment_duration = float(recruitment_duration) if recruitment_duration else 12
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
                label = 0  # default to success
            
            labels.append(label)
    
    print(f"✓ Loaded {len(texts)} samples")
    
    return texts, np.array(structured_features_list, dtype=np.float32), np.array(labels, dtype=np.int64)


def compute_class_weights(labels: np.ndarray, num_classes: int = 3) -> torch.Tensor:
    """
    Compute class weights for handling imbalanced data
    
    Args:
        labels: Array of labels
        num_classes: Number of classes
        
    Returns:
        Class weights tensor
    """
    class_counts = np.bincount(labels, minlength=num_classes)
    total_samples = len(labels)
    
    # Inverse frequency weighting
    class_weights = total_samples / (num_classes * class_counts + 1e-6)
    
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
    freeze_bert: bool = False
) -> Dict[str, any]:
    """
    Main training function for enrollment prediction model
    
    Args:
        collection_name: ChromaDB collection name
        api_key: ChromaDB API key
        tenant: ChromaDB tenant
        database: ChromaDB database name
        epochs: Number of training epochs
        batch_size: Batch size
        learning_rate: Learning rate
        validation_split: Fraction of data for validation
        max_samples: Maximum samples to use (None for all)
        save_dir: Directory to save model
        device: Device to train on
        freeze_bert: Whether to freeze BioBERT parameters
        
    Returns:
        Training history dict
    """
    if device is None:
        device = 'cuda' if torch.cuda.is_available() else 'cpu'
    
    print(f"🚀 Starting training on {device}")
    
    # Load data from ChromaDB
    print("📊 Loading data from ChromaDB...")
    texts, structured_features, labels = load_data_from_chromadb(
        collection_name, api_key, tenant, database, max_samples
    )
    
    print(f"✓ Loaded {len(texts)} samples")
    print(f"  Class distribution: {np.bincount(labels)}")
    
    # Normalize structured features
    feature_mean = structured_features.mean(axis=0)
    feature_std = structured_features.std(axis=0) + 1e-6
    structured_features = (structured_features - feature_mean) / feature_std
    
    # Train/validation split
    train_texts, val_texts, train_features, val_features, train_labels, val_labels = train_test_split(
        texts, structured_features, labels,
        test_size=validation_split,
        random_state=42,
        stratify=labels
    )
    
    print(f"✓ Train: {len(train_texts)}, Validation: {len(val_texts)}")
    
    # Initialize tokenizer and model
    print("🔧 Initializing model...")
    tokenizer = AutoTokenizer.from_pretrained("dmis-lab/biobert-base-cased-v1.1")
    model = EnrollmentFusionModel(freeze_bert=freeze_bert).to(device)
    
    # Create datasets
    train_dataset = EnrollmentDataset(train_texts, train_features, train_labels, tokenizer)
    val_dataset = EnrollmentDataset(val_texts, val_features, val_labels, tokenizer)
    
    train_loader = DataLoader(train_dataset, batch_size=batch_size, shuffle=True)
    val_loader = DataLoader(val_dataset, batch_size=batch_size)
    
    # Compute class weights for imbalanced data
    class_weights = compute_class_weights(train_labels).to(device)
    print(f"✓ Class weights: {class_weights.cpu().numpy()}")
    
    # Loss and optimizer
    criterion = nn.CrossEntropyLoss(weight=class_weights)
    optimizer = torch.optim.AdamW(model.parameters(), lr=learning_rate)
    
    # Training loop
    history = {'train_loss': [], 'val_loss': [], 'val_accuracy': [], 'val_f1': []}
    best_val_f1 = 0.0
    
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
        
        # Save best model
        if val_f1 > best_val_f1:
            best_val_f1 = val_f1
            os.makedirs(save_dir, exist_ok=True)
            
            # Save model
            model_path = os.path.join(save_dir, 'enrollment_model.pt')
            torch.save({
                'model_state_dict': model.state_dict(),
                'feature_mean': feature_mean,
                'feature_std': feature_std,
                'class_weights': class_weights.cpu().numpy(),
                'num_classes': 3
            }, model_path)
            
            # Save tokenizer
            tokenizer_path = os.path.join(save_dir, 'tokenizer')
            tokenizer.save_pretrained(tokenizer_path)
            
            print(f"  ✓ Saved best model (F1: {best_val_f1:.4f})")
    
    print(f"\n✨ Training complete! Best validation F1: {best_val_f1:.4f}")
    print(f"📁 Model saved to: {save_dir}")
    
    return history
