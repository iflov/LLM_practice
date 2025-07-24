"""
Test script to verify DEFAULT_MODEL is being used correctly
"""
import requests
import json
import time

BASE_URL = "http://localhost:8000"

def test_default_model():
    """Test that DEFAULT_MODEL is used first"""
    print("\n=== Testing DEFAULT_MODEL Priority ===\n")
    
    # Create a new session
    response = requests.post(f"{BASE_URL}/sessions")
    session_id = response.json()["session_id"]
    print(f"Created session: {session_id}")
    
    # Send a chat request
    chat_request = {
        "message": "Hi! Which model are you using to respond to this message?",
        "session_id": session_id,
        "stream": False
    }
    
    print("\nSending chat request...")
    print(f"Request: {json.dumps(chat_request, indent=2)}")
    
    response = requests.post(
        f"{BASE_URL}/chat",
        json=chat_request,
        headers={"Content-Type": "application/json"}
    )
    
    if response.status_code == 200:
        result = response.json()
        print(f"\nResponse Status: SUCCESS")
        print(f"Model Used: {result.get('metadata', {}).get('model_used', 'Unknown')}")
        print(f"Response: {result.get('response', 'No response')[:200]}...")
        
        # Check if DEFAULT_MODEL was used
        model_used = result.get('metadata', {}).get('model_used', '')
        if 'google/gemini-2.0-flash-exp:free' in model_used:
            print("\n✅ SUCCESS: DEFAULT_MODEL (google/gemini-2.0-flash-exp:free) was used!")
        else:
            print(f"\n⚠️  WARNING: Expected DEFAULT_MODEL but got: {model_used}")
    else:
        print(f"\nResponse Status: ERROR ({response.status_code})")
        print(f"Error: {response.text}")
    
    # Test with tool calling
    print("\n\n=== Testing with Tool Calling ===\n")
    
    tool_request = {
        "message": "What's the weather in Seoul and calculate 25 * 4?",
        "session_id": session_id,
        "stream": False
    }
    
    print("Sending tool-calling request...")
    print(f"Request: {json.dumps(tool_request, indent=2)}")
    
    response = requests.post(
        f"{BASE_URL}/chat",
        json=tool_request,
        headers={"Content-Type": "application/json"}
    )
    
    if response.status_code == 200:
        result = response.json()
        print(f"\nResponse Status: SUCCESS")
        print(f"Model Used: {result.get('metadata', {}).get('model_used', 'Unknown')}")
        print(f"Tools Used: {result.get('metadata', {}).get('tools_used', [])}")
        print(f"Response: {result.get('response', 'No response')[:200]}...")
    else:
        print(f"\nResponse Status: ERROR ({response.status_code})")
        print(f"Error: {response.text}")

def check_model_priority():
    """Check model priority configuration"""
    print("\n=== Checking Model Priority Configuration ===\n")
    print("Expected model priority order:")
    print("1. DEFAULT_MODEL: google/gemini-2.0-flash-exp:free (from .env)")
    print("2. Then fallback models in priority order:")
    print("   - moonshotai/kimi-k2:free (priority: 0)")
    print("   - deepseek/deepseek-chat-v3-0324:free (priority: 1)")
    print("   - google/gemini-2.0-flash-exp:free (priority: 2)")
    print("   - google/gemini-flash-1.5-8b (priority: 3)")
    print("\nNote: DEFAULT_MODEL should be tried FIRST, regardless of priority")

if __name__ == "__main__":
    # First check configuration
    check_model_priority()
    
    # Then test actual behavior
    print("\n" + "="*50 + "\n")
    
    # Wait a bit to ensure server is ready
    print("Waiting for server to be ready...")
    time.sleep(2)
    
    try:
        test_default_model()
    except requests.exceptions.ConnectionError:
        print("\n❌ ERROR: Could not connect to server at http://localhost:8000")
        print("Make sure the server is running with: python main.py")
    except Exception as e:
        print(f"\n❌ ERROR: {str(e)}")