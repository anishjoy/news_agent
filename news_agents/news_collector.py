"""News Collection Agent using OpenAI Agents SDK."""

import os
import yaml
import requests
import feedparser
from bs4 import BeautifulSoup
from newsapi import NewsApiClient
from typing import List, Dict, Any
from agents import Agent, Runner, function_tool
from utils.logger import setup_logger

logger = setup_logger(__name__)

class NewsCollectorAgent:
    def __init__(self):
        self.newsapi = NewsApiClient(api_key=os.getenv("NEWS_API_KEY"))
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        })
        
        # Load configuration
        with open('config.yaml', 'r') as f:
            self.config = yaml.safe_load(f)
    
    @function_tool
    def search_newsapi(self, company: str, days_back: int = 1) -> str:
        """Search for news using NewsAPI."""
        try:
            from datetime import datetime, timedelta
            
            # Calculate date range
            to_date = datetime.now()
            from_date = to_date - timedelta(days=days_back)
            
            # Search for company news
            articles = self.newsapi.get_everything(
                q=company,
                from_param=from_date.strftime('%Y-%m-%d'),
                to=to_date.strftime('%Y-%m-%d'),
                language='en',
                sort_by='publishedAt',
                page_size=50
            )
            
            results = []
            for article in articles.get('articles', []):
                results.append({
                    'title': article.get('title', ''),
                    'url': article.get('url', ''),
                    'published_date': article.get('publishedAt', ''),
                    'snippet': article.get('description', ''),
                    'source': article.get('source', {}).get('name', ''),
                    'company': company
                })
            
            logger.info(f"Found {len(results)} articles from NewsAPI for {company}")
            return f"Found {len(results)} articles from NewsAPI for {company}"
            
        except Exception as e:
            logger.error(f"Error searching NewsAPI for {company}: {e}")
            return f"Error searching NewsAPI for {company}: {e}"
    
    @function_tool
    def scrape_google_news(self, company: str) -> str:
        """Scrape Google News RSS feed for company news."""
        try:
            # Google News RSS URL
            query = company.replace(' ', '+')
            rss_url = f"https://news.google.com/rss/search?q={query}&hl=en-US&gl=US&ceid=US:en"
            
            feed = feedparser.parse(rss_url)
            results = []
            
            for entry in feed.entries[:20]:  # Limit to 20 articles
                results.append({
                    'title': entry.get('title', ''),
                    'url': entry.get('link', ''),
                    'published_date': entry.get('published', ''),
                    'snippet': entry.get('summary', ''),
                    'source': 'Google News',
                    'company': company
                })
            
            logger.info(f"Found {len(results)} articles from Google News for {company}")
            return f"Found {len(results)} articles from Google News for {company}"
            
        except Exception as e:
            logger.error(f"Error scraping Google News for {company}: {e}")
            return f"Error scraping Google News for {company}: {e}"
    
    def calculate_relevance_score(self, title: str, snippet: str) -> float:
        """Calculate relevance score for an article based on title and snippet."""
        try:
            score = 0.0
            content = f"{title} {snippet}".lower()
            title_lower = title.lower()
            
            # High-impact leadership changes (highest priority)
            leadership_keywords = ['ceo', 'cfo', 'cto', 'president', 'chairman', 'founder', 'co-founder']
            leadership_actions = ['appointed', 'named', 'resigned', 'stepped down', 'fired', 'terminated', 'replaced', 'hired', 'joined']
            
            for keyword in leadership_keywords:
                if keyword in content:
                    for action in leadership_actions:
                        if action in content:
                            score += 5.0  # Very high score for leadership changes
                            break
            
            # Stock price movements (look for percentage changes)
            import re
            stock_patterns = [
                r'(\d+(?:\.\d+)?%)\s*(?:up|down|rise|fall|gain|loss|increase|decrease)',
                r'(?:up|down|rise|fall|gain|loss|increase|decrease)\s*(\d+(?:\.\d+)?%)',
                r'(\d+(?:\.\d+)?%)\s*(?:higher|lower)',
                r'(?:surge|plunge|jump|drop|spike|crash)\s*(\d+(?:\.\d+)?%)'
            ]
            
            for pattern in stock_patterns:
                matches = re.findall(pattern, content)
                for match in matches:
                    try:
                        percentage = float(match.replace('%', ''))
                        if percentage >= 5.0:  # Only significant movements
                            score += 4.0
                            break
                    except:
                        continue
            
            # AI-related keywords (very high priority for you)
            ai_keywords = ['ai', 'artificial intelligence', 'machine learning', 'ml', 'neural', 'deep learning', 'chatgpt', 'gpt', 'llm', 'generative ai']
            for keyword in ai_keywords:
                if keyword in content:
                    score += 3.0
            
            # Business impact keywords
            business_keywords = ['acquisition', 'merger', 'partnership', 'deal', 'funding', 'investment', 'ipo', 'layoffs', 'hiring', 'expansion']
            for keyword in business_keywords:
                if keyword in content:
                    score += 2.0
            
            # Earnings and financial results
            earnings_keywords = ['earnings', 'revenue', 'profit', 'loss', 'quarterly', 'annual', 'guidance', 'forecast']
            for keyword in earnings_keywords:
                if keyword in content:
                    score += 1.5
            
            # Regulatory and legal issues
            regulatory_keywords = ['lawsuit', 'settlement', 'fine', 'regulatory', 'investigation', 'sec', 'ftc']
            for keyword in regulatory_keywords:
                if keyword in content:
                    score += 2.5
            
            # Product launches and major announcements
            product_keywords = ['launch', 'announce', 'unveil', 'release', 'introduce', 'breakthrough', 'innovation']
            for keyword in product_keywords:
                if keyword in content:
                    score += 1.5
            
            # Boost score for articles with high-impact words in title
            high_impact_words = ['breakthrough', 'major', 'significant', 'historic', 'record', 'first', 'new', 'revolutionary']
            for word in high_impact_words:
                if word in title_lower:
                    score += 1.0
            
            return min(score, 15.0)  # Cap at 15 for more granular scoring
            
        except Exception as e:
            logger.error(f"Error calculating relevance score: {e}")
            return 0.0
    
    def create_agent(self) -> Agent:
        """Create the news collection agent using OpenAI Agents SDK."""
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
                self.search_newsapi,
                self.scrape_google_news,
                self.calculate_relevance_score
            ]
        )
    
    def collect_news_for_company(self, company: str) -> List[Dict[str, Any]]:
        """Collect news for a specific company using direct API calls (bypassing Agents SDK)."""
        try:
            all_articles = []
            
            # Search NewsAPI directly
            try:
                from datetime import datetime, timedelta
                
                # Calculate date range
                to_date = datetime.now()
                from_date = to_date - timedelta(days=1)
                
                # Search for company news
                articles = self.newsapi.get_everything(
                    q=company,
                    from_param=from_date.strftime('%Y-%m-%d'),
                    to=to_date.strftime('%Y-%m-%d'),
                    language='en',
                    sort_by='publishedAt',
                    page_size=50
                )
                
                for article in articles.get('articles', []):
                    all_articles.append({
                        'title': article.get('title', ''),
                        'url': article.get('url', ''),
                        'published_date': article.get('publishedAt', ''),
                        'snippet': article.get('description', ''),
                        'source': article.get('source', {}).get('name', ''),
                        'company': company
                    })
                
                logger.info(f"Found {len(articles.get('articles', []))} articles from NewsAPI for {company}")
                
            except Exception as e:
                logger.error(f"Error searching NewsAPI for {company}: {e}")
            
            # Search Google News directly
            try:
                import feedparser
                
                # Google News RSS URL
                query = company.replace(' ', '+')
                rss_url = f"https://news.google.com/rss/search?q={query}&hl=en-US&gl=US&ceid=US:en"
                
                feed = feedparser.parse(rss_url)
                
                for entry in feed.entries[:20]:  # Limit to 20 articles
                    all_articles.append({
                        'title': entry.get('title', ''),
                        'url': entry.get('link', ''),
                        'published_date': entry.get('published', ''),
                        'snippet': entry.get('summary', ''),
                        'source': 'Google News',
                        'company': company
                    })
                
                logger.info(f"Found {len(feed.entries[:20])} articles from Google News for {company}")
                
            except Exception as e:
                logger.error(f"Error scraping Google News for {company}: {e}")
            
            # Calculate relevance scores and filter
            filtered_articles = []
            for article in all_articles:
                relevance_score = self.calculate_relevance_score(
                    article.get('title', ''), 
                    article.get('snippet', '')
                )
                if relevance_score >= 3.0:
                    article['relevance_score'] = relevance_score
                    filtered_articles.append(article)
            
            # Sort by relevance score (highest first)
            filtered_articles.sort(key=lambda x: x.get('relevance_score', 0), reverse=True)
            
            # Limit to top 10 most relevant articles per company
            filtered_articles = filtered_articles[:10]
            
            logger.info(f"Collected {len(filtered_articles)} relevant articles for {company}")
            return filtered_articles
            
        except Exception as e:
            logger.error(f"Error collecting news for {company}: {e}")
            return []