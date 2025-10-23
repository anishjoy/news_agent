"""Final comprehensive test of OpenAI Agents SDK with real data collection."""

import os
import yaml
import time
from typing import List, Dict, Any
from agents import Agent, Runner, function_tool
from utils.logger import setup_logger

# Load environment variables from .env file if it exists
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

logger = setup_logger(__name__)

# Global variables to store system state
_collected_news = {}
_deduplicated_news = {}
_storage_results = {}

@function_tool
def collect_news_for_company(company: str) -> str:
    """Collect news for a specific company using direct API calls."""
    try:
        # Import the working news collector without Agents SDK
        from news_agents.news_collector import NewsCollectorAgent
        
        collector = NewsCollectorAgent()
        # Use the direct method that works without Agents SDK
        articles = collector.collect_news_for_company(company)
        
        # Store in global state
        _collected_news[company] = articles
        
        logger.info(f"Collected {len(articles)} articles for {company}")
        return f"Successfully collected {len(articles)} articles for {company}"
        
    except Exception as e:
        logger.error(f"Error collecting news for {company}: {e}")
        return f"Error collecting news for {company}: {e}"

@function_tool
def deduplicate_articles(company: str) -> str:
    """Deduplicate articles for a specific company."""
    try:
        # Import the working deduplicator without Agents SDK
        from news_agents.deduplicator import DeduplicatorAgent
        
        if company not in _collected_news:
            return f"No collected news found for {company}"
        
        deduplicator = DeduplicatorAgent()
        articles = _collected_news[company]
        unique_articles = deduplicator.deduplicate_articles(articles, company)
        
        # Store in global state
        _deduplicated_news[company] = unique_articles
        
        logger.info(f"Deduplicated {len(articles)} articles to {len(unique_articles)} unique articles for {company}")
        return f"Successfully deduplicated articles for {company}: {len(unique_articles)} unique articles"
        
    except Exception as e:
        logger.error(f"Error deduplicating articles for {company}: {e}")
        return f"Error deduplicating articles for {company}: {e}"

@function_tool
def store_articles(company: str) -> str:
    """Store articles for a specific company."""
    try:
        # Import the working storage agent without Agents SDK
        from news_agents.storage import StorageAgent
        
        if company not in _deduplicated_news:
            return f"No deduplicated news found for {company}"
        
        storage = StorageAgent()
        articles = _deduplicated_news[company]
        result = storage.store_articles(articles, company)
        
        # Store in global state
        _storage_results[company] = result
        
        logger.info(f"Stored {result['stored_count']} articles for {company}")
        return f"Successfully stored {result['stored_count']} articles for {company}"
        
    except Exception as e:
        logger.error(f"Error storing articles for {company}: {e}")
        return f"Error storing articles for {company}: {e}"

@function_tool
def send_email_summary() -> str:
    """Send email summary of all collected news."""
    try:
        # Import the working email sender without Agents SDK
        from news_agents.email_sender import EmailSenderAgent
        
        # Collect all articles from all companies
        all_articles = []
        companies = []
        
        for company, articles in _deduplicated_news.items():
            all_articles.extend(articles)
            companies.append(company)
        
        if not all_articles:
            return "No articles to send in email summary"
        
        email_sender = EmailSenderAgent()
        success = email_sender.send_news_summary(all_articles, companies)
        
        if success:
            logger.info(f"Sent email summary with {len(all_articles)} articles")
            return f"Successfully sent email summary with {len(all_articles)} articles"
        else:
            return "Failed to send email summary"
        
    except Exception as e:
        logger.error(f"Error sending email summary: {e}")
        return f"Error sending email summary: {e}"

class FinalNewsAgentSystem:
    def __init__(self, config_path='config.yaml'):
        """Initialize the final news agent system."""
        self.config_path = config_path
        self.load_config()
        
        # Create the main system agent
        self.system_agent = self.create_system_agent()
    
    def load_config(self):
        """Load configuration from YAML file."""
        try:
            with open(self.config_path, 'r') as f:
                self.config = yaml.safe_load(f)
            self.companies = [company['name'] for company in self.config.get('companies', [])]
            logger.info(f"Loaded configuration for {len(self.companies)} companies")
        except Exception as e:
            logger.error(f"Error loading configuration: {e}")
            self.companies = []
            self.config = {}
    
    def create_system_agent(self) -> Agent:
        """Create the main system agent with function tools."""
        return Agent(
            name="Final News System Agent",
            instructions=f"""
            You are a news monitoring system agent responsible for collecting, processing, and distributing news.
            
            Companies to monitor: {', '.join(self.companies)}
            
            Your workflow:
            1. For each company, collect recent news focusing on:
               - AI-related developments
               - Stock price movements (≥5%)
               - Leadership changes
               - Major business news
            
            2. Deduplicate articles to remove duplicates
            
            3. Store unique articles in the database
            
            4. Send a consolidated email summary
            
            Use the available tools to perform each step of the workflow.
            Focus on high-impact news relevant to a Client Partner at Tiger Analytics.
            Prioritize AI news, significant stock movements, and leadership changes.
            """,
            tools=[
                collect_news_for_company,
                deduplicate_articles,
                store_articles,
                send_email_summary
            ]
        )
    
    def run_full_pipeline(self):
        """Run the complete news monitoring pipeline."""
        try:
            logger.info("🚀 Starting Final News Agent System with OpenAI Agents SDK")
            start_time = time.time()
            
            # Prepare input for the system agent
            input_text = f"""
            Run the complete news monitoring pipeline for companies: {', '.join(self.companies)}.
            
            Process each company through the full workflow:
            1. Collect recent news (focus on AI, stock movements ≥5%, leadership changes)
            2. Remove duplicates using semantic similarity
            3. Store unique articles in Pinecone
            4. Send consolidated email summary
            
            Ensure all steps are completed successfully and handle any errors gracefully.
            """
            
            # Run the system agent
            result = Runner.run_sync(self.system_agent, input_text)
            
            execution_time = time.time() - start_time
            
            logger.info(f"✅ Pipeline completed successfully in {execution_time:.2f} seconds")
            logger.info(f"Final output: {result.final_output}")
            
            return {
                'success': True,
                'execution_time': execution_time,
                'final_output': result.final_output,
                'collected_news': _collected_news,
                'deduplicated_news': _deduplicated_news,
                'storage_results': _storage_results
            }
            
        except Exception as e:
            logger.error(f"❌ Error in pipeline execution: {e}")
            return {
                'success': False,
                'error': str(e),
                'execution_time': 0
            }

def main():
    """Main entry point."""
    try:
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
        
        # Initialize system
        system = FinalNewsAgentSystem()
        
        # Run the pipeline
        results = system.run_full_pipeline()
        
        if results['success']:
            logger.info("🎉 Final News Agent System completed successfully")
            logger.info(f"⏱️ Execution time: {results['execution_time']:.2f} seconds")
            
            # Print detailed results
            if 'collected_news' in results:
                total_articles = sum(len(articles) for articles in results['collected_news'].values())
                total_unique = sum(len(articles) for articles in results['deduplicated_news'].values())
                total_stored = sum(result['stored_count'] for result in results['storage_results'].values())
                
                logger.info("📊 DETAILED RESULTS:")
                logger.info(f"  📰 Total articles collected: {total_articles}")
                logger.info(f"  🔍 Total unique articles: {total_unique}")
                logger.info(f"  💾 Total articles stored: {total_stored}")
                
                for company, articles in results['collected_news'].items():
                    unique_count = len(results['deduplicated_news'].get(company, []))
                    stored_count = results['storage_results'].get(company, {}).get('stored_count', 0)
                    logger.info(f"  🏢 {company}: {len(articles)} collected → {unique_count} unique → {stored_count} stored")
            
            return 0
        else:
            logger.error(f"❌ Final News Agent System failed: {results.get('error', 'Unknown error')}")
            return 1
            
    except Exception as e:
        logger.error(f"❌ Fatal error in main: {e}")
        return 1

if __name__ == "__main__":
    exit(main())
