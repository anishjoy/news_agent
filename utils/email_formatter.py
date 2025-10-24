"""Email formatting utilities for news summaries."""

from typing import List, Dict, Any
from datetime import datetime
import logging
import html as html_module
import re

logger = logging.getLogger(__name__)

class EmailFormatter:
    def __init__(self, priorities: List[str]):
        self.priorities = priorities
    
    def _clean_html_content(self, content: str) -> str:
        """Clean and escape HTML content to prevent issues in email."""
        if not content:
            return ""
        
        # Remove HTML tags and decode entities
        content = re.sub(r'<[^>]+>', '', content)
        content = html_module.unescape(content)
        
        # Clean up extra whitespace
        content = re.sub(r'\s+', ' ', content).strip()
        
        # Truncate if too long
        if len(content) > 300:
            content = content[:300] + "..."
        
        return content
    
    def _format_date(self, date_str: str) -> str:
        """Format date string for display."""
        if not date_str or date_str == 'Unknown date':
            return 'Recent'
        
        try:
            # Try to parse and format the date
            from datetime import datetime
            # Handle various date formats
            for fmt in ['%Y-%m-%dT%H:%M:%SZ', '%Y-%m-%d %H:%M:%S', '%Y-%m-%d']:
                try:
                    dt = datetime.strptime(date_str[:19], fmt)
                    return dt.strftime('%b %d, %Y')
                except:
                    continue
            return 'Recent'
        except:
            return 'Recent'
    
    def calculate_priority_score(self, article: Dict[str, Any]) -> float:
        """Calculate priority score based on keywords and content."""
        score = article.get('relevance_score', 0.0)  # Use the relevance score from news collector
        
        # Additional boost for specific high-impact indicators
        content = f"{article.get('title', '')} {article.get('snippet', '')}".lower()
        
        # Leadership changes get extra boost
        if any(word in content for word in ["ceo", "cfo", "cto", "president", "chairman", "founder"]):
            if any(word in content for word in ["appointed", "named", "resigned", "stepped down", "fired", "replaced"]):
                score += 2.0
        
        # Stock movements get extra boost
        import re
        stock_patterns = [
            r'(\d+(?:\.\d+)?%)\s*(?:up|down|rise|fall|gain|loss)',
            r'(?:surge|plunge|jump|drop|spike|crash)\s*(\d+(?:\.\d+)?%)'
        ]
        
        for pattern in stock_patterns:
            matches = re.findall(pattern, content)
            for match in matches:
                try:
                    percentage = float(match.replace('%', ''))
                    if percentage >= 5.0:
                        score += 1.5
                        break
                except:
                    continue
        
        # AI news gets extra boost
        ai_keywords = ["ai", "artificial intelligence", "machine learning", "chatgpt", "gpt", "llm"]
        if any(keyword in content for keyword in ai_keywords):
            score += 1.0
        
        return score
    
    def format_email_html(self, articles: List[Dict[str, Any]], companies: List[str]) -> str:
        """Format articles into HTML email."""
        if not articles:
            return self._empty_summary_html()
        
        # Sort articles by priority score
        sorted_articles = sorted(articles, key=self.calculate_priority_score, reverse=True)
        
        # Group by company
        company_articles = {}
        for article in sorted_articles:
            company = article.get("company", "Unknown")
            if company not in company_articles:
                company_articles[company] = []
            company_articles[company].append(article)
        
        html = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="utf-8">
            <title>Daily News Summary</title>
            <style>
                body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
                .header {{ background-color: #f4f4f4; padding: 20px; text-align: center; }}
                .company-section {{ margin: 20px 0; padding: 15px; border-left: 4px solid #007cba; }}
                .article {{ margin: 15px 0; padding: 10px; background-color: #f9f9f9; border-radius: 5px; }}
                .article.high-priority {{ background-color: #fff3cd; border-left: 4px solid #ffc107; }}
                .article-title {{ font-weight: bold; color: #007cba; margin-bottom: 5px; }}
                .article-meta {{ font-size: 0.9em; color: #666; margin-bottom: 8px; }}
                .article-snippet {{ margin-bottom: 10px; }}
                .article-link {{ color: #007cba; text-decoration: none; }}
                .priority-badge {{ background-color: #ffc107; color: #000; padding: 2px 6px; border-radius: 3px; font-size: 0.8em; }}
                .summary-stats {{ background-color: #e7f3ff; padding: 15px; margin: 20px 0; border-radius: 5px; }}
            </style>
        </head>
        <body>
            <div class="header">
                <h1>📰 Daily News Summary</h1>
                <p>Generated on {datetime.now().strftime('%B %d, %Y at %I:%M %p')}</p>
            </div>
            
            <div class="summary-stats">
                <h3>📊 Summary Statistics</h3>
                <p><strong>Total Articles:</strong> {len(articles)}</p>
                <p><strong>Companies Monitored:</strong> {', '.join(companies)}</p>
                <p><strong>High Priority Articles:</strong> {len([a for a in articles if self.calculate_priority_score(a) >= 5.0])}</p>
            </div>
        """
        
        # Add articles by company
        for company, company_articles in company_articles.items():
            html += f"""
            <div class="company-section">
                <h2>🏢 {company}</h2>
            """
            
            for article in company_articles:
                priority_score = self.calculate_priority_score(article)
                priority_class = "high-priority" if priority_score >= 5.0 else ""
                priority_badge = '<span class="priority-badge">🔥 HIGH PRIORITY</span>' if priority_score >= 5.0 else ""
                
                # Clean and escape content
                title = self._clean_html_content(article.get('title', 'No title'))
                snippet = self._clean_html_content(article.get('snippet', 'No summary available'))
                url = article.get('url', '#')
                published_date = self._format_date(article.get('published_date', 'Unknown date'))
                
                # Escape HTML content
                escaped_title = html_module.escape(title)
                escaped_url = html_module.escape(url)
                escaped_snippet = html_module.escape(snippet)
                
                html += f"""
                <div class="article {priority_class}">
                    <div class="article-title">
                        {escaped_title} {priority_badge}
                    </div>
                    <div class="article-meta">
                        📅 {published_date} | 
                        🔗 <a href="{escaped_url}" class="article-link">Read Full Article</a>
                    </div>
                    <div class="article-snippet">
                        {escaped_snippet}
                    </div>
                </div>
                """
            
            html += "</div>"
        
        html += """
            <div style="margin-top: 30px; padding: 20px; background-color: #f4f4f4; text-align: center;">
                <p><em>This summary was generated by your AI News Agent</em></p>
            </div>
        </body>
        </html>
        """
        
        return html
    
    def _empty_summary_html(self) -> str:
        """HTML for when no articles are found."""
        return f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="utf-8">
            <title>Daily News Summary</title>
        </head>
        <body style="font-family: Arial, sans-serif; text-align: center; padding: 50px;">
            <h1>📰 Daily News Summary</h1>
            <p>No new articles found for the monitored companies today.</p>
            <p><em>Generated on {datetime.now().strftime('%B %d, %Y at %I:%M %p')}</em></p>
        </body>
        </html>
        """

