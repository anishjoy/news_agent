# News Agent System Architecture

## Overview

The News Agent System is a multi-agent architecture built using the OpenAI Agents SDK that automatically monitors, processes, and summarizes news about companies you manage.

## System Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                    News Agent System                            │
├─────────────────────────────────────────────────────────────────┤
│  GitHub Actions (Scheduler)                                    │
│  └── Daily at 7 AM EST                                         │
│      └── Triggers main.py                                     │
└─────────────────────────────────────────────────────────────────┘
                                │
                                ▼
┌─────────────────────────────────────────────────────────────────┐
│                    Orchestration Layer                         │
│  └── NewsAgentOrchestrator (main.py)                          │
│      ├── Environment Validation                               │
│      ├── Company Configuration Loading                        │
│      └── Pipeline Coordination                                │
└─────────────────────────────────────────────────────────────────┘
                                │
                                ▼
┌─────────────────────────────────────────────────────────────────┐
│                    Agent Pipeline                              │
├─────────────────────────────────────────────────────────────────┤
│  1. News Collection Agent                                      │
│     ├── NewsAPI Integration                                   │
│     ├── Google News RSS                                        │
│     ├── Web Scraping (BeautifulSoup)                         │
│     └── Relevance Scoring                                      │
│                                                                 │
│  2. Deduplication Agent                                        │
│     ├── Pinecone Vector Search                                 │
│     ├── Similarity Calculation                                 │
│     └── Duplicate Detection                                    │
│                                                                 │
│  3. Storage Agent                                              │
│     ├── Pinecone Vector Storage                                │
│     ├── Metadata Management                                    │
│     └── Batch Operations                                       │
│                                                                 │
│  4. Email Agent                                                │
│     ├── HTML Email Generation                                  │
│     ├── Gmail SMTP Integration                                 │
│     └── Priority-based Formatting                              │
└─────────────────────────────────────────────────────────────────┘
```

## Data Flow

### 1. News Collection Phase
```
Company List → NewsAPI → Google News → Web Scraping → Relevance Scoring
     ↓
Filtered Articles (relevance_score >= 2.0)
```

### 2. Deduplication Phase
```
New Articles → Pinecone Query → Similarity Check → Duplicate Detection
     ↓
Unique Articles Only
```

### 3. Storage Phase
```
Unique Articles → Embedding Generation → Pinecone Storage → Verification
     ↓
Stored with Metadata (company, date, url, content)
```

### 4. Email Phase
```
All Articles → Priority Scoring → HTML Generation → Email Sending
     ↓
Daily Summary Email
```

## Agent Details

### News Collection Agent
- **Purpose**: Gather news from multiple sources
- **Tools**: NewsAPI, Google News RSS, Web Scraping
- **Output**: Structured article data with relevance scores
- **Focus**: Stock prices, leadership changes, AI developments

### Deduplication Agent
- **Purpose**: Remove duplicate articles
- **Tools**: Pinecone vector search, similarity calculation
- **Output**: Unique articles only
- **Threshold**: 0.85 similarity score

### Storage Agent
- **Purpose**: Store articles in vector database
- **Tools**: Pinecone upsert operations
- **Output**: Storage confirmation and statistics
- **Metadata**: Company, date, URL, content, relevance

### Email Agent
- **Purpose**: Send daily summaries
- **Tools**: Gmail SMTP, HTML formatting
- **Output**: Professional email with prioritized content
- **Features**: AI-highlighted, company-grouped, executive-style

## Technology Stack

### Core Framework
- **OpenAI Agents SDK**: Multi-agent coordination
- **Python 3.11+**: Runtime environment
- **GitHub Actions**: Scheduling and deployment

### Data Sources
- **NewsAPI**: Primary news source
- **Google News RSS**: Secondary source
- **Web Scraping**: Fallback for specific sites

### Storage & Processing
- **Pinecone**: Vector database for deduplication
- **OpenAI Embeddings**: text-embedding-3-small
- **OpenAI GPT-4o**: Agent reasoning

### Communication
- **Gmail SMTP**: Email delivery
- **HTML Templates**: Professional formatting

## Configuration

### Environment Variables
```bash
OPENAI_API_KEY=sk-...           # OpenAI API key
PINECONE_API_KEY=...            # Pinecone API key
NEWS_API_KEY=...               # NewsAPI key
GMAIL_SENDER=...               # Gmail address
GMAIL_APP_PASSWORD=...         # Gmail app password
```

### Company Configuration
```yaml
companies:
  - name: "Tiger Analytics"
  - name: "Microsoft"
  - name: "Google"

priorities:
  - "AI"
  - "Artificial Intelligence"
  - "stock price"
  - "leadership change"
```

## Error Handling

### Agent-Level Errors
- Individual agent failures don't stop the pipeline
- Fallback to alternative data sources
- Comprehensive logging and error reporting

### System-Level Errors
- Environment validation before execution
- Graceful degradation on API failures
- GitHub Actions failure notifications

### Data Quality
- Relevance scoring filters low-quality content
- Deduplication prevents information overload
- Priority-based email formatting

## Scalability Considerations

### Horizontal Scaling
- Each company processed independently
- Parallel agent execution possible
- Stateless agent design

### Vertical Scaling
- Configurable article limits
- Batch processing for storage
- Rate limiting for API calls

### Cost Management
- NewsAPI free tier: 1000 requests/day
- Pinecone usage monitoring
- OpenAI token optimization

## Security

### API Key Management
- Environment variables for secrets
- GitHub Secrets for CI/CD
- No hardcoded credentials

### Data Privacy
- No personal data collection
- Public news sources only
- Secure email transmission

### Access Control
- GitHub repository permissions
- Gmail app password authentication
- Pinecone API key restrictions

## Monitoring & Observability

### Logging
- Structured logging with timestamps
- Agent execution tracking
- Error categorization and reporting

### Metrics
- Articles collected per company
- Deduplication effectiveness
- Storage success rates
- Email delivery confirmation

### Alerts
- GitHub Actions failure notifications
- Email delivery failures
- API quota exceeded warnings

## Future Enhancements

### Additional Data Sources
- Social media monitoring
- Press release feeds
- Financial data APIs

### Advanced Features
- Sentiment analysis
- Trend detection
- Custom alert rules
- Mobile app notifications

### Integration Options
- Slack notifications
- Microsoft Teams
- Webhook endpoints
- API for external systems

