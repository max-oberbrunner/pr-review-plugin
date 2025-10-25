#!/usr/bin/env python3
"""
Simple connection test for Azure DevOps API.

This script performs basic authentication and connectivity checks
without fetching actual PR data.
"""

import os
import sys

try:
    import requests
except ImportError:
    print("❌ Error: 'requests' library not found.")
    print("   Install with: pip install requests")
    print("   Or run: ./setup_venv.sh")
    sys.exit(1)

try:
    from dotenv import load_dotenv
except ImportError:
    print("❌ Error: 'python-dotenv' library not found.")
    print("   Install with: pip install python-dotenv")
    print("   Or run: pip install -r requirements.txt")
    sys.exit(1)

import base64
from urllib.parse import quote

# Load environment variables from .env file
load_dotenv()


def encode_token(token: str) -> str:
    """Encode PAT token for basic auth."""
    credentials = f":{token}"
    return base64.b64encode(credentials.encode()).decode()


def test_connection(org: str, token: str) -> bool:
    """Test basic API connectivity and authentication."""

    print("🔧 Azure DevOps API Connection Test")
    print("=" * 50)
    print()

    # Step 1: Verify token format
    print("1️⃣  Verifying token format...")
    if not token or len(token) < 20:
        print("   ❌ Token appears invalid (too short)")
        return False
    print(f"   ✓ Token length: {len(token)} characters")
    print()

    # Step 2: Test organization endpoint
    print("2️⃣  Testing organization access...")
    url = f"https://dev.azure.com/{quote(org)}/_apis/projects?api-version=7.1"

    print(f"   URL: {url}")

    headers = {
        "Authorization": f"Basic {encode_token(token)}",
        "Content-Type": "application/json"
    }

    try:
        response = requests.get(url, headers=headers, timeout=10)

        print(f"   Status: {response.status_code}")

        if response.status_code == 200:
            data = response.json()
            project_count = data.get('count', 0)
            print(f"   ✓ Successfully connected!")
            print(f"   ✓ Found {project_count} projects in organization '{org}'")

            if project_count > 0:
                print()
                print("   📋 Available projects:")
                for project in data.get('value', [])[:5]:  # Show first 5
                    print(f"      • {project['name']} (ID: {project['id']})")

                if project_count > 5:
                    print(f"      ... and {project_count - 5} more")

            return True

        elif response.status_code == 401:
            print("   ❌ Authentication failed")
            print("      • Check your PAT token is valid")
            print("      • Verify token hasn't expired")
            print("      • Ensure token has required scopes (Code: Read)")
            return False

        elif response.status_code == 404:
            print("   ❌ Organization not found")
            print(f"      • Verify organization name: '{org}'")
            print("      • Check you have access to this organization")
            return False

        else:
            print(f"   ❌ Unexpected status code: {response.status_code}")
            print(f"      Response: {response.text[:200]}")
            return False

    except requests.exceptions.ConnectionError:
        print("   ❌ Connection error")
        print("      • Check your internet connection")
        print("      • Verify Azure DevOps is accessible")
        return False

    except requests.exceptions.Timeout:
        print("   ❌ Request timed out")
        print("      • Try again in a moment")
        return False

    except Exception as e:
        print(f"   ❌ Unexpected error: {e}")
        return False


def main():
    # Get credentials from environment or command line
    token = os.getenv("AZURE_DEVOPS_PAT")
    org = os.getenv("AZURE_DEVOPS_ORG")

    if not token:
        print("❌ Error: AZURE_DEVOPS_PAT environment variable not set")
        print()
        print("💡 Set it with:")
        print("   export AZURE_DEVOPS_PAT='your-token-here'")
        print()
        print("   Or add to .env file:")
        print("   AZURE_DEVOPS_PAT=your-token-here")
        sys.exit(1)

    if not org:
        print("⚠️  Warning: AZURE_DEVOPS_ORG not set")
        org = input("Enter your Azure DevOps organization name: ").strip()

        if not org:
            print("❌ Organization name required")
            sys.exit(1)

    print()
    success = test_connection(org, token)
    print()

    if success:
        print("✅ Connection test PASSED")
        print()
        print("🎯 Next steps:")
        print("   1. Set project and repo in .env:")
        print("      AZURE_DEVOPS_PROJECT=your-project")
        print("      AZURE_DEVOPS_REPO=your-repo")
        print()
        print("   2. Test fetching PR comments:")
        print("      ./fetch_pr_comments.py --org", org, "--project PROJECT --repo REPO --pr PR_ID")
        print()
        print("   3. For detailed debugging:")
        print("      python debug_api.py --org", org, "--project PROJECT --repo REPO --pr PR_ID")
    else:
        print("❌ Connection test FAILED")
        print()
        print("🆘 Troubleshooting:")
        print("   • Run: cat docs/DEBUGGING.md")
        print("   • Check: https://dev.azure.com/" + org)
        print("   • Create new token: https://dev.azure.com/" + org + "/_usersSettings/tokens")

    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
