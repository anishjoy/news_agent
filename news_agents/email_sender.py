"""Email Sender Agent using OpenAI Agents SDK."""

import os
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import List, Dict, Any
from agents import Agent, Runner, function_tool
from utils.email_formatter import EmailFormatter
from utils.logger import setup_logger

logger = setup_logger(__name__)

class EmailSenderAgent:
    def __init__(self):
        self.smtp_server = "smtp.gmail.com"
        self.smtp_port = 587
        self.sender_email = os.getenv("GMAIL_SENDER")
        self.sender_password = os.getenv("GMAIL_APP_PASSWORD")
        self.recipient_email = os.getenv("GMAIL_SENDER")  # Send to self for now
        
        # Load configuration
        import yaml
        with open('config.yaml', 'r') as f:
            self.config = yaml.safe_load(f)
        
        self.email_formatter = EmailFormatter(self.config.get('priorities', []))
    
    @function_tool
    def create_email_subject(self, total_articles: int, high_priority_count: int, top_companies: str) -> str:
        """Create email subject line based on articles and companies."""
        try:
            if high_priority_count > 0:
                subject = f"🔥 {total_articles} High-Priority News Updates - {top_companies}"
            else:
                subject = f"📰 {total_articles} News Updates - {top_companies}"
            
            logger.info(f"Created email subject: {subject}")
            return subject
            
        except Exception as e:
            logger.error(f"Error creating email subject: {e}")
            return f"📰 {total_articles} News Updates"
    
    @function_tool
    def format_email_content(self, article_count: int, companies: str) -> str:
        """Format articles into HTML email content."""
        try:
            # Simplified version for Agents SDK
            html_content = f"""
            <html>
            <body>
                <h1>News Summary</h1>
                <p>Found {article_count} articles for companies: {companies}</p>
                <p>This is a simplified email format for the Agents SDK demonstration.</p>
            </body>
            </html>
            """
            logger.info(f"Formatted email content for {article_count} articles")
            return html_content
            
        except Exception as e:
            logger.error(f"Error formatting email content: {e}")
            return f"<html><body><h1>News Summary</h1><p>Error formatting content: {e}</p></body></html>"
    
    @function_tool
    def send_email(self, subject: str, html_content: str, recipient: str) -> str:
        """Send email via Gmail SMTP."""
        try:
            # Create message
            msg = MIMEMultipart('alternative')
            msg['Subject'] = subject
            msg['From'] = self.sender_email
            msg['To'] = recipient
            
            # Create HTML part
            html_part = MIMEText(html_content, 'html')
            msg.attach(html_part)
            
            # Send email
            with smtplib.SMTP(self.smtp_server, self.smtp_port) as server:
                server.starttls()
                server.login(self.sender_email, self.sender_password)
                server.send_message(msg)
            
            logger.info(f"Successfully sent email to {recipient}")
            return f"Successfully sent email to {recipient}"
            
        except Exception as e:
            logger.error(f"Error sending email: {e}")
            return f"Error sending email: {e}"
    
    def create_agent(self) -> Agent:
        """Create the email sender agent using OpenAI Agents SDK."""
        return Agent(
            name="Email Sender",
            instructions="""
            You are an email sender agent specialized in creating and sending news summaries via email.
            Your primary responsibilities are:
            1. Create compelling email subject lines
            2. Format articles into professional HTML emails
            3. Send emails via Gmail SMTP
            4. Handle email delivery and error reporting
            
            For each email, use the available tools to:
            1. Create appropriate subject lines based on content
            2. Format articles into HTML email content
            3. Send emails via SMTP
            4. Track delivery success/failure
            
            Focus on creating executive-style summaries with key highlights.
            Prioritize high-impact news and AI-related content.
            """,
            tools=[
                self.create_email_subject,
                self.format_email_content,
                self.send_email
            ]
        )
    
    def send_news_summary(self, articles: List[Dict[str, Any]], companies: List[str]) -> bool:
        """Send news summary email using direct SMTP calls."""
        try:
            if not articles:
                logger.info("No articles to send in email summary")
                return True
            
            # Create email subject
            total_articles = len(articles)
            high_priority_count = len([
                a for a in articles 
                if a.get('relevance_score', 0) >= 5.0
            ])
            
            # Get top companies by article count
            company_counts = {}
            for article in articles:
                company = article.get('company', 'Unknown')
                company_counts[company] = company_counts.get(company, 0) + 1
            
            top_companies = sorted(company_counts.items(), key=lambda x: x[1], reverse=True)[:3]
            company_names = [company for company, _ in top_companies]
            
            if high_priority_count > 0:
                subject = f"🔥 {total_articles} High-Priority News Updates - {', '.join(company_names)} and {len(company_counts) - len(company_names)} others"
            else:
                subject = f"📰 {total_articles} News Updates - {', '.join(company_names)} and {len(company_counts) - len(company_names)} others"
            
            # Format email content
            html_content = self.email_formatter.format_email_html(articles, companies)
            
            # Send email
            success = self.send_email(subject, html_content, self.recipient_email)
            
            if success:
                logger.info(f"Successfully sent news summary with {len(articles)} articles")
            else:
                logger.error("Failed to send news summary email")
            
            return success
            
        except Exception as e:
            logger.error(f"Error sending news summary: {e}")
            return False