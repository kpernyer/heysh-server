#!/usr/bin/env python3
"""
Quick API Routes Verification Script
Verifies that all API routes are correctly updated to use topic terminology
"""

import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

def test_route_imports():
    """Test that route modules can be imported."""
    print("=" * 70)
    print("TESTING API ROUTE IMPORTS")
    print("=" * 70)
    print()

    try:
        print("✓ Importing routes_data...")
        from service import routes_data
        print("  - Module imported successfully")

        print("✓ Importing routes_workflows...")
        from service import routes_workflows
        print("  - Module imported successfully")

        print("✓ Importing request schemas...")
        from app.schemas import requests
        print("  - Module imported successfully")

        print("✓ Importing response schemas...")
        from app.schemas import responses
        print("  - Module imported successfully")

        print("✓ Importing domain models...")
        from app.models import domain
        print("  - Module imported successfully")

        return True
    except Exception as e:
        print(f"✗ Import failed: {e}")
        return False


def test_request_schemas():
    """Test that request schemas have topic_id fields."""
    print()
    print("=" * 70)
    print("TESTING REQUEST SCHEMAS")
    print("=" * 70)
    print()

    from app.schemas.requests import (
        UploadDocumentRequest,
        AskQuestionRequest,
        SubmitReviewRequest,
        WorkflowDataRequest,
        DocumentDataRequest,
        CreateTopicRequest
    )

    schemas_to_test = [
        ("UploadDocumentRequest", UploadDocumentRequest),
        ("AskQuestionRequest", AskQuestionRequest),
        ("SubmitReviewRequest", SubmitReviewRequest),
        ("WorkflowDataRequest", WorkflowDataRequest),
        ("DocumentDataRequest", DocumentDataRequest),
    ]

    all_passed = True

    for name, schema in schemas_to_test:
        print(f"Testing {name}...")

        # Check if has topic_id field
        if hasattr(schema, '__fields__'):
            fields = schema.__fields__.keys()
        else:
            fields = schema.model_fields.keys()

        if 'topic_id' in fields:
            print(f"  ✓ Has 'topic_id' field")
        else:
            print(f"  ✗ Missing 'topic_id' field")
            all_passed = False

        if 'domain_id' in fields:
            print(f"  ✗ Still has 'domain_id' field (should be removed)")
            all_passed = False

    # Test CreateTopicRequest separately
    print(f"Testing CreateTopicRequest...")
    if hasattr(CreateTopicRequest, '__fields__'):
        fields = CreateTopicRequest.__fields__.keys()
    else:
        fields = CreateTopicRequest.model_fields.keys()

    required_fields = ['topic_id', 'name', 'created_by']
    for field in required_fields:
        if field in fields:
            print(f"  ✓ Has '{field}' field")
        else:
            print(f"  ✗ Missing '{field}' field")
            all_passed = False

    return all_passed


def test_model_classes():
    """Test that model classes are renamed."""
    print()
    print("=" * 70)
    print("TESTING MODEL CLASSES")
    print("=" * 70)
    print()

    from app.models.domain import (
        Topic,
        TopicStatus,
        TopicRole,
        TopicMember,
        BootstrapInput,
        BootstrapResult
    )

    classes_to_test = [
        ("Topic", Topic),
        ("TopicStatus", TopicStatus),
        ("TopicRole", TopicRole),
        ("TopicMember", TopicMember),
        ("BootstrapInput", BootstrapInput),
        ("BootstrapResult", BootstrapResult),
    ]

    print("Checking model classes exist:")
    for name, cls in classes_to_test:
        print(f"  ✓ {name} class exists")

    # Check TopicRole enum values
    print("\nChecking TopicRole enum values:")
    expected_roles = ['OWNER', 'CONTRIBUTOR', 'CONTROLLER', 'MEMBER']
    for role in expected_roles:
        if hasattr(TopicRole, role):
            print(f"  ✓ TopicRole.{role} exists")
        else:
            print(f"  ✗ TopicRole.{role} missing")
            return False

    # Check field names in Topic model
    print("\nChecking Topic model fields:")
    if hasattr(Topic, '__fields__'):
        fields = Topic.__fields__.keys()
    else:
        fields = Topic.model_fields.keys()

    expected_fields = ['id', 'name', 'description', 'owner_id', 'status']
    for field in expected_fields:
        if field in fields:
            print(f"  ✓ Topic has '{field}' field")
        else:
            print(f"  ✗ Topic missing '{field}' field")
            return False

    return True


def test_route_definitions():
    """Test that routes are defined correctly."""
    print()
    print("=" * 70)
    print("TESTING ROUTE DEFINITIONS")
    print("=" * 70)
    print()

    try:
        from service.routes_data import router as data_router

        # Get all routes from the router
        routes = []
        for route in data_router.routes:
            if hasattr(route, 'path') and hasattr(route, 'methods'):
                routes.append((route.path, list(route.methods)))

        print("Routes in routes_data:")
        topic_routes = []
        domain_routes = []

        for path, methods in routes:
            method_str = ', '.join(methods)
            print(f"  {method_str:10} {path}")

            if '/topics' in path:
                topic_routes.append(path)
            if '/domains' in path:
                domain_routes.append(path)

        print(f"\n✓ Found {len(topic_routes)} routes with '/topics'")
        print(f"✓ Found {len(domain_routes)} routes with '/domains' (should be 0)")

        if domain_routes:
            print("\n⚠️  WARNING: Still have /domains routes:")
            for route in domain_routes:
                print(f"    - {route}")

        return len(domain_routes) == 0

    except Exception as e:
        print(f"✗ Error testing routes: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """Run all tests."""
    print("\n" + "=" * 70)
    print("API ROUTES VERIFICATION")
    print("=" * 70)
    print()

    results = {}

    # Run tests
    results['imports'] = test_route_imports()
    results['schemas'] = test_request_schemas()
    results['models'] = test_model_classes()
    results['routes'] = test_route_definitions()

    # Summary
    print()
    print("=" * 70)
    print("SUMMARY")
    print("=" * 70)
    print()

    for test_name, passed in results.items():
        status = "✓ PASS" if passed else "✗ FAIL"
        print(f"{status:10} {test_name.upper()}")

    print()

    all_passed = all(results.values())

    if all_passed:
        print("=" * 70)
        print("✅ ALL TESTS PASSED - API IS CORRECTLY UPDATED")
        print("=" * 70)
        return 0
    else:
        print("=" * 70)
        print("⚠️  SOME TESTS FAILED - REVIEW ERRORS ABOVE")
        print("=" * 70)
        return 1


if __name__ == "__main__":
    sys.exit(main())
