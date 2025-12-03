"""
Training Script for Enrollment Prediction Model

This script trains the BioBERT-based enrollment prediction model using data from ChromaDB.
Run this script to train the model before using it for predictions.

Usage:
    python train_model.py [--epochs 10] [--batch-size 16]
"""

import argparse
import sys
import os
from dotenv import load_dotenv

# Add parent directory to Python path
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
if parent_dir not in sys.path:
    sys.path.insert(0, parent_dir)

# Load environment variables from .env file in parent directory
env_path = os.path.join(parent_dir, '.env')
load_dotenv(env_path)

# Now import from ml_models package
try:
    from ml_models.training import train_enrollment_model
except ImportError:
    # If that fails, try direct import (when running from ml_models dir)
    from training import train_enrollment_model


def main():
    parser = argparse.ArgumentParser(description='Train Enrollment Prediction Model')
    parser.add_argument('--epochs', type=int, default=10, help='Number of training epochs')
    parser.add_argument('--batch-size', type=int, default=16, help='Batch size for training')
    parser.add_argument('--learning-rate', type=float, default=2e-5, help='Learning rate')
    parser.add_argument('--max-samples', type=int, default=None, help='Maximum samples to use (None for all)')
    parser.add_argument('--freeze-bert', action='store_true', help='Freeze BioBERT parameters')
    parser.add_argument('--collection', type=str, default='clinical_trials', help='ChromaDB collection name')
    
    args = parser.parse_args()
    
    print("=" * 60)
    print("ENROLLMENT PREDICTION MODEL TRAINING")
    print("=" * 60)
    print(f"\nConfiguration:")
    print(f"  Epochs: {args.epochs}")
    print(f"  Batch Size: {args.batch_size}")
    print(f"  Learning Rate: {args.learning_rate}")
    print(f"  Max Samples: {args.max_samples or 'All'}")
    print(f"  Freeze BERT: {args.freeze_bert}")
    print(f"  Collection: {args.collection}")
    print("\n" + "=" * 60 + "\n")
    
    # Train the model
    history = train_enrollment_model(
        collection_name=args.collection,
        epochs=args.epochs,
        batch_size=args.batch_size,
        learning_rate=args.learning_rate,
        max_samples=args.max_samples,
        freeze_bert=args.freeze_bert
    )
    
    print("\n" + "=" * 60)
    print("TRAINING COMPLETE!")
    print("=" * 60)
    print(f"\nFinal Metrics:")
    print(f"  Best Validation F1: {max(history['val_f1']):.4f}")
    print(f"  Best Validation Accuracy: {max(history['val_accuracy']):.4f}")
    print(f"\nModel saved to: ml_models/saved_models/")
    print("\nYou can now use the model for predictions!")
    print("=" * 60)


if __name__ == '__main__':
    main()
