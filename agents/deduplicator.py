"""Deduplication Agent using OpenAI Agents SDK and Pinecone."""

import os
from typing import List, Dict, Any
from agents import Agent, function_tool
from utils.pinecone_client import PineconeClient
from utils.logger import setup_logger

logger = setup_logger(__name__)

class DeduplicatorAgent:
    def __init__(self):
        self.pinecone_client = PineconeClient()
    
    @function_tool
    def query_similar_articles(self, article: Dict[str, Any], company: str, threshold: float = 0.85) -> List[Dict[str, Any]]:
        """Query Pinecone for similar articles to check for duplicates."""
        try:
            # Create search text from article content
            search_text = f"{article.get('title', '')} {article.get('snippet', '')}"
            
            # Query Pinecone for similar articles
            similar_articles = self.pinecone_client.query_similar(
                text=search_text,
                company=company,
                threshold=threshold
            )
            
            logger.info(f"Found {len(similar_articles)} similar articles for {article.get('title', '')}")
            return similar_articles
            
        except Exception as e:
            logger.error(f"Error querying similar articles: {e}")
            return []
    
    @function_tool
    def calculate_similarity_score(self, article1: Dict[str, Any], article2: Dict[str, Any]) -> float:
        """Calculate similarity score between two articles."""
        try:
            # Simple text similarity based on title and snippet
            title1 = article1.get('title', '').lower()
            title2 = article2.get('title', '').lower()
            snippet1 = article1.get('snippet', '').lower()
            snippet2 = article2.get('snippet', '').lower()
            
            # Calculate Jaccard similarity
            words1 = set(title1.split() + snippet1.split())
            words2 = set(title2.split() + snippet2.split())
            
            if not words1 or not words2:
                return 0.0
            
            intersection = len(words1.intersection(words2))
            union = len(words1.union(words2))
            
            jaccard_score = intersection / union if union > 0 else 0.0
            
            # Boost score if titles are very similar
            if title1 and title2:
                title_words1 = set(title1.split())
                title_words2 = set(title2.split())
                title_intersection = len(title_words1.intersection(title_words2))
                title_union = len(title_words1.union(title_words2))
                title_similarity = title_intersection / title_union if title_union > 0 else 0.0
                
                # Weight title similarity more heavily
                jaccard_score = max(jaccard_score, title_similarity * 0.8)
            
            return jaccard_score
            
        except Exception as e:
            logger.error(f"Error calculating similarity score: {e}")
            return 0.0
    
    @function_tool
    def is_duplicate(self, article: Dict[str, Any], similar_articles: List[Dict[str, Any]], threshold: float = 0.85) -> bool:
        """Determine if an article is a duplicate based on similarity scores."""
        try:
            if not similar_articles:
                return False
            
            # Check if any similar article has high enough similarity
            for similar in similar_articles:
                similarity_score = similar.get('score', 0.0)
                if similarity_score >= threshold:
                    logger.info(f"Article '{article.get('title', '')}' is duplicate with score {similarity_score}")
                    return True
            
            return False
            
        except Exception as e:
            logger.error(f"Error checking for duplicates: {e}")
            return False
    
    @function_tool
    def filter_unique_articles(self, articles: List[Dict[str, Any]], company: str) -> List[Dict[str, Any]]:
        """Filter out duplicate articles, keeping only unique ones."""
        try:
            unique_articles = []
            
            for article in articles:
                # Query for similar articles in Pinecone
                similar_articles = self.query_similar_articles(article, company)
                
                # Check if this article is a duplicate
                is_dup = self.is_duplicate(article, similar_articles)
                
                if not is_dup:
                    unique_articles.append(article)
                    logger.info(f"Article '{article.get('title', '')}' is unique")
                else:
                    logger.info(f"Article '{article.get('title', '')}' is duplicate, skipping")
            
            logger.info(f"Filtered {len(articles)} articles to {len(unique_articles)} unique articles")
            return unique_articles
            
        except Exception as e:
            logger.error(f"Error filtering unique articles: {e}")
            return articles  # Return original list if error
    
    def create_agent(self) -> Agent:
        """Create the deduplication agent."""
        return Agent(
            name="Deduplicator",
            instructions="""
            You are a deduplication agent responsible for identifying and removing duplicate news articles.
            Your tasks are:
            1. Query Pinecone vector database for similar articles
            2. Calculate similarity scores between new and existing articles
            3. Identify duplicates based on content similarity (threshold: 0.85)
            4. Filter out duplicate articles, keeping only unique ones
            5. Return a list of unique articles that should be stored
            
            Focus on:
            - Title similarity
            - Content similarity
            - Publication date proximity
            - Source credibility
            
            Be conservative - only mark as duplicate if you're confident it's the same story.
            """,
            tools=[
                self.query_similar_articles,
                self.calculate_similarity_score,
                self.is_duplicate,
                self.filter_unique_articles
            ]
        )
    
    def deduplicate_articles(self, articles: List[Dict[str, Any]], company: str) -> List[Dict[str, Any]]:
        """Deduplicate articles for a specific company."""
        try:
            agent = self.create_agent()
            
            # Prepare input for the agent
            input_text = f"""
            Deduplicate the following articles for {company}:
            {articles}
            
            Query Pinecone for similar articles and remove duplicates.
            Return only unique articles that should be stored.
            """
            
            from agents import Runner
            result = Runner.run_sync(agent, input_text)
            
            # For now, use the tools directly since the agent output parsing is complex
            unique_articles = self.filter_unique_articles(articles, company)
            
            logger.info(f"Deduplicated {len(articles)} articles to {len(unique_articles)} unique articles for {company}")
            return unique_articles
            
        except Exception as e:
            logger.error(f"Error deduplicating articles for {company}: {e}")
            return articles  # Return original list if error

