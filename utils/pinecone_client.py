"""Pinecone client utilities for vector operations."""

import os
from typing import List, Dict, Any, Optional
from pinecone import Pinecone
from openai import OpenAI
import logging

logger = logging.getLogger(__name__)

class PineconeClient:
    def __init__(self):
        self.pc = Pinecone(api_key=os.getenv("PINECONE_API_KEY"))
        self.index_name = os.getenv("PINECONE_INDEX_NAME", "news-agent-index")
        self.index = self.pc.Index(self.index_name)
        self.openai_client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
        
    def get_embedding(self, text: str) -> List[float]:
        """Generate embedding for text using OpenAI."""
        try:
            response = self.openai_client.embeddings.create(
                model="text-embedding-3-small",
                input=text
            )
            return response.data[0].embedding
        except Exception as e:
            logger.error(f"Error generating embedding: {e}")
            raise
    
    def query_similar(self, text: str, company: str, top_k: int = 10, threshold: float = 0.85) -> List[Dict[str, Any]]:
        """Query for similar articles in Pinecone."""
        try:
            embedding = self.get_embedding(text)
            results = self.index.query(
                vector=embedding,
                top_k=top_k,
                include_metadata=True,
                filter={"company": company}
            )
            
            # Filter by similarity threshold
            similar_articles = []
            for match in results.matches:
                if match.score >= threshold:
                    similar_articles.append({
                        "id": match.id,
                        "score": match.score,
                        "metadata": match.metadata
                    })
            
            return similar_articles
        except Exception as e:
            logger.error(f"Error querying Pinecone: {e}")
            return []
    
    def upsert_article(self, article_id: str, content: str, metadata: Dict[str, Any]) -> bool:
        """Store article in Pinecone."""
        try:
            embedding = self.get_embedding(content)
            
            self.index.upsert(
                vectors=[{
                    "id": article_id,
                    "values": embedding,
                    "metadata": metadata
                }]
            )
            return True
        except Exception as e:
            logger.error(f"Error upserting to Pinecone: {e}")
            return False
    
    def batch_upsert(self, articles: List[Dict[str, Any]]) -> bool:
        """Batch upsert multiple articles."""
        try:
            vectors = []
            for article in articles:
                embedding = self.get_embedding(article["content"])
                vectors.append({
                    "id": article["id"],
                    "values": embedding,
                    "metadata": article["metadata"]
                })
            
            self.index.upsert(vectors=vectors)
            return True
        except Exception as e:
            logger.error(f"Error batch upserting to Pinecone: {e}")
            return False

