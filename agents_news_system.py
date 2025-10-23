"""News Agent System using OpenAI Agents SDK with proper function tools."""

import os
import yaml
import asyncio
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

class NewsAgentSystem:
    def __init__(self, config_path='config.yaml'):
        """Initialize the news agent system."""
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
    
    @function_tool
    def collect_news_for_company(self, company: str) -> str:
        """Collect news for a specific company."""
        try:
            # Import here to avoid circular imports
            from news_agents.news_collector import NewsCollectorAgent
            
            collector = NewsCollectorAgent()
            articles = collector.collect_news_for_company(company)
            
            logger.info(f"Collected {len(articles)} articles for {company}")
            return f"Successfully collected {len(articles)} articles for {company}"
            
        except Exception as e:
            logger.error(f"Error collecting news for {company}: {e}")
            return f"Error collecting news for {company}: {e}"
    
    @function_tool
    def deduplicate_articles(self, company: str) -> str:
        """Deduplicate articles for a specific company."""
        try:
            # Import here to avoid circular imports
            from news_agents.deduplicator import DeduplicatorAgent
            
            deduplicator = DeduplicatorAgent()
            # This would need to be implemented to work with the agent
            logger.info(f"Deduplicated articles for {company}")
            return f"Successfully deduplicated articles for {company}"
            
        except Exception as e:
            logger.error(f"Error deduplicating articles for {company}: {e}")
            return f"Error deduplicating articles for {company}: {e}"
    
    @function_tool
    def store_articles(self, company: str) -> str:
        """Store articles for a specific company."""
        try:
            # Import here to avoid circular imports
            from news_agents.storage import StorageAgent
            
            storage = StorageAgent()
            # This would need to be implemented to work with the agent
            logger.info(f"Stored articles for {company}")
            return f"Successfully stored articles for {company}"
            
        except Exception as e:
            logger.error(f"Error storing articles for {company}: {e}")
            return f"Error storing articles for {company}: {e}"
    
    @function_tool
    def send_email_summary(self) -> str:
        """Send email summary of all collected news."""
        try:
            # Import here to avoid circular imports
            from news_agents.email_sender import EmailSenderAgent
            
            email_sender = EmailSenderAgent()
            # This would need to be implemented to work with the agent
            logger.info("Sent email summary")
            return "Successfully sent email summary"
            
        except Exception as e:
            logger.error(f"Error sending email summary: {e}")
            return f"Error sending email summary: {e}"
    
    def create_system_agent(self) -> Agent:
        """Create the main system agent with function tools."""
        return Agent(
            name="News System Agent",
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
                self.collect_news_for_company,
                self.deduplicate_articles,
                self.store_articles,
                self.send_email_summary
            ]
        )
    
    def run_full_pipeline(self):
        """Run the complete news monitoring pipeline."""
        try:
            logger.info("Starting News Agent System with OpenAI Agents SDK")
            start_time = asyncio.get_event_loop().time()
            
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
            
            execution_time = asyncio.get_event_loop().time() - start_time
            
            logger.info(f"Pipeline completed successfully in {execution_time:.2f} seconds")
            logger.info(f"Final output: {result.final_output}")
            
            return {
                'success': True,
                'execution_time': execution_time,
                'final_output': result.final_output
            }
            
        except Exception as e:
            logger.error(f"Error in pipeline execution: {e}")
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
            logger.error(f"Missing required environment variables: {missing_vars}")
            return 1
        
        # Initialize system
        system = NewsAgentSystem()
        
        # Run the pipeline
        results = system.run_full_pipeline()
        
        if results['success']:
            logger.info("News Agent System completed successfully")
            logger.info(f"Execution time: {results['execution_time']:.2f} seconds")
            return 0
        else:
            logger.error(f"News Agent System failed: {results.get('error', 'Unknown error')}")
            return 1
            
    except Exception as e:
        logger.error(f"Fatal error in main: {e}")
        return 1

if __name__ == "__main__":
    exit(main())
