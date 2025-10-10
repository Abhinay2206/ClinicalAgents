#!/usr/bin/env python3
"""
Test script for individual clinical agents
"""
import os
import sys
import numpy as np
from dotenv import load_dotenv

# Add the agents_server directory to Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from gemini_client import GeminiClient
from agents.enrollment_agent import EnrollmentAgent
from agents.efficacy_agent import EfficacyAgent
from agents.safety_agent import SafetyAgent

def test_gemini_client():
    """Test Gemini client"""
    print("Testing Gemini Client...")
    try:
        client = GeminiClient()
        response = client.generate("Hello, please respond with 'Gemini is working correctly!'")
        print(f"Gemini Response: {response}")
        return True
    except Exception as e:
        print(f"Gemini Client Error: {e}")
        return False

def test_enrollment_agent():
    """Test Enrollment Agent with FAISS search"""
    print("\nTesting Enrollment Agent...")
    try:
        llm = GeminiClient()
        agent = EnrollmentAgent(llm)
        
        # Create a sample embedding (384 dimensions for sentence transformers)
        sample_embedding = np.random.rand(384).astype(np.float32)
        sample_embedding = sample_embedding / np.linalg.norm(sample_embedding)
        
        result = agent.analyze(sample_embedding, "Aspirin")
        print(f"Enrollment Analysis: {result[:200]}...")
        return True
    except Exception as e:
        print(f"Enrollment Agent Error: {e}")
        return False

def test_efficacy_agent():
    """Test Efficacy Agent with Neo4j"""
    print("\nTesting Efficacy Agent...")
    try:
        llm = GeminiClient()
        agent = EfficacyAgent(llm)
        
        result = agent.analyze("Aspirin")
        print(f"Efficacy Analysis: {result[:200]}...")
        return True
    except Exception as e:
        print(f"Efficacy Agent Error: {e}")
        return False

def test_safety_agent():
    """Test Safety Agent with FDA API"""
    print("\nTesting Safety Agent...")
    try:
        llm = GeminiClient()
        agent = SafetyAgent(llm)
        
        result = agent.analyze("aspirin")
        print(f"Safety Analysis: {result[:200]}...")
        return True
    except Exception as e:
        print(f"Safety Agent Error: {e}")
        return False

def main():
    """Run all tests"""
    load_dotenv()
    
    print("Clinical Agents Test Suite")
    print("=" * 50)
    
    tests = [
        ("Gemini Client", test_gemini_client),
        ("Enrollment Agent", test_enrollment_agent),
        ("Efficacy Agent", test_efficacy_agent),
        ("Safety Agent", test_safety_agent)
    ]
    
    results = {}
    for test_name, test_func in tests:
        try:
            results[test_name] = test_func()
        except Exception as e:
            print(f"Test {test_name} failed with exception: {e}")
            results[test_name] = False
    
    print("\n" + "=" * 50)
    print("TEST RESULTS SUMMARY")
    print("=" * 50)
    
    for test_name, passed in results.items():
        status = "✅ PASSED" if passed else "❌ FAILED"
        print(f"{test_name}: {status}")
    
    all_passed = all(results.values())
    print(f"\nOverall Status: {'✅ ALL TESTS PASSED' if all_passed else '❌ SOME TESTS FAILED'}")
    
    if not all_passed:
        print("\nTroubleshooting Tips:")
        print("1. Make sure you have set up your .env file with correct credentials")
        print("2. Install required packages: pip install -r requirements.txt")
        print("3. Check that your Neo4j database is running and accessible")
        print("4. Verify that FAISS index and metadata files exist in datasets/")

if __name__ == "__main__":
    main()