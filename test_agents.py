"""Test script for individual agents."""

import os
import sys
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def test_news_collector():
    """Test the news collection agent."""
    print("Testing News Collector Agent...")
    try:
        from news_agents.news_collector import NewsCollectorAgent
        collector = NewsCollectorAgent()
        
        # Test with a single company
        articles = collector.collect_news_for_company("Tiger Analytics")
        print(f"✅ News Collector: Found {len(articles)} articles")
        
        if articles:
            print(f"Sample article: {articles[0].get('title', 'No title')}")
        
        return True
    except Exception as e:
        print(f"❌ News Collector failed: {e}")
        return False

def test_deduplicator():
    """Test the deduplication agent."""
    print("Testing Deduplicator Agent...")
    try:
        from news_agents.deduplicator import DeduplicatorAgent
        deduplicator = DeduplicatorAgent()
        
        # Test with sample articles
        sample_articles = [
            {
                'title': 'Tiger Analytics announces AI partnership',
                'snippet': 'Tiger Analytics has announced a new AI partnership...',
                'company': 'Tiger Analytics',
                'url': 'https://example.com/1'
            },
            {
                'title': 'Tiger Analytics AI partnership news',
                'snippet': 'Tiger Analytics announced a partnership in AI...',
                'company': 'Tiger Analytics',
                'url': 'https://example.com/2'
            }
        ]
        
        unique_articles = deduplicator.deduplicate_articles(sample_articles, "Tiger Analytics")
        print(f"✅ Deduplicator: {len(sample_articles)} -> {len(unique_articles)} articles")
        
        return True
    except Exception as e:
        print(f"❌ Deduplicator failed: {e}")
        return False

def test_storage_agent():
    """Test the storage agent."""
    print("Testing Storage Agent...")
    try:
        from news_agents.storage import StorageAgent
        storage = StorageAgent()
        
        # Test with sample article
        sample_article = {
            'title': 'Test article',
            'snippet': 'This is a test article',
            'company': 'Tiger Analytics',
            'url': 'https://example.com/test'
        }
        
        result = storage.store_single_article(sample_article)
        print(f"✅ Storage Agent: Article stored = {result}")
        
        return True
    except Exception as e:
        print(f"❌ Storage Agent failed: {e}")
        return False

def test_email_agent():
    """Test the email agent."""
    print("Testing Email Agent...")
    try:
        from news_agents.email_sender import EmailSenderAgent
        email_sender = EmailSenderAgent()
        
        # Test email configuration
        config_valid = email_sender.validate_email_config()
        print(f"✅ Email Agent: Configuration valid = {config_valid}")
        
        if config_valid:
            # Test email formatting
            sample_articles = [
                {
                    'title': 'Tiger Analytics AI News',
                    'snippet': 'Tiger Analytics announced new AI capabilities',
                    'company': 'Tiger Analytics',
                    'url': 'https://example.com',
                    'published_date': '2024-01-01'
                }
            ]
            
            html_content = email_sender.format_email_content(sample_articles, ["Tiger Analytics"])
            print(f"✅ Email Agent: HTML content generated ({len(html_content)} chars)")
        
        return True
    except Exception as e:
        print(f"❌ Email Agent failed: {e}")
        return False

def test_full_pipeline():
    """Test the full pipeline."""
    print("Testing Full Pipeline...")
    try:
        from main import NewsAgentOrchestrator
        orchestrator = NewsAgentOrchestrator()
        
        # Test environment validation
        env_valid = orchestrator.validate_environment()
        print(f"✅ Environment validation: {env_valid}")
        
        if env_valid:
            print("✅ Full pipeline ready to run")
        else:
            print("❌ Environment validation failed")
        
        return env_valid
    except Exception as e:
        print(f"❌ Full pipeline test failed: {e}")
        return False

def main():
    """Run all tests."""
    print("🧪 Running News Agent Tests\n")
    
    tests = [
        ("Environment", lambda: os.getenv("OPENAI_API_KEY") is not None),
        ("News Collector", test_news_collector),
        ("Deduplicator", test_deduplicator),
        ("Storage Agent", test_storage_agent),
        ("Email Agent", test_email_agent),
        ("Full Pipeline", test_full_pipeline)
    ]
    
    results = []
    for test_name, test_func in tests:
        try:
            result = test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"❌ {test_name} test crashed: {e}")
            results.append((test_name, False))
        print()
    
    # Summary
    print("📊 Test Results Summary:")
    passed = 0
    for test_name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"  {test_name}: {status}")
        if result:
            passed += 1
    
    print(f"\n🎯 Tests passed: {passed}/{len(results)}")
    
    if passed == len(results):
        print("🎉 All tests passed! Your news agent is ready to go.")
        return 0
    else:
        print("⚠️  Some tests failed. Please check the configuration.")
        return 1

if __name__ == "__main__":
    exit(main())

