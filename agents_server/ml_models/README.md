# Enrollment Prediction Module

ML-powered clinical trial enrollment prediction using BioBERT fusion model.

## 🚀 Quick Start

### 1. Train Model (Google Colab - Recommended)
```
1. Upload train_colab.ipynb to https://colab.research.google.com/
2. Enable GPU: Runtime → Change runtime type → T4 GPU
3. Update ChromaDB credentials in cell 2
4. Upload enrollment_predictor.py and training.py when prompted
5. Run all cells (~40 min)
6. Download enrollment_model.zip
7. Extract to ml_models/saved_models/
```

### 2. Test Model
```bash
python test_model.py
```

### 3. Use in Code
```python
from ml_models.inference import EnrollmentPredictor

predictor = EnrollmentPredictor()
result = predictor.predict_enrollment(
    disease="Type 2 Diabetes",
    criteria_text="Adults 18-65",
    tabular_features={'phase': 3, 'target_enrollment': 500, 'site_count': 20, 'recruitment_duration': 18}
)
print(f"Prediction: {result['predicted_class']}")
```

---

### Step 1: Train the Model

Train the model using data from ChromaDB:

```bash
cd agents_server/ml_models
python train_model.py --epochs 10 --batch-size 16
```

**Training Options:**
- `--epochs`: Number of training epochs (default: 10)
- `--batch-size`: Batch size (default: 16)
- `--learning-rate`: Learning rate (default: 2e-5)
- `--max-samples`: Limit training samples (default: all)
- `--freeze-bert`: Freeze BioBERT parameters for faster training
- `--collection`: ChromaDB collection name (default: 'clinical_trials')

**Expected Output:**
```
🚀 Starting training on cuda
📊 Loading data from ChromaDB...
✓ Loaded 5000 samples
  Class distribution: [3000 1500  500]
✓ Train: 4000, Validation: 1000
🔧 Initializing model...
✓ Class weights: [0.5 1.0 3.0]

📈 Epoch 1/10
Training: 100%|██████████| 250/250 [02:15<00:00]
Validation: 100%|██████████| 63/63 [00:15<00:00]
  Train Loss: 0.8234
  Val Loss: 0.6543, Accuracy: 0.7850, F1: 0.7623
  ✓ Saved best model (F1: 0.7623)
...
✨ Training complete! Best validation F1: 0.8234
📁 Model saved to: ml_models/saved_models/
```

### Step 2: Make Predictions

#### Python API

```python
from ml_models.inference import EnrollmentPredictor

# Initialize predictor
predictor = EnrollmentPredictor()

# Make prediction
result = predictor.predict_enrollment(
    disease="Type 2 Diabetes",
    criteria_text="Adults aged 18-65 with HbA1c > 7.5%",
    tabular_features={
        'phase': 3,
        'target_enrollment': 500,
        'site_count': 20,
        'recruitment_duration': 18
    }
)

# View results
print(f"Predicted Outcome: {result['predicted_class']}")
print(f"Confidence: {result['confidence_scores'][result['predicted_class']] * 100:.1f}%")
print("\nTop Risk Drivers:")
for driver in result['top_risk_drivers']:
    print(f"  - {driver['feature']}: {driver['direction']} impact")
```

**Output:**
```
Predicted Outcome: success
Confidence: 82.3%

Top Risk Drivers:
  - phase: positive impact
  - site_count: positive impact
  - target_enrollment: negative impact
```

#### Standalone Function

```python
from ml_models.inference import predict_enrollment

result = predict_enrollment(
    disease="Alzheimer's Disease",
    criteria_text="Mild to moderate AD, MMSE 18-26",
    tabular_features={'phase': 2, 'target_enrollment': 200, 'site_count': 10, 'recruitment_duration': 24}
)
```

## 🔧 Integration with Enrollment Agent

To integrate ML predictions into the existing enrollment agent:

```python
# In agents/enrollment_agent.py

# 1. Add import at top
try:
    from ml_models.inference import EnrollmentPredictor
    ML_AVAILABLE = True
except ImportError:
    ML_AVAILABLE = False

# 2. Initialize in __init__
if ML_AVAILABLE:
    try:
        self.ml_predictor = EnrollmentPredictor()
    except:
        self.ml_predictor = None

# 3. Use in predict_enrollment_success method
def predict_enrollment_success(self, trial_metadata):
    # Try ML prediction first
    if self.ml_predictor:
        try:
            ml_result = self.ml_predictor.predict_enrollment(
                disease=trial_metadata.get('disease', 'Unknown'),
                criteria_text=trial_metadata.get('eligibility_criteria', ''),
                tabular_features={
                    'phase': self._extract_phase_number(trial_metadata.get('phase')),
                    'target_enrollment': trial_metadata.get('target_enrollment', 100),
                    'site_count': trial_metadata.get('site_count', 5),
                    'recruitment_duration': trial_metadata.get('recruitment_duration_months', 12)
                }
            )
            # Return ML-enhanced prediction
            return {
                'score': self._ml_score_to_percentage(ml_result),
                'category': f"ML: {ml_result['predicted_class'].title()}",
                'emoji': self._get_emoji(ml_result['predicted_class']),
                'factors': [f"🤖 {d['feature']}: {d['direction']}" for d in ml_result['top_risk_drivers']],
                'ml_prediction': ml_result
            }
        except Exception as e:
            print(f"ML prediction failed: {e}")
    
    # Fallback to rule-based prediction
    return self._rule_based_prediction(trial_metadata)
```

## 📊 Model Architecture

```
Input:
  ├─ Text: Disease + Eligibility Criteria
  │   └─ BioBERT Encoder (768-dim)
  └─ Structured Features: [phase, enrollment, sites, duration]
      └─ MLP (4 → 64 → 32)

Fusion:
  └─ Concatenate (768 + 32 = 800-dim)
      └─ MLP (800 → 128 → 3)

Output:
  └─ Softmax → [P(success), P(delayed), P(fail)]
```

## 🎓 Training Data Format

The model expects ChromaDB metadata with these fields:

```python
{
    'disease': 'Type 2 Diabetes',
    'eligibility_criteria': 'Adults 18-65...',
    'phase': 'Phase 3',
    'target_enrollment': 500,
    'site_count': 20,
    'recruitment_duration_months': 18,
    'status': 'Completed'  # Used to derive labels
}
```

**Label Mapping:**
- `success` (0): Completed, Recruiting, Active
- `delayed` (1): Delayed, Suspended
- `fail` (2): Terminated, Withdrawn

## 🔍 Explainability

### Gradient-Based Feature Importance

```python
result = predictor.predict_enrollment(...)

for driver in result['top_risk_drivers']:
    print(f"{driver['feature']}: {driver['impact']:.3f} ({driver['direction']})")
```

### SHAP Analysis (Advanced)

```python
from ml_models.explainability import SHAPExplainer

# Create explainer
explainer = SHAPExplainer(predictor.model)

# Get SHAP values
explanation = explainer.explain_prediction(
    structured_features=normalized_features
)

print("SHAP Feature Importance:")
for exp in explanation['explanations']:
    print(f"  {exp['feature']}: {exp['shap_value']:.3f}")
```

## 🐛 Troubleshooting

### Model Not Found Error

```
FileNotFoundError: Model not found at ml_models/saved_models/enrollment_model.pt
```

**Solution:** Train the model first:
```bash
python ml_models/train_model.py
```

### CUDA Out of Memory

```
RuntimeError: CUDA out of memory
```

**Solution:** Reduce batch size or use CPU:
```bash
python train_model.py --batch-size 8
```

Or force CPU training by setting:
```python
device = 'cpu'
```

### Import Error

```
ImportError: No module named 'transformers'
```

**Solution:** Install dependencies:
```bash
pip install torch>=2.0.0 transformers>=4.30.0 shap>=0.42.0
```

## 📈 Performance Tips

1. **Faster Training:**
   - Use `--freeze-bert` to freeze BioBERT parameters
   - Reduce `--max-samples` for quick experiments
   - Use GPU if available

2. **Better Accuracy:**
   - Train for more epochs (15-20)
   - Use larger batch size if memory allows
   - Don't freeze BERT for better text understanding

3. **Production Deployment:**
   - Save model to persistent storage
   - Use model versioning
   - Monitor prediction latency
   - Cache predictions for repeated queries

## 📝 API Reference

### `EnrollmentPredictor`

**Methods:**
- `__init__(model_dir='ml_models/saved_models', device=None)`
- `predict_enrollment(disease, criteria_text='', tabular_features=None) -> dict`

**Returns:**
```python
{
    'predicted_class': str,  # 'success', 'delayed', or 'fail'
    'confidence_scores': {
        'success': float,
        'delayed': float,
        'fail': float
    },
    'top_risk_drivers': [
        {
            'feature': str,
            'impact': float,
            'direction': str,  # 'positive' or 'negative'
            'value': float
        }
    ]
}
```

## 🎯 Next Steps

1. **Train the model** with your ChromaDB data
2. **Test predictions** with sample trials
3. **Integrate** into enrollment agent (optional)
4. **Monitor** prediction accuracy
5. **Retrain** periodically with new data

## 📚 Additional Resources

- [BioBERT Paper](https://arxiv.org/abs/1901.08746)
- [SHAP Documentation](https://shap.readthedocs.io/)
- [PyTorch Documentation](https://pytorch.org/docs/)

---

**Need Help?** Check the implementation files:
- `ml_models/enrollment_predictor.py` - Model architecture
- `ml_models/training.py` - Training pipeline
- `ml_models/inference.py` - Prediction interface
- `ml_models/explainability.py` - SHAP integration
