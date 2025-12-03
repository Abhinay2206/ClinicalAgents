"""
Test Script for Enrollment Prediction Model

This script tests the trained enrollment prediction model with various scenarios.
Run this after extracting the trained model to verify everything works.

Usage:
    python test_model.py
"""

import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from ml_models.inference import EnrollmentPredictor


def print_result(result, scenario_name):
    """Pretty print prediction results"""
    print("\n" + "=" * 60)
    print(f"📊 {scenario_name}")
    print("=" * 60)
    
    predicted = result['predicted_class']
    confidence = result['confidence_scores'][predicted] * 100
    
    print(f"\n✨ Prediction: {predicted.upper()}")
    print(f"🎯 Confidence: {confidence:.1f}%")
    
    print(f"\n📈 All Probabilities:")
    for class_name, prob in result['confidence_scores'].items():
        bar = "█" * int(prob * 50)
        print(f"  {class_name:10s}: {prob*100:5.1f}% {bar}")
    
    print(f"\n🔍 Top Risk Drivers:")
    for i, driver in enumerate(result['top_risk_drivers'][:5], 1):
        direction_emoji = "📈" if driver['direction'] == 'positive' else "📉"
        print(f"  {i}. {direction_emoji} {driver['feature']:25s} (impact: {driver['impact']:.3f})")
    
    print("=" * 60)


def main():
    print("\n" + "🚀" * 30)
    print("ENROLLMENT PREDICTION MODEL - TEST SUITE")
    print("🚀" * 30)
    
    # Initialize predictor
    print("\n📦 Loading model...")
    try:
        predictor = EnrollmentPredictor()
        print("✅ Model loaded successfully!")
    except FileNotFoundError as e:
        print(f"\n❌ Error: {e}")
        print("\n💡 Make sure you've extracted the model to: ml_models/saved_models/")
        return
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")
        return
    
    # Test Case 1: High Success Probability
    print("\n" + "🧪" * 30)
    print("TEST CASE 1: Large Phase 3 Trial (Expected: SUCCESS)")
    print("🧪" * 30)
    
    result1 = predictor.predict_enrollment(
        disease="Type 2 Diabetes",
        criteria_text="Adults aged 18-65 with HbA1c > 7.5%, no severe complications",
        tabular_features={
            'phase': 3,
            'target_enrollment': 500,
            'site_count': 25,
            'recruitment_duration': 18
        }
    )
    print_result(result1, "Large Phase 3 Diabetes Trial")
    
    # Test Case 2: Moderate Risk
    print("\n" + "🧪" * 30)
    print("TEST CASE 2: Early Phase Trial (Expected: DELAYED or SUCCESS)")
    print("🧪" * 30)
    
    result2 = predictor.predict_enrollment(
        disease="Alzheimer's Disease",
        criteria_text="Mild to moderate AD, MMSE 18-26, age 60-85",
        tabular_features={
            'phase': 2,
            'target_enrollment': 200,
            'site_count': 10,
            'recruitment_duration': 24
        }
    )
    print_result(result2, "Phase 2 Alzheimer's Trial")
    
    # Test Case 3: High Risk
    print("\n" + "🧪" * 30)
    print("TEST CASE 3: Small Phase 1 Trial (Expected: DELAYED or FAIL)")
    print("🧪" * 30)
    
    result3 = predictor.predict_enrollment(
        disease="Rare Genetic Disorder",
        criteria_text="Very specific genetic mutation, age 18-40, no prior treatments",
        tabular_features={
            'phase': 1,
            'target_enrollment': 50,
            'site_count': 3,
            'recruitment_duration': 36
        }
    )
    print_result(result3, "Phase 1 Rare Disease Trial")
    
    # Test Case 4: Cancer Trial
    print("\n" + "🧪" * 30)
    print("TEST CASE 4: Cancer Trial (Expected: Variable)")
    print("🧪" * 30)
    
    result4 = predictor.predict_enrollment(
        disease="Non-Small Cell Lung Cancer",
        criteria_text="Stage III-IV NSCLC, EGFR mutation positive, prior chemotherapy",
        tabular_features={
            'phase': 3,
            'target_enrollment': 800,
            'site_count': 50,
            'recruitment_duration': 24
        }
    )
    print_result(result4, "Phase 3 Lung Cancer Trial")
    
    # Test Case 5: Minimal Information
    print("\n" + "🧪" * 30)
    print("TEST CASE 5: Minimal Information (Default Values)")
    print("🧪" * 30)
    
    result5 = predictor.predict_enrollment(
        disease="Hypertension",
        criteria_text="",  # No criteria
        tabular_features=None  # Use defaults
    )
    print_result(result5, "Hypertension Trial (Defaults)")
    
    # Summary
    print("\n" + "📊" * 30)
    print("TEST SUMMARY")
    print("📊" * 30)
    
    results = [
        ("Large Phase 3 Diabetes", result1),
        ("Phase 2 Alzheimer's", result2),
        ("Phase 1 Rare Disease", result3),
        ("Phase 3 Lung Cancer", result4),
        ("Hypertension (Defaults)", result5)
    ]
    
    print(f"\n{'Trial':<30} {'Prediction':<12} {'Confidence':<12}")
    print("-" * 60)
    for name, result in results:
        pred = result['predicted_class']
        conf = result['confidence_scores'][pred] * 100
        print(f"{name:<30} {pred.upper():<12} {conf:>6.1f}%")
    
    print("\n" + "✅" * 30)
    print("ALL TESTS COMPLETED SUCCESSFULLY!")
    print("✅" * 30)
    
    print("\n💡 Next Steps:")
    print("  1. Review the predictions above")
    print("  2. Integrate into enrollment_agent.py (see README.md)")
    print("  3. Test with real clinical trial data")
    print("\n")


if __name__ == '__main__':
    main()
