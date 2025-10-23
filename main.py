"""Main orchestration layer for the multi-agent news monitoring system."""

import os
import yaml
import asyncio
from datetime import datetime
from typing import List, Dict, Any
from dotenv import load_dotenv

from news_agents.news_collector import NewsCollectorAgent
from news_agents.deduplicator import DeduplicatorAgent
from news_agents.storage import StorageAgent
from news_agents.email_sender import EmailSenderAgent
from utils.logger import setup_logger

# Load environment variables
load_dotenv()

logger = setup_logger(__name__)

class NewsAgentOrchestrator:
    def __init__(self):
        """Initialize the news agent orchestrator."""
        self.news_collector = NewsCollectorAgent()
        self.deduplicator = DeduplicatorAgent()
        self.storage_agent = StorageAgent()
        self.email_sender = EmailSenderAgent()
        
        # Load configuration
        with open('config.yaml', 'r') as f:
            self.config = yaml.safe_load(f)
        
        self.companies = [company['name'] for company in self.config.get('companies', [])]
        logger.info(f"Initialized orchestrator for companies: {self.companies}")
    
    def validate_environment(self) -> bool:
        """Validate that all required environment variables are set."""
        required_vars = [
            'OPENAI_API_KEY',
            'PINECONE_API_KEY',
            'NEWS_API_KEY',
            'GMAIL_SENDER',
            'GMAIL_APP_PASSWORD'
        ]
        
        missing_vars = []
        for var in required_vars:
            if not os.getenv(var):
                missing_vars.append(var)
        
        if missing_vars:
            logger.error(f"Missing environment variables: {missing_vars}")
            return False
        
        logger.info("Environment validation passed")
        return True
    
    def collect_news_for_all_companies(self) -> Dict[str, List[Dict[str, Any]]]:
        """Collect news for all configured companies."""
        all_news = {}
        
        for company in self.companies:
            logger.info(f"Collecting news for {company}")
            try:
                articles = self.news_collector.collect_news_for_company(company)
                all_news[company] = articles
                logger.info(f"Collected {len(articles)} articles for {company}")
            except Exception as e:
                logger.error(f"Error collecting news for {company}: {e}")
                all_news[company] = []
        
        total_articles = sum(len(articles) for articles in all_news.values())
        logger.info(f"Total articles collected: {total_articles}")
        return all_news
    
    def deduplicate_news(self, all_news: Dict[str, List[Dict[str, Any]]]) -> Dict[str, List[Dict[str, Any]]]:
        """Deduplicate news for all companies."""
        deduplicated_news = {}
        
        for company, articles in all_news.items():
            if not articles:
                deduplicated_news[company] = []
                continue
            
            logger.info(f"Deduplicating {len(articles)} articles for {company}")
            try:
                unique_articles = self.deduplicator.deduplicate_articles(articles, company)
                deduplicated_news[company] = unique_articles
                logger.info(f"Deduplicated to {len(unique_articles)} unique articles for {company}")
            except Exception as e:
                logger.error(f"Error deduplicating articles for {company}: {e}")
                deduplicated_news[company] = articles  # Keep original if deduplication fails
        
        return deduplicated_news
    
    def store_news(self, deduplicated_news: Dict[str, List[Dict[str, Any]]]) -> Dict[str, Dict[str, Any]]:
        """Store deduplicated news in Pinecone."""
        storage_results = {}
        
        for company, articles in deduplicated_news.items():
            if not articles:
                storage_results[company] = {
                    'total_articles': 0,
                    'stored_count': 0,
                    'failed_count': 0,
                    'success_rate': 1.0
                }
                continue
            
            logger.info(f"Storing {len(articles)} articles for {company}")
            try:
                result = self.storage_agent.store_articles(articles, company)
                storage_results[company] = result
                logger.info(f"Storage result for {company}: {result}")
            except Exception as e:
                logger.error(f"Error storing articles for {company}: {e}")
                storage_results[company] = {
                    'total_articles': len(articles),
                    'stored_count': 0,
                    'failed_count': len(articles),
                    'success_rate': 0.0
                }
        
        return storage_results
    
    def send_email_summary(self, deduplicated_news: Dict[str, List[Dict[str, Any]]]) -> bool:
        """Send email summary of all news."""
        try:
            # Flatten all articles
            all_articles = []
            for company, articles in deduplicated_news.items():
                all_articles.extend(articles)
            
            if not all_articles:
                logger.info("No articles to send in email summary")
                return True
            
            logger.info(f"Sending email summary with {len(all_articles)} articles")
            success = self.email_sender.send_news_summary(all_articles, self.companies)
            
            if success:
                logger.info("Email summary sent successfully")
            else:
                logger.error("Failed to send email summary")
            
            return success
            
        except Exception as e:
            logger.error(f"Error sending email summary: {e}")
            return False
    
    def run_full_pipeline(self) -> Dict[str, Any]:
        """Run the complete news monitoring pipeline."""
        start_time = datetime.now()
        logger.info("Starting news monitoring pipeline")
        
        # Validate environment
        if not self.validate_environment():
            return {
                'success': False,
                'error': 'Environment validation failed',
                'execution_time': 0
            }
        
        try:
            # Step 1: Collect news
            logger.info("Step 1: Collecting news")
            all_news = self.collect_news_for_all_companies()
            
            # Step 2: Deduplicate
            logger.info("Step 2: Deduplicating news")
            deduplicated_news = self.deduplicate_news(all_news)
            
            # Step 3: Store in Pinecone
            logger.info("Step 3: Storing news in Pinecone")
            storage_results = self.store_news(deduplicated_news)
            
            # Step 4: Send email summary
            logger.info("Step 4: Sending email summary")
            email_success = self.send_email_summary(deduplicated_news)
            
            # Calculate execution time
            execution_time = (datetime.now() - start_time).total_seconds()
            
            # Prepare results
            total_articles_collected = sum(len(articles) for articles in all_news.values())
            total_articles_deduplicated = sum(len(articles) for articles in deduplicated_news.values())
            total_articles_stored = sum(result['stored_count'] for result in storage_results.values())
            
            results = {
                'success': True,
                'execution_time': execution_time,
                'companies_processed': len(self.companies),
                'total_articles_collected': total_articles_collected,
                'total_articles_deduplicated': total_articles_deduplicated,
                'total_articles_stored': total_articles_stored,
                'email_sent': email_success,
                'storage_results': storage_results,
                'companies_news': {
                    company: len(articles) for company, articles in deduplicated_news.items()
                }
            }
            
            logger.info(f"Pipeline completed successfully in {execution_time:.2f} seconds")
            logger.info(f"Results: {results}")
            
            return results
            
        except Exception as e:
            execution_time = (datetime.now() - start_time).total_seconds()
            logger.error(f"Pipeline failed: {e}")
            return {
                'success': False,
                'error': str(e),
                'execution_time': execution_time
            }

def main():
    """Main entry point for the news agent system."""
    logger.info("Starting News Agent System")
    
    # Create orchestrator
    orchestrator = NewsAgentOrchestrator()
    
    # Run the pipeline
    results = orchestrator.run_full_pipeline()
    
    # Log results
    if results['success']:
        logger.info("News Agent System completed successfully")
        logger.info(f"Execution time: {results['execution_time']:.2f} seconds")
        logger.info(f"Articles processed: {results['total_articles_collected']}")
        logger.info(f"Unique articles: {results['total_articles_deduplicated']}")
        logger.info(f"Articles stored: {results['total_articles_stored']}")
        logger.info(f"Email sent: {results['email_sent']}")
    else:
        logger.error(f"News Agent System failed: {results['error']}")
        return 1
    
    return 0

if __name__ == "__main__":
    exit(main())

