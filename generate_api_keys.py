#!/usr/bin/env python3
"""
Generate API keys for the HackRX Document Q&A system
"""

import secrets
import string
from datetime import datetime

def generate_api_key(prefix: str = "hackrx", purpose: str = "general", length: int = 32) -> str:
    """
    Generate a secure API key
    
    Args:
        prefix: Prefix for the API key
        purpose: Purpose of the key (prod, dev, test, etc.)
        length: Length of the random part
        
    Returns:
        str: Generated API key
    """
    # Generate random alphanumeric string
    alphabet = string.ascii_letters + string.digits
    random_part = ''.join(secrets.choice(alphabet) for _ in range(length))
    
    # Get current year
    year = datetime.now().year
    
    # Format: hackrx-2024-prod-abc123def456...
    api_key = f"{prefix}-{year}-{purpose}-{random_part}"
    
    return api_key

def generate_multiple_keys(count: int = 3) -> list:
    """Generate multiple API keys for different purposes"""
    purposes = ["prod", "dev", "test", "demo", "backup"]
    keys = []
    
    for i in range(count):
        purpose = purposes[i % len(purposes)]
        key = generate_api_key(purpose=purpose)
        keys.append(key)
    
    return keys

def main():
    """Generate and display API keys"""
    print("🔑 HackRX API Key Generator")
    print("=" * 50)
    
    # Generate default keys
    print("\n📋 Default API Keys:")
    default_keys = [
        "hackrx-2024-prod-abc123def456ghi789jkl012mno345",
        "hackrx-2024-dev-xyz789uvw456rst123opq890lmn567", 
        "hackrx-2024-test-def456ghi789jkl012mno345pqr678"
    ]
    
    for i, key in enumerate(default_keys, 1):
        print(f"  {i}. {key}")
    
    # Generate new secure keys
    print("\n🔒 Newly Generated Secure Keys:")
    new_keys = generate_multiple_keys(5)
    
    for i, key in enumerate(new_keys, 1):
        print(f"  {i}. {key}")
    
    # Show environment variable format
    print("\n📄 Environment Variable Format:")
    all_keys = default_keys + new_keys
    env_value = ",".join(all_keys)
    print(f"API_KEYS={env_value}")
    
    # Show curl examples
    print("\n🌐 Usage Examples:")
    example_key = new_keys[0]
    
    print(f"""
# Synchronous processing:
curl -X POST "http://localhost:8000/hackrx/run" \\
  -H "Authorization: Bearer {example_key}" \\
  -H "Content-Type: application/json" \\
  -d '{{
    "documents": "https://example.com/policy.pdf",
    "questions": ["What is the waiting period?"]
  }}'

# Direct LLM query:
curl -X GET "http://localhost:8000/llm?query=What is insurance?" \\
  -H "Authorization: Bearer {example_key}"

# Webhook with callback:
curl -X POST "http://localhost:8000/hackrx/webhook" \\
  -H "Authorization: Bearer {example_key}" \\
  -H "Content-Type: application/json" \\
  -d '{{
    "documents": "https://example.com/policy.pdf",
    "questions": ["What is the waiting period?"],
    "callback_url": "https://your-app.com/callback"
  }}'
""")
    
    print("\n⚙️ Configuration:")
    print("Add these to your .env file or environment variables:")
    print(f"API_KEY_ENABLED=true")
    print(f"API_KEYS={env_value}")
    
    print("\n🔐 Security Notes:")
    print("- Store these keys securely")
    print("- Use different keys for different environments")
    print("- Rotate keys periodically")
    print("- Never commit keys to version control")

if __name__ == "__main__":
    main()
