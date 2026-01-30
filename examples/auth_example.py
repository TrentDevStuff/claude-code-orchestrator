"""
Example: Using API Key Authentication

Demonstrates:
1. Generating API keys
2. Making authenticated requests
3. Handling rate limits
4. Key management
"""

import requests
import time
from src.auth import AuthManager


def main():
    print("=" * 70)
    print("API Key Authentication Example")
    print("=" * 70)

    # Initialize AuthManager
    print("\n1. Initializing AuthManager...")
    auth_manager = AuthManager(db_path="data/auth.db")

    # Generate API key
    print("\n2. Generating API key...")
    project_id = "example-project"
    api_key = auth_manager.generate_key(
        project_id=project_id,
        rate_limit=10  # Low limit for demo
    )
    print(f"   API Key: {api_key}")
    print(f"   Project ID: {project_id}")
    print(f"   Rate Limit: 10 requests/minute")

    # Get key info
    print("\n3. Retrieving key information...")
    info = auth_manager.get_key_info(api_key)
    print(f"   Created: {info['created_at']}")
    print(f"   Last Used: {info['last_used_at']}")
    print(f"   Revoked: {info['revoked']}")

    # Validate key
    print("\n4. Validating API key...")
    is_valid, returned_project_id = auth_manager.validate_key(api_key)
    print(f"   Valid: {is_valid}")
    print(f"   Project ID: {returned_project_id}")

    # Test rate limiting
    print("\n5. Testing rate limiting (10 requests)...")
    for i in range(12):
        allowed = auth_manager.check_rate_limit(api_key)
        status = "✓ Allowed" if allowed else "✗ Blocked (rate limit)"
        print(f"   Request {i+1:2d}: {status}")

    # Get updated key info
    print("\n6. Key info after usage...")
    info = auth_manager.get_key_info(api_key)
    print(f"   Last Used: {info['last_used_at']}")

    # Revoke key
    print("\n7. Revoking API key...")
    success = auth_manager.revoke_key(api_key)
    print(f"   Revoked: {success}")

    # Try to validate revoked key
    print("\n8. Validating revoked key...")
    is_valid, _ = auth_manager.validate_key(api_key)
    print(f"   Valid: {is_valid} (should be False)")

    print("\n" + "=" * 70)
    print("Example completed!")
    print("=" * 70)


def example_http_request():
    """
    Example of making an authenticated HTTP request.

    NOTE: This requires the API server to be running.
    Start with: python main.py
    """
    print("\n" + "=" * 70)
    print("HTTP Request Example (requires server running)")
    print("=" * 70)

    # Generate a test key
    auth_manager = AuthManager(db_path="data/auth.db")
    api_key = auth_manager.generate_key(project_id="http-example", rate_limit=100)

    print(f"\nGenerated API Key: {api_key}")

    # Make authenticated request
    headers = {"Authorization": f"Bearer {api_key}"}

    try:
        response = requests.post(
            "http://localhost:8080/v1/chat/completions",
            headers=headers,
            json={
                "messages": [{"role": "user", "content": "Say hello!"}],
                "model": "haiku"
            },
            timeout=5
        )

        if response.status_code == 200:
            data = response.json()
            print(f"\nSuccess!")
            print(f"Response: {data['content'][:100]}...")
        else:
            print(f"\nError: {response.status_code}")
            print(f"Detail: {response.json()}")

    except requests.exceptions.ConnectionError:
        print("\nServer not running. Start with: python main.py")

    except Exception as e:
        print(f"\nError: {e}")


if __name__ == "__main__":
    main()

    # Uncomment to test HTTP requests (requires server running)
    # example_http_request()
