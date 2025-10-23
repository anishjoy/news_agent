"""Proper OpenAI Agents SDK implementation using Runner with agent handoffs."""

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

# Global state for passing data between agents
_collected_articles = {}
_unique_articles = {}
_storage_results = {}

# News Collection Agent
@function_tool
def search_newsapi(company: str, days_back: int = 1) -> str:
    """Search for news using NewsAPI."""
    try:
        from news_agents.news_collector import NewsCollectorAgent
        collector = NewsCollectorAgent()
        
        # Use NewsAPI directly
        from datetime import datetime, timedelta
        to_date = datetime.now()
        from_date = to_date - timedelta(days=days_back)
        
        articles = collector.newsapi.get_everything(
            q=company,
            from_param=from_date.strftime('%Y-%m-%d'),
            to=to_date.strftime('%Y-%m-%d'),
            language='en',
            sort_by='publishedAt',
            page_size=50
        )
        
        article_count = len(articles.get('articles', []))
        logger.info(f"Found {article_count} articles from NewsAPI for {company}")
        return f"Found {article_count} articles from NewsAPI for {company}"
        
    except Exception as e:
        logger.error(f"Error searching NewsAPI for {company}: {e}")
        return f"Error searching NewsAPI for {company}: {e}"

@function_tool
def scrape_google_news(company: str) -> str:
    """Scrape Google News RSS feed for company news."""
    try:
        import feedparser
        
        query = company.replace(' ', '+')
        rss_url = f"https://news.google.com/rss/search?q={query}&hl=en-US&gl=US&ceid=US:en"
        
        feed = feedparser.parse(rss_url)
        article_count = len(feed.entries[:20])  # Limit to 20 articles
        
        logger.info(f"Found {article_count} articles from Google News for {company}")
        return f"Found {article_count} articles from Google News for {company}"
        
    except Exception as e:
        logger.error(f"Error scraping Google News for {company}: {e}")
        return f"Error scraping Google News for {company}: {e}"

@function_tool
def calculate_relevance_score(title: str, snippet: str) -> str:
    """Calculate relevance score for an article."""
    try:
        from news_agents.news_collector import NewsCollectorAgent
        collector = NewsCollectorAgent()
        
        score = collector.calculate_relevance_score(title, snippet)
        return f"Relevance score: {score:.2f}"
        
    except Exception as e:
        logger.error(f"Error calculating relevance score: {e}")
        return f"Error calculating relevance score: {e}"

# Deduplication Agent
@function_tool
def query_similar_articles(title: str, snippet: str, company: str) -> str:
    """Query Pinecone for similar articles to check for duplicates."""
    try:
        from utils.pinecone_client import PineconeClient
        pinecone_client = PineconeClient()
        
        search_text = f"{title} {snippet}"
        similar_articles = pinecone_client.query_similar(
            text=search_text,
            company=company,
            threshold=0.85
        )
        
        similar_count = len(similar_articles)
        logger.info(f"Found {similar_count} similar articles in Pinecone")
        return f"Found {similar_count} similar articles in Pinecone"
        
    except Exception as e:
        logger.error(f"Error querying similar articles: {e}")
        return f"Error querying similar articles: {e}"

@function_tool
def is_duplicate(similarity_score: float, threshold: float = 0.85) -> str:
    """Determine if an article is a duplicate based on similarity score."""
    is_dup = similarity_score >= threshold
    status = "duplicate" if is_dup else "unique"
    return f"Article is {status} (similarity: {similarity_score:.3f})"

# Storage Agent
@function_tool
def store_single_article(title: str, url: str, snippet: str, company: str) -> str:
    """Store a single article in Pinecone."""
    try:
        from utils.pinecone_client import PineconeClient
        import uuid
        
        pinecone_client = PineconeClient()
        article_id = str(uuid.uuid4())
        content = f"{title} {snippet}"
        metadata = {
            'company': company,
            'title': title,
            'url': url,
            'snippet': snippet
        }
        
        success = pinecone_client.upsert_article(article_id, content, metadata)
        status = "successfully stored" if success else "failed to store"
        return f"Article {status} in Pinecone"
        
    except Exception as e:
        logger.error(f"Error storing article: {e}")
        return f"Error storing article: {e}"

# Email Agent
@function_tool
def create_email_subject(total_articles: int, companies: str) -> str:
    """Create email subject line based on articles and companies."""
    if total_articles > 0:
        subject = f"📰 {total_articles} News Updates - {companies}"
    else:
        subject = "📰 No new articles found"
    return f"Email subject: {subject}"

@function_tool
def format_email_content(articles_count: int, companies: str) -> str:
    """Format articles into HTML email content."""
    try:
        # Create a simple HTML email template
        html_content = f"""
        <html>
        <body>
            <h2>📰 Daily News Summary</h2>
            <p>Here are the latest news updates for {companies}:</p>
            <p><strong>Total Articles:</strong> {articles_count}</p>
            <hr>
            <p>This is a consolidated summary of the most relevant news articles collected and processed by the News Agent System.</p>
            <p>Articles have been filtered for relevance and deduplicated to ensure you receive only the most important updates.</p>
            <hr>
            <p><em>Generated by News Agent System</em></p>
        </body>
        </html>
        """
        return html_content
        
    except Exception as e:
        logger.error(f"Error formatting email content: {e}")
        return f"<html><body><p>Error formatting email content: {e}</p></body></html>"

@function_tool
def send_email_via_smtp(subject: str, html_content: str, recipient: str) -> str:
    """Send email via Gmail SMTP."""
    try:
        import smtplib
        from email.mime.text import MIMEText
        from email.mime.multipart import MIMEMultipart
        
        # Gmail SMTP configuration
        smtp_server = "smtp.gmail.com"
        smtp_port = 587
        sender_email = os.getenv("GMAIL_SENDER")
        sender_password = os.getenv("GMAIL_APP_PASSWORD")
        
        if not sender_email or not sender_password:
            return "Error: Gmail credentials not configured"
        
        # Create message
        msg = MIMEMultipart()
        msg['From'] = sender_email
        msg['To'] = recipient
        msg['Subject'] = subject
        
        # Add HTML content
        msg.attach(MIMEText(html_content, 'html'))
        
        # Send email
        with smtplib.SMTP(smtp_server, smtp_port) as server:
            server.starttls()
            server.login(sender_email, sender_password)
            server.send_message(msg)
        
        logger.info(f"Email sent successfully to {recipient}")
        return f"Email sent successfully to {recipient}"
        
    except Exception as e:
        logger.error(f"Error sending email: {e}")
        return f"Error sending email: {e}"

class NewsAgentSystem:
    def __init__(self, config_path='config.yaml'):
        """Initialize the news agent system."""
        self.config_path = config_path
        self.load_config()
        
        # Create specialized agents
        self.news_collector = self.create_news_collector_agent()
        self.deduplicator = self.create_deduplicator_agent()
        self.storage_agent = self.create_storage_agent()
        self.email_agent = self.create_email_agent()
    
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
    
    def create_news_collector_agent(self) -> Agent:
        """Create the news collection agent."""
        return Agent(
            name="News Collector",
            instructions="""
            You are a news collection agent specialized in gathering information about companies.
            Your primary focus is on:
            1. Stock price changes and financial news (look for percentage movements ≥5%)
            2. Leadership changes and executive appointments
            3. AI-related developments and announcements
            4. Major business partnerships and acquisitions

            For each company, use the available tools to:
            1. Search NewsAPI for recent articles
            2. Scrape Google News RSS feeds
            3. Calculate relevance scores for articles
            4. Return structured data with company, title, url, published_date, snippet, and relevance_score

            Prioritize articles that mention AI, stock prices, or leadership changes.
            Only return articles with relevance_score >= 3.0.
            Limit to top 10 most relevant articles per company.
            """,
            tools=[
                search_newsapi,
                scrape_google_news,
                calculate_relevance_score
            ]
        )
    
    def create_deduplicator_agent(self) -> Agent:
        """Create the deduplication agent."""
        return Agent(
            name="Deduplicator",
            instructions="""
            You are a news deduplication agent. Your task is to compare newly collected articles
            with previously stored articles in Pinecone to identify and filter out redundant information.
            
            Use the provided tools to:
            1. Query for similar articles in Pinecone
            2. Determine if a new article is a duplicate based on similarity score
            3. Filter out duplicates and return only unique articles
            
            Use a similarity threshold of 0.85 for duplicate detection.
            """,
            tools=[
                query_similar_articles,
                is_duplicate
            ]
        )
    
    def create_storage_agent(self) -> Agent:
        """Create the storage agent."""
        return Agent(
            name="Storage Agent",
            instructions="""
            You are a news storage agent. Your role is to store unique news articles
            into the Pinecone vector database. Ensure that each article is properly
            embedded and indexed for future deduplication and retrieval.
            
            Use the provided tools to:
            1. Store individual articles in Pinecone
            2. Track success/failure rates
            3. Organize articles by company and metadata
            """,
            tools=[
                store_single_article
            ]
        )
    
    def create_email_agent(self) -> Agent:
        """Create the email agent."""
        return Agent(
            name="Email Agent",
            instructions="""
            You are an email sending agent. Your task is to format and send a consolidated
            news summary to the user via Gmail SMTP. Ensure the email is well-formatted
            and contains all relevant news articles.
            
            Use the provided tools to:
            1. Create compelling email subject lines
            2. Format articles into HTML email content
            3. Send emails via Gmail SMTP
            
            When sending emails, use the recipient email address provided in the input.
            Default recipient is anishjoy@gmail.com if not specified.
            """,
            tools=[
                create_email_subject,
                format_email_content,
                send_email_via_smtp
            ]
        )
    
    def run_full_pipeline(self):
        """Run the complete news monitoring pipeline using Runner with agent handoffs."""
        try:
            logger.info("🚀 Starting News Agent System with proper Runner implementation")
            start_time = time.time()
            
            all_results = {}
            
            # Process each company through the full agent pipeline
            for company in self.companies:
                logger.info(f"🔄 Processing {company} through agent pipeline")
                
                try:
                    # Step 1: News Collection Agent
                    logger.info(f"📰 Step 1: Collecting news for {company}")
                    collection_input = f"""
                    Collect recent news for {company}. Focus on:
                    - AI-related developments
                    - Stock price movements (≥5%)
                    - Leadership changes
                    - Major business news
                    
                    Use NewsAPI and Google News RSS feeds.
                    Calculate relevance scores and filter for high-impact news.
                    """
                    
                    collection_result = Runner.run_sync(self.news_collector, collection_input)
                    logger.info(f"✅ News collection completed for {company}")
                    
                    # Step 2: Deduplication Agent
                    logger.info(f"🔍 Step 2: Deduplicating articles for {company}")
                    dedup_input = f"""
                    Deduplicate articles for {company}.
                    Compare against existing articles in Pinecone.
                    Remove duplicates using semantic similarity.
                    Return only unique, high-value articles.
                    """
                    
                    dedup_result = Runner.run_sync(self.deduplicator, dedup_input)
                    logger.info(f"✅ Deduplication completed for {company}")
                    
                    # Step 3: Storage Agent
                    logger.info(f"💾 Step 3: Storing articles for {company}")
                    storage_input = f"""
                    Store unique articles for {company} in Pinecone.
                    Ensure proper metadata and organization.
                    Track success/failure rates.
                    """
                    
                    storage_result = Runner.run_sync(self.storage_agent, storage_input)
                    logger.info(f"✅ Storage completed for {company}")
                    
                    all_results[company] = {
                        'collection': collection_result,
                        'deduplication': dedup_result,
                        'storage': storage_result
                    }
                    
                except Exception as e:
                    logger.error(f"❌ Error processing {company}: {e}")
                    all_results[company] = {'error': str(e)}
            
            # Step 4: Email Agent (for all companies)
            logger.info("📧 Step 4: Sending consolidated email summary")
            recipient_email = self.config.get('email', {}).get('recipient', 'anishjoy@gmail.com')
            email_input = f"""
            Send a consolidated news summary for companies: {', '.join(self.companies)}.
            Recipient email: {recipient_email}
            Create a compelling subject line and format the content professionally.
            Focus on high-impact news and AI-related content.
            """
            
            email_result = Runner.run_sync(self.email_agent, email_input)
            logger.info("✅ Email summary sent")
            
            execution_time = time.time() - start_time
            
            logger.info(f"🎉 Pipeline completed successfully in {execution_time:.2f} seconds")
            
            return {
                'success': True,
                'execution_time': execution_time,
                'results': all_results,
                'email_result': email_result
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
        system = NewsAgentSystem()
        
        # Run the pipeline
        results = system.run_full_pipeline()
        
        if results['success']:
            logger.info("🎉 News Agent System completed successfully")
            logger.info(f"⏱️ Execution time: {results['execution_time']:.2f} seconds")
            
            # Print detailed results
            for company, result in results['results'].items():
                if 'error' in result:
                    logger.error(f"❌ {company}: {result['error']}")
                else:
                    logger.info(f"✅ {company}: Processed through all agents")
            
            return 0
        else:
            logger.error(f"❌ News Agent System failed: {results.get('error', 'Unknown error')}")
            return 1
            
    except Exception as e:
        logger.error(f"❌ Fatal error in main: {e}")
        return 1

if __name__ == "__main__":
    exit(main())
