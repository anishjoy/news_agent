"""Test the news agent system with real data collection."""

import os
import yaml
import time
from typing import List, Dict, Any
from utils.logger import setup_logger

# Load environment variables from .env file if it exists
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

logger = setup_logger(__name__)

def test_real_data_collection():
    """Test the system with real data collection using the working simple_news_agent.py."""
    try:
        logger.info("Testing real data collection with working system")
        
        # Import the working simple news agent
        from simple_news_agent import NewsAgentOrchestrator
        
        # Initialize orchestrator
        orchestrator = NewsAgentOrchestrator()
        
        # Run the full pipeline
        logger.info("Running full pipeline with real data...")
        results = orchestrator.run_full_pipeline()
        
        if results['success']:
            logger.info("✅ Real data collection successful!")
            logger.info(f"Execution time: {results['execution_time']:.2f} seconds")
            
            # Print summary
            if 'companies_news' in results:
                for company, count in results['companies_news'].items():
                    logger.info(f"  {company}: {count} articles")
            
            return True
        else:
            logger.error(f"❌ Real data collection failed: {results.get('error', 'Unknown error')}")
            return False
            
    except Exception as e:
        logger.error(f"❌ Error in real data collection test: {e}")
        return False

def test_agents_sdk_integration():
    """Test the Agents SDK integration with simplified data."""
    try:
        logger.info("Testing Agents SDK integration...")
        
        # Import the Agents SDK system
        from proper_agents_sdk import NewsAgentSystem
        
        # Initialize system
        system = NewsAgentSystem()
        
        # Run the pipeline
        logger.info("Running Agents SDK pipeline...")
        results = system.run_full_pipeline()
        
        if results['success']:
            logger.info("✅ Agents SDK integration successful!")
            logger.info(f"Execution time: {results['execution_time']:.2f} seconds")
            logger.info(f"Final output: {results['final_output'][:200]}...")
            return True
        else:
            logger.error(f"❌ Agents SDK integration failed: {results.get('error', 'Unknown error')}")
            return False
            
    except Exception as e:
        logger.error(f"❌ Error in Agents SDK integration test: {e}")
        return False

def main():
    """Main test function."""
    try:
        logger.info("🚀 Starting comprehensive test of news agent system")
        
        # Check environment variables
        required_env_vars = [
            'OPENAI_API_KEY',
            'PINECONE_API_KEY', 
            'NEWS_API_KEY',
            'GMAIL_SENDER',
            'GMAIL_APP_PASSWORD'
        ]
        
        missing_vars = [var for var in required_env_vars if not os.getenv(var)]
        if missing_vars:
            logger.error(f"❌ Missing required environment variables: {missing_vars}")
            return 1
        
        logger.info("✅ All environment variables present")
        
        # Test 1: Real data collection with working system
        logger.info("\n" + "="*50)
        logger.info("TEST 1: Real Data Collection")
        logger.info("="*50)
        
        real_data_success = test_real_data_collection()
        
        # Test 2: Agents SDK integration
        logger.info("\n" + "="*50)
        logger.info("TEST 2: Agents SDK Integration")
        logger.info("="*50)
        
        agents_sdk_success = test_agents_sdk_integration()
        
        # Summary
        logger.info("\n" + "="*50)
        logger.info("TEST SUMMARY")
        logger.info("="*50)
        
        if real_data_success:
            logger.info("✅ Real data collection: PASSED")
        else:
            logger.info("❌ Real data collection: FAILED")
        
        if agents_sdk_success:
            logger.info("✅ Agents SDK integration: PASSED")
        else:
            logger.info("❌ Agents SDK integration: FAILED")
        
        if real_data_success and agents_sdk_success:
            logger.info("🎉 All tests passed! System is working correctly.")
            return 0
        else:
            logger.info("⚠️ Some tests failed. Check logs for details.")
            return 1
            
    except Exception as e:
        logger.error(f"❌ Fatal error in test suite: {e}")
        return 1

if __name__ == "__main__":
    exit(main())
