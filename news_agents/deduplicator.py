"""Deduplication Agent using OpenAI Agents SDK."""

import os
from typing import List, Dict, Any
from agents import Agent, Runner, function_tool
from utils.pinecone_client import PineconeClient
from utils.logger import setup_logger

logger = setup_logger(__name__)

class DeduplicatorAgent:
    def __init__(self):
        self.pinecone_client = PineconeClient()
    
    @function_tool
    def query_similar_articles(self, title: str, snippet: str, company: str, threshold: float = 0.85) -> str:
        """Query Pinecone for similar articles to check for duplicates."""
        try:
            # Create search text from article content
            search_text = f"{title} {snippet}"
            
            # Query Pinecone for similar articles
            similar_articles = self.pinecone_client.query_similar(
                text=search_text,
                company=company,
                threshold=threshold
            )
            
            logger.info(f"Found {len(similar_articles)} similar articles for {title}")
            return f"Found {len(similar_articles)} similar articles for {title}"
            
        except Exception as e:
            logger.error(f"Error querying similar articles: {e}")
            return f"Error querying similar articles: {e}"
    
    @function_tool
    def is_duplicate(self, title: str, similarity_score: float, threshold: float = 0.85) -> bool:
        """Determine if an article is a duplicate based on similarity score."""
        try:
            if similarity_score >= threshold:
                logger.info(f"Article '{title}' is duplicate with score {similarity_score}")
                return True
            
            return False
            
        except Exception as e:
            logger.error(f"Error checking for duplicates: {e}")
            return False
    
    def create_agent(self) -> Agent:
        """Create the deduplication agent using OpenAI Agents SDK."""
        return Agent(
            name="Deduplicator",
            instructions="""
            You are a deduplication agent specialized in identifying and removing duplicate news articles.
            Your primary responsibilities are:
            1. Query Pinecone vector database for similar articles
            2. Compare similarity scores to identify duplicates
            3. Filter out duplicate articles while keeping unique ones
            4. Ensure only truly new information is passed forward
            
            For each article, use the available tools to:
            1. Query for similar articles in the database
            2. Check if the article is a duplicate based on similarity scores
            3. Return only unique articles
            
            Use a similarity threshold of 0.85 for duplicate detection.
            Focus on semantic similarity rather than exact text matches.
            """,
            tools=[
                self.query_similar_articles,
                self.is_duplicate
            ]
        )
    
    def filter_unique_articles(self, articles: List[Dict[str, Any]], company: str) -> List[Dict[str, Any]]:
        """Filter out duplicate articles using direct Pinecone calls."""
        try:
            unique_articles = []
            
            for article in articles:
                # Query for similar articles in Pinecone directly
                try:
                    search_text = f"{article.get('title', '')} {article.get('snippet', '')}"
                    similar_articles = self.pinecone_client.query_similar(
                        text=search_text,
                        company=company,
                        threshold=0.85
                    )
                    
                    # Check if this article is a duplicate
                    is_dup = False
                    for similar in similar_articles:
                        similarity_score = similar.get('score', 0.0)
                        if similarity_score >= 0.85:
                            is_dup = True
                            logger.info(f"Article '{article.get('title', '')}' is duplicate with score {similarity_score}")
                            break
                    
                    if not is_dup:
                        unique_articles.append(article)
                        logger.info(f"Article '{article.get('title', '')}' is unique")
                    else:
                        logger.info(f"Article '{article.get('title', '')}' is duplicate, skipping")
                        
                except Exception as e:
                    logger.error(f"Error checking article for duplicates: {e}")
                    # If we can't check, assume it's unique
                    unique_articles.append(article)
            
            logger.info(f"Filtered {len(articles)} articles to {len(unique_articles)} unique articles")
            return unique_articles
            
        except Exception as e:
            logger.error(f"Error filtering unique articles: {e}")
            return articles  # Return original list if error
    
    def deduplicate_articles(self, articles: List[Dict[str, Any]], company: str) -> List[Dict[str, Any]]:
        """Deduplicate articles for a specific company."""
        try:
            unique_articles = self.filter_unique_articles(articles, company)
            logger.info(f"Deduplicated {len(articles)} articles to {len(unique_articles)} unique articles for {company}")
            return unique_articles
            
        except Exception as e:
            logger.error(f"Error deduplicating articles for {company}: {e}")
            return articles  # Return original list if error