#!/usr/bin/env python3
"""
Simple validation test for VerifyAI pipeline structure.
Tests the pipeline logic without loading actual ML models.
"""

import sys
import os
sys.path.append(os.path.dirname(__file__))

def test_imports():
    """Test that all pipeline modules can be imported."""
    try:
        from pipeline.ingest import validate_file, validate_caption
        from pipeline.preprocess import preprocess_media
        from pipeline.clip_gate import should_early_exit
        from pipeline.blip_captioner import generate_caption
        from pipeline.ner_extractor import extract_entities
        from pipeline.comparator import compare_consistency
        from pipeline.evidence_search import search_evidence
        from pipeline.output_builder import build_early_exit_bilan, build_full_bilan
        from models.loader import load_all_models
        print("✓ All pipeline modules imported successfully")
        return True
    except ImportError as e:
        print(f"✗ Import error: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_constants():
    """Test that constants are properly defined."""
    try:
        from pipeline.ingest import SUPPORTED_IMAGE_TYPES, SUPPORTED_VIDEO_TYPES, MAX_FILE_SIZE
        assert SUPPORTED_IMAGE_TYPES == {'image/jpeg', 'image/png', 'image/webp'}
        assert SUPPORTED_VIDEO_TYPES == {'video/mp4', 'video/quicktime'}
        assert MAX_FILE_SIZE == 100 * 1024 * 1024  # 100MB
        print("✓ Constants are correctly defined")
        return True
    except Exception as e:
        print(f"✗ Constants test failed: {e}")
        return False

def test_output_structure():
    """Test that output builder creates proper structure."""
    try:
        from pipeline.output_builder import build_early_exit_bilan, build_full_bilan

        # Test early exit bilan
        early_bilan = build_early_exit_bilan(
            clip_score=0.95,
            processing_time_ms=1200
        )
        required_keys = ['verdict', 'score', 'processing_time', 'file_name', 'early_exit']
        for key in required_keys:
            assert key in early_bilan, f"Missing key: {key}"
        assert early_bilan['early_exit'] == True

        # Test full bilan
        full_bilan = build_full_bilan(
            verdict="CONSISTENT",
            score=0.85,
            flags=[],
            explanation="Test explanation",
            clip_score=0.9,
            blip_description="Test description",
            entities={'persons': [], 'locations': [], 'organizations': []},
            evidence=[],
            processing_time=2.5,
            file_name="test.jpg"
        )
        required_keys = ['verdict', 'score', 'flags', 'explanation', 'analysis_detail', 'evidence', 'processing_time', 'file_name', 'early_exit']
        for key in required_keys:
            assert key in full_bilan, f"Missing key: {key}"
        assert full_bilan['early_exit'] == False

        print("✓ Output structures are correct")
        return True
    except Exception as e:
        print(f"✗ Output structure test failed: {e}")
        return False

def main():
    """Run all validation tests."""
    print("Running VerifyAI pipeline validation tests...\n")

    tests = [
        test_imports,
        test_constants,
        test_output_structure
    ]

    passed = 0
    total = len(tests)

    for test in tests:
        if test():
            passed += 1
        print()

    print(f"Results: {passed}/{total} tests passed")

    if passed == total:
        print("🎉 All validation tests passed! The pipeline structure is correct.")
        return 0
    else:
        print("❌ Some tests failed. Please check the errors above.")
        return 1

if __name__ == "__main__":
    sys.exit(main())