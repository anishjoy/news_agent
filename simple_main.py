"""Simplified main script for testing the news agent system."""

import os
import yaml
from datetime import datetime
from typing import List, Dict, Any
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def test_environment():
    """Test environment variables."""
    print("🔍 Testing Environment Variables...")
    
    required_vars = [
        'OPENAI_API_KEY',
        'PINECONE_API_KEY', 
        'NEWS_API_KEY',
        'GMAIL_SENDER',
        'GMAIL_APP_PASSWORD'
    ]
    
    missing_vars = []
    for var in required_vars:
        value = os.getenv(var)
        if not value or value.startswith('your-'):
            missing_vars.append(var)
        else:
            print(f"✅ {var}: {'*' * 10}")  # Hide actual values
    
    if missing_vars:
        print(f"❌ Missing or invalid variables: {missing_vars}")
        return False
    
    print("✅ All environment variables are set!")
    return True

def test_config():
    """Test configuration file."""
    print("\n📋 Testing Configuration...")
    
    try:
        with open('config.yaml', 'r') as f:
            config = yaml.safe_load(f)
        
        companies = config.get('companies', [])
        priorities = config.get('priorities', [])
        
        print(f"✅ Companies: {[c['name'] for c in companies]}")
        print(f"✅ Priorities: {priorities}")
        
        return True
    except Exception as e:
        print(f"❌ Config error: {e}")
        return False

def test_news_api():
    """Test NewsAPI connection."""
    print("\n📰 Testing NewsAPI...")
    
    try:
        from newsapi import NewsApiClient
        
        api_key = os.getenv('NEWS_API_KEY')
        if not api_key or api_key.startswith('your-'):
            print("❌ NewsAPI key not set")
            return False
        
        newsapi = NewsApiClient(api_key=api_key)
        
        # Test with a simple query
        articles = newsapi.get_everything(
            q='AI',
            language='en',
            sort_by='publishedAt',
            page_size=5
        )
        
        print(f"✅ NewsAPI: Found {len(articles.get('articles', []))} articles")
        return True
        
    except Exception as e:
        print(f"❌ NewsAPI error: {e}")
        return False

def test_pinecone():
    """Test Pinecone connection."""
    print("\n🗄️ Testing Pinecone...")
    
    try:
        from pinecone import Pinecone
        
        api_key = os.getenv('PINECONE_API_KEY')
        if not api_key or api_key.startswith('your-'):
            print("❌ Pinecone API key not set")
            return False
        
        pc = Pinecone(api_key=api_key)
        
        # List indexes
        indexes = pc.list_indexes()
        print(f"✅ Pinecone: Connected, {len(indexes)} indexes found")
        return True
        
    except Exception as e:
        print(f"❌ Pinecone error: {e}")
        return False

def test_openai():
    """Test OpenAI connection."""
    print("\n🤖 Testing OpenAI...")
    
    try:
        from openai import OpenAI
        
        api_key = os.getenv('OPENAI_API_KEY')
        if not api_key or api_key.startswith('your-'):
            print("❌ OpenAI API key not set")
            return False
        
        client = OpenAI(api_key=api_key)
        
        # Test with a simple completion
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[{"role": "user", "content": "Hello"}],
            max_tokens=10
        )
        
        print("✅ OpenAI: Connection successful")
        return True
        
    except Exception as e:
        print(f"❌ OpenAI error: {e}")
        return False

def test_email():
    """Test email configuration."""
    print("\n📧 Testing Email Configuration...")
    
    try:
        import smtplib
        
        sender = os.getenv('GMAIL_SENDER')
        password = os.getenv('GMAIL_APP_PASSWORD')
        
        if not sender or not password:
            print("❌ Email credentials not set")
            return False
        
        # Test SMTP connection
        with smtplib.SMTP("smtp.gmail.com", 587) as server:
            server.starttls()
            server.login(sender, password)
        
        print("✅ Email: SMTP connection successful")
        return True
        
    except Exception as e:
        print(f"❌ Email error: {e}")
        return False

def main():
    """Run all tests."""
    print("🧪 News Agent System - Connection Tests\n")
    
    tests = [
        ("Environment Variables", test_environment),
        ("Configuration File", test_config),
        ("NewsAPI", test_news_api),
        ("Pinecone", test_pinecone),
        ("OpenAI", test_openai),
        ("Email", test_email)
    ]
    
    results = []
    for test_name, test_func in tests:
        try:
            result = test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"❌ {test_name} test crashed: {e}")
            results.append((test_name, False))
    
    # Summary
    print("\n📊 Test Results Summary:")
    passed = 0
    for test_name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"  {test_name}: {status}")
        if result:
            passed += 1
    
    print(f"\n🎯 Tests passed: {passed}/{len(results)}")
    
    if passed == len(results):
        print("🎉 All connections working! Your news agent is ready to go.")
        print("\n📋 Next steps:")
        print("1. Set up your Pinecone index with dimension 1536")
        print("2. Get a NewsAPI key from https://newsapi.org/")
        print("3. Run the full system with: python main.py")
        return 0
    else:
        print("⚠️  Some connections failed. Please check the configuration.")
        return 1

if __name__ == "__main__":
    exit(main())
