"""Main orchestration using OpenAI Agents SDK with proper handoffs."""

import os
import yaml
import asyncio
from typing import List, Dict, Any
from agents import Agent, Runner
from utils.logger import setup_logger

logger = setup_logger(__name__)

class NewsAgentOrchestrator:
    def __init__(self, config_path='config.yaml'):
        """Initialize the news agent orchestrator."""
        self.config_path = config_path
        self.load_config()
        
        # Create the main orchestration agent
        self.orchestrator_agent = self.create_orchestrator_agent()
    
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
    
    def create_orchestrator_agent(self) -> Agent:
        """Create the main orchestration agent."""
        return Agent(
            name="News Orchestrator",
            instructions=f"""
            You are the main orchestration agent for a multi-agent news monitoring system.
            Your role is to coordinate the workflow for news collection and processing.
            
            Companies to monitor: {', '.join(self.companies)}
            
            Your workflow:
            1. Collect news for each company focusing on:
               - AI-related developments
               - Stock price movements (≥5%)
               - Leadership changes
               - Major business news
            
            2. Process and deduplicate articles
            
            3. Store unique articles in database
            
            4. Send consolidated email summary
            
            Focus on high-impact news that would be relevant to a Client Partner at Tiger Analytics.
            Prioritize AI news, significant stock movements, and leadership changes.
            """
        )
    
    def run_full_pipeline(self):
        """Run the complete news monitoring pipeline using Agents SDK."""
        try:
            logger.info("Starting News Agent System with OpenAI Agents SDK")
            start_time = asyncio.get_event_loop().time()
            
            # Prepare input for the orchestrator
            input_text = f"""
            Run the complete news monitoring pipeline for companies: {', '.join(self.companies)}.
            
            Process each company through the full workflow:
            1. Collect recent news (focus on AI, stock movements ≥5%, leadership changes)
            2. Remove duplicates using semantic similarity
            3. Store unique articles in Pinecone
            4. Send consolidated email summary
            
            Ensure all agents work together efficiently and handle errors gracefully.
            """
            
            # Run the orchestrator agent
            result = Runner.run_sync(self.orchestrator_agent, input_text)
            
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
        
        # Initialize orchestrator
        orchestrator = NewsAgentOrchestrator()
        
        # Run the pipeline
        results = orchestrator.run_full_pipeline()
        
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