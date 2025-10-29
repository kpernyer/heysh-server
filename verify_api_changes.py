#!/usr/bin/env python3
"""
Static verification of API changes (Domain → Topic)
Analyzes source files without importing to verify all changes are complete
"""

import re
from pathlib import Path


def check_file_for_patterns(filepath, patterns_to_find, patterns_to_avoid):
    """Check a file for required and forbidden patterns."""
    try:
        with open(filepath, 'r') as f:
            content = f.read()

        found = []
        avoided = []

        for pattern_name, pattern in patterns_to_find.items():
            if re.search(pattern, content):
                found.append(pattern_name)

        for pattern_name, pattern in patterns_to_avoid.items():
            if re.search(pattern, content):
                avoided.append(pattern_name)

        return found, avoided, content

    except Exception as e:
        return [], [], f"Error reading file: {e}"


def test_routes_data():
    """Test routes_data.py for topic endpoints."""
    print("=" * 70)
    print("TESTING: src/service/routes_data.py")
    print("=" * 70)

    filepath = Path("src/service/routes_data.py")

    patterns_to_find = {
        "GET /topics": r'@router\.get\(["\']\/topics["\']',
        "GET /topics/search": r'@router\.get\(["\']\/topics\/search["\']',
        "GET /topics/{topic_id}": r'@router\.get\(["\']\/topics\/\{topic_id\}["\']',
        "topic_id parameter": r'topic_id:\s*str',
        "list_topics function": r'async def list_topics\(',
        "search_topics function": r'async def search_topics\(',
        "get_topic function": r'async def get_topic\(',
    }

    patterns_to_avoid = {
        "domain_id parameter": r'domain_id:\s*str',
        "GET /domains endpoint": r'@router\.get\(["\']\/domains[^/]',
        "list_domains function": r'async def list_domains\(',
        "search_domains function": r'async def search_domains\(',
        "get_domain function": r'async def get_domain\(',
    }

    found, avoided, _ = check_file_for_patterns(filepath, patterns_to_find, patterns_to_avoid)

    print("\nRequired patterns (topic terminology):")
    for pattern in patterns_to_find:
        status = "✓" if pattern in found else "✗"
        print(f"  {status} {pattern}")

    print("\nForbidden patterns (domain terminology):")
    for pattern in patterns_to_avoid:
        status = "✓ NOT FOUND" if pattern not in avoided else "✗ STILL EXISTS"
        print(f"  {status} {pattern}")

    success = len(found) == len(patterns_to_find) and len(avoided) == 0
    print(f"\nResult: {'✓ PASS' if success else '✗ FAIL'}")
    return success


def test_routes_workflows():
    """Test routes_workflows.py for topic fields."""
    print("\n" + "=" * 70)
    print("TESTING: src/service/routes_workflows.py")
    print("=" * 70)

    filepath = Path("src/service/routes_workflows.py")

    patterns_to_find = {
        "POST /topics endpoint": r'@router\.post\(["\']\/topics["\']',
        "topic_id in logging": r'topic_id=request\.topic_id',
        "create_topic function": r'async def create_topic\(',
        "CreateTopicRequest import": r'CreateTopicRequest',
    }

    patterns_to_avoid = {
        "domain_id in logging": r'domain_id=request\.domain_id',
        "POST /domains endpoint": r'@router\.post\(["\']\/domains["\']',
        "create_domain function": r'async def create_domain\(',
    }

    found, avoided, _ = check_file_for_patterns(filepath, patterns_to_find, patterns_to_avoid)

    print("\nRequired patterns (topic terminology):")
    for pattern in patterns_to_find:
        status = "✓" if pattern in found else "✗"
        print(f"  {status} {pattern}")

    print("\nForbidden patterns (domain terminology):")
    for pattern in patterns_to_avoid:
        status = "✓ NOT FOUND" if pattern not in avoided else "✗ STILL EXISTS"
        print(f"  {status} {pattern}")

    success = len(found) == len(patterns_to_find) and len(avoided) == 0
    print(f"\nResult: {'✓ PASS' if success else '✗ FAIL'}")
    return success


def test_request_schemas():
    """Test request schemas for topic_id fields."""
    print("\n" + "=" * 70)
    print("TESTING: src/app/schemas/requests.py")
    print("=" * 70)

    filepath = Path("src/app/schemas/requests.py")

    patterns_to_find = {
        "UploadDocumentRequest class": r'class UploadDocumentRequest\(BaseModel\)',
        "AskQuestionRequest class": r'class AskQuestionRequest\(BaseModel\)',
        "SubmitReviewRequest class": r'class SubmitReviewRequest\(BaseModel\)',
        "WorkflowDataRequest class": r'class WorkflowDataRequest\(BaseModel\)',
        "DocumentDataRequest class": r'class DocumentDataRequest\(BaseModel\)',
        "CreateTopicRequest class": r'class CreateTopicRequest\(BaseModel\)',
        "topic_id fields present": r'topic_id:\s*str',
    }

    patterns_to_avoid = {
        "domain_id field": r'domain_id:\s*str\s*=\s*Field',
    }

    found, avoided, content = check_file_for_patterns(filepath, patterns_to_find, patterns_to_avoid)

    print("\nRequired patterns (topic_id fields):")
    for pattern in patterns_to_find:
        status = "✓" if pattern in found else "✗"
        print(f"  {status} {pattern}")

    print("\nForbidden patterns (domain_id fields):")
    for pattern in patterns_to_avoid:
        status = "✓ NOT FOUND" if pattern not in avoided else "✗ STILL EXISTS"
        print(f"  {status} {pattern}")

    # Count topic_id occurrences
    topic_id_count = len(re.findall(r'topic_id', content))
    domain_id_count = len(re.findall(r'domain_id', content))

    print(f"\nOccurrences:")
    print(f"  topic_id: {topic_id_count}")
    print(f"  domain_id: {domain_id_count} (should be 0)")

    success = len(found) >= 5 and len(avoided) == 0 and domain_id_count == 0
    print(f"\nResult: {'✓ PASS' if success else '✗ FAIL'}")
    return success


def test_domain_models():
    """Test domain.py models for Topic classes."""
    print("\n" + "=" * 70)
    print("TESTING: src/app/models/domain.py")
    print("=" * 70)

    filepath = Path("src/app/models/domain.py")

    patterns_to_find = {
        "Topic class": r'class Topic\(BaseModel\)',
        "TopicStatus enum": r'class TopicStatus\(Enum\)',
        "TopicRole enum": r'class TopicRole\(Enum\)',
        "TopicMember class": r'class TopicMember\(BaseModel\)',
        "OWNER role": r'OWNER\s*=\s*["\']owner["\']',
        "CONTRIBUTOR role": r'CONTRIBUTOR\s*=\s*["\']contributor["\']',
        "CONTROLLER role": r'CONTROLLER\s*=\s*["\']controller["\']',
        "MEMBER role": r'MEMBER\s*=\s*["\']member["\']',
    }

    patterns_to_avoid = {
        "Domain class": r'class Domain\(BaseModel\)',
        "DomainStatus enum": r'class DomainStatus\(Enum\)',
        "DomainRole enum": r'class DomainRole\(Enum\)',
        "DomainMember class": r'class DomainMember\(BaseModel\)',
    }

    found, avoided, _ = check_file_for_patterns(filepath, patterns_to_find, patterns_to_avoid)

    print("\nRequired patterns (Topic classes):")
    for pattern in patterns_to_find:
        status = "✓" if pattern in found else "✗"
        print(f"  {status} {pattern}")

    print("\nForbidden patterns (Domain classes):")
    for pattern in patterns_to_avoid:
        status = "✓ NOT FOUND" if pattern not in avoided else "✗ STILL EXISTS"
        print(f"  {status} {pattern}")

    success = len(found) == len(patterns_to_find) and len(avoided) == 0
    print(f"\nResult: {'✓ PASS' if success else '✗ FAIL'}")
    return success


def main():
    """Run all verification tests."""
    print("\n" + "=" * 70)
    print("API CHANGES VERIFICATION (Domain → Topic)")
    print("=" * 70)
    print()

    results = {
        "routes_data": test_routes_data(),
        "routes_workflows": test_routes_workflows(),
        "request_schemas": test_request_schemas(),
        "domain_models": test_domain_models(),
    }

    # Summary
    print("\n" + "=" * 70)
    print("SUMMARY")
    print("=" * 70)

    for test_name, passed in results.items():
        status = "✓ PASS" if passed else "✗ FAIL"
        print(f"{status:10} {test_name}")

    print()

    all_passed = all(results.values())

    if all_passed:
        print("=" * 70)
        print("✅ ALL VERIFICATIONS PASSED")
        print("=" * 70)
        print()
        print("Summary:")
        print("  ✓ API routes updated to use /topics endpoints")
        print("  ✓ Request schemas use topic_id instead of domain_id")
        print("  ✓ Models renamed to Topic, TopicRole, TopicMember, etc.")
        print("  ✓ All role semantics (OWNER, CONTRIBUTOR, CONTROLLER, MEMBER) present")
        print()
        print("The API is ready for frontend integration!")
        return 0
    else:
        print("=" * 70)
        print("⚠️  SOME VERIFICATIONS FAILED")
        print("=" * 70)
        print("\nPlease review the failed tests above.")
        return 1


if __name__ == "__main__":
    import sys
    sys.exit(main())
