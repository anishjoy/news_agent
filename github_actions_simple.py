#!/usr/bin/env python3
"""
GitHub Actions Simple News Agent - Fallback version without Agents SDK
This version uses direct API calls to avoid potential SDK connection issues.
"""

import os
import yaml
import time
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import List, Dict, Any
from utils.logger import setup_logger
from news_agents.news_collector import NewsCollectorAgent
from news_agents.deduplicator import DeduplicatorAgent
from news_agents.storage import StorageAgent
from utils.email_formatter import EmailFormatter
from dotenv import load_dotenv

# Load environment variables
try:
    load_dotenv()
except ImportError:
    pass

logger = setup_logger(__name__)

class SimpleNewsAgentSystem:
    """Simple news agent system without Agents SDK for GitHub Actions."""
    
    def __init__(self, config_path='config.yaml'):
        self.config_path = config_path
        self.companies = []
        self.config = {}
        self._load_config()
        
        # Initialize agents
        self.news_collector = NewsCollectorAgent()
        self.deduplicator = DeduplicatorAgent()
        self.storage = StorageAgent()
        
        # Initialize email formatter with priorities
        priorities = self.config.get('priorities', [
            'AI', 'Artificial Intelligence', 'Machine Learning',
            'leadership change', 'CEO', 'executive', 'stock price',
            'earnings', 'partnership', 'acquisition', 'merger'
        ])
        self.email_formatter = EmailFormatter(priorities)
        
        # Email configuration
        self.sender_email = os.getenv("GMAIL_SENDER")
        self.sender_password = os.getenv("GMAIL_APP_PASSWORD")
        self.recipient_email = self.config.get('email', {}).get('recipient', 'anishjoy@gmail.com')
    
    def _load_config(self):
        """Load configuration from YAML file."""
        try:
            with open(self.config_path, 'r') as f:
                self.config = yaml.safe_load(f)
            self.companies = [c['name'] for c in self.config.get('companies', [])]
            logger.info(f"Loaded configuration for {len(self.companies)} companies")
        except Exception as e:
            logger.error(f"Error loading configuration: {e}")
            self.companies = []
            self.config = {}
    
    def test_connections(self):
        """Test API connections before running the main pipeline."""
        try:
            logger.info("🔍 Testing API connections...")
            
            # Test OpenAI connection
            try:
                from openai import OpenAI
                client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
                response = client.chat.completions.create(
                    model="gpt-3.5-turbo",
                    messages=[{"role": "user", "content": "Test"}],
                    max_tokens=5
                )
                logger.info("✅ OpenAI connection successful")
            except Exception as e:
                logger.error(f"❌ OpenAI connection failed: {e}")
                return False
            
            # Test NewsAPI connection
            try:
                from newsapi import NewsApiClient
                newsapi = NewsApiClient(api_key=os.getenv("NEWS_API_KEY"))
                response = newsapi.get_everything(q="test", page_size=1)
                logger.info("✅ NewsAPI connection successful")
            except Exception as e:
                logger.error(f"❌ NewsAPI connection failed: {e}")
                return False
            
            # Test Pinecone connection
            try:
                from utils.pinecone_client import PineconeClient
                pc = PineconeClient()
                # Test with a simple query
                test_results = pc.query_similar("test", "test_company", top_k=1)
                logger.info("✅ Pinecone connection successful")
            except Exception as e:
                logger.error(f"❌ Pinecone connection failed: {e}")
                return False
            
            logger.info("✅ All API connections successful")
            return True
            
        except Exception as e:
            logger.error(f"❌ Connection test failed: {e}")
            return False
    
    def collect_news_for_company(self, company: str) -> List[Dict[str, Any]]:
        """Collect news for a specific company."""
        try:
            logger.info(f"📰 Collecting news for {company}")
            articles = self.news_collector.collect_news_for_company(company)
            logger.info(f"✅ Collected {len(articles)} articles for {company}")
            return articles
        except Exception as e:
            logger.error(f"❌ Error collecting news for {company}: {e}")
            return []
    
    def deduplicate_articles(self, articles: List[Dict[str, Any]], company: str) -> List[Dict[str, Any]]:
        """Deduplicate articles for a company."""
        try:
            logger.info(f"🔍 Deduplicating {len(articles)} articles for {company}")
            unique_articles = self.deduplicator.deduplicate_articles(articles, company)
            logger.info(f"✅ Found {len(unique_articles)} unique articles for {company}")
            return unique_articles
        except Exception as e:
            logger.error(f"❌ Error deduplicating articles for {company}: {e}")
            return articles  # Return original articles if deduplication fails
    
    def store_articles(self, articles: List[Dict[str, Any]], company: str) -> Dict[str, Any]:
        """Store articles in Pinecone."""
        try:
            logger.info(f"💾 Storing {len(articles)} articles for {company}")
            result = self.storage.store_articles(articles, company)
            logger.info(f"✅ Stored {result['stored_count']} articles for {company}")
            return result
        except Exception as e:
            logger.error(f"❌ Error storing articles for {company}: {e}")
            return {'stored_count': 0, 'failed_count': len(articles)}
    
    def send_email_summary(self, all_articles: List[Dict[str, Any]]) -> bool:
        """Send email summary of all articles."""
        try:
            if not all_articles:
                logger.info("📧 No articles to send in email summary")
                return True
            
            logger.info(f"📧 Sending email summary with {len(all_articles)} articles")
            
            # Create email subject
            total_articles = len(all_articles)
            high_priority_count = len([a for a in all_articles if a.get('relevance_score', 0) >= 5.0])
            
            if high_priority_count > 0:
                subject = f"🔥 {total_articles} High-Priority News Updates"
            else:
                subject = f"📰 {total_articles} News Updates"
            
            # Format email content
            html_content = self.email_formatter.format_email_html(all_articles, self.companies)
            
            # Send email
            msg = MIMEMultipart()
            msg['From'] = self.sender_email
            msg['To'] = self.recipient_email
            msg['Subject'] = subject
            
            msg.attach(MIMEText(html_content, 'html'))
            
            with smtplib.SMTP("smtp.gmail.com", 587) as server:
                server.starttls()
                server.login(self.sender_email, self.sender_password)
                server.send_message(msg)
            
            logger.info(f"✅ Email sent successfully to {self.recipient_email}")
            return True
            
        except Exception as e:
            logger.error(f"❌ Error sending email: {e}")
            return False
    
    def run_full_pipeline(self):
        """Run the complete news monitoring pipeline."""
        try:
            logger.info("🚀 Starting Simple News Agent System (No Agents SDK)")
            start_time = time.time()
            
            all_articles = []
            successful_companies = 0
            
            # Process each company
            for company in self.companies:
                logger.info(f"🔄 Processing {company}")
                
                try:
                    # Step 1: Collect news
                    articles = self.collect_news_for_company(company)
                    
                    if articles:
                        # Step 2: Deduplicate
                        unique_articles = self.deduplicate_articles(articles, company)
                        
                        if unique_articles:
                            # Step 3: Store
                            storage_result = self.store_articles(unique_articles, company)
                            
                            # Add to all articles for email
                            all_articles.extend(unique_articles)
                            successful_companies += 1
                            
                            logger.info(f"✅ Successfully processed {company}")
                        else:
                            logger.info(f"ℹ️ No unique articles found for {company}")
                    else:
                        logger.info(f"ℹ️ No articles found for {company}")
                        
                except Exception as e:
                    logger.error(f"❌ Error processing {company}: {e}")
            
            # Step 4: Send email summary
            if all_articles:
                self.send_email_summary(all_articles)
            else:
                logger.info("📧 No articles to send in email summary")
            
            execution_time = time.time() - start_time
            
            if successful_companies > 0:
                logger.info(f"🎉 Pipeline completed with {successful_companies} companies processed in {execution_time:.2f} seconds")
                return {
                    'success': True,
                    'execution_time': execution_time,
                    'successful_companies': successful_companies,
                    'total_articles': len(all_articles)
                }
            else:
                logger.error("❌ Pipeline failed - no companies processed successfully")
                return {
                    'success': False,
                    'error': 'All companies failed to process',
                    'execution_time': execution_time,
                    'successful_companies': 0
                }
            
        except Exception as e:
            logger.error(f"❌ Error in pipeline execution: {e}")
            return {
                'success': False,
                'error': str(e),
                'execution_time': 0,
                'successful_companies': 0
            }

def main():
    """Main entry point for GitHub Actions."""
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
        
        # Test connections first
        system = SimpleNewsAgentSystem()
        if not system.test_connections():
            logger.error("❌ Connection tests failed - aborting pipeline")
            return 1
        
        # Run the pipeline
        results = system.run_full_pipeline()
        
        if results['success']:
            logger.info("🎉 Simple News Agent System completed successfully")
            logger.info(f"⏱️ Execution time: {results['execution_time']:.2f} seconds")
            logger.info(f"📊 Successful companies: {results.get('successful_companies', 0)}")
            logger.info(f"📰 Total articles: {results.get('total_articles', 0)}")
            return 0
        else:
            logger.error(f"❌ Simple News Agent System failed: {results.get('error', 'Unknown error')}")
            return 1
            
    except Exception as e:
        logger.error(f"❌ Simple News Agent System failed: {e}")
        return 1

if __name__ == "__main__":
    exit(main())
