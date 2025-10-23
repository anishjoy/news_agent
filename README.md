# Multi-Agent News Monitoring System

A sophisticated multi-agent system that automatically collects, deduplicates, and summarizes news about companies you manage, with special focus on AI-related developments.

## Architecture

The system uses 4 specialized agents built with the OpenAI Agents SDK:

1. **News Collection Agent** - Scrapes web and calls news APIs for company information
2. **Deduplication Agent** - Compares new articles against Pinecone vector store
3. **Storage Agent** - Inserts new/unique news into Pinecone
4. **Email Agent** - Sends consolidated summary via Gmail SMTP

## Setup Instructions

### 1. Clone and Install Dependencies

```bash
git clone <your-repo>
cd news_agent
pip install -r requirements.txt
```

### 2. Configure Environment Variables

Copy `.env.example` to `.env` and fill in your API keys:

```bash
cp .env.example .env
```

Required API keys:
- **OpenAI API Key**: Get from https://platform.openai.com/api-keys
- **Pinecone API Key**: Get from https://app.pinecone.io/
- **NewsAPI Key**: Get from https://newsapi.org/ (free tier available)
- **Gmail App Password**: Enable 2FA and generate app password

### 3. Configure Companies

Edit `config.yaml` to add the companies you want to monitor:

```yaml
companies:
  - name: "Tiger Analytics"
  - name: "Microsoft"
  - name: "Google"
```

### 4. Set Up Pinecone

1. Create a Pinecone account at https://app.pinecone.io/
2. Create a new index:
   - Name: `news-agent-index`
   - Dimensions: `1536`
   - Metric: `cosine`
3. Note your environment and API key

### 5. GitHub Actions Setup

1. Fork this repository
2. Go to Settings > Secrets and variables > Actions
3. Add the following secrets:
   - `OPENAI_API_KEY`
   - `PINECONE_API_KEY`
   - `NEWS_API_KEY`
   - `GMAIL_APP_PASSWORD`
   - `GMAIL_SENDER`

### 6. Test Locally

```bash
python main.py
```

### 7. Deploy to GitHub Actions

The workflow will automatically run daily at 7 AM UTC. You can also trigger it manually from the Actions tab.

## Features

- **Automated Daily Collection**: Runs every day at 7 AM
- **Smart Deduplication**: Uses vector similarity to avoid duplicate news
- **AI-Focused Prioritization**: Special attention to AI-related news
- **Executive Summaries**: Clean, actionable email reports
- **Multi-Source News**: NewsAPI, web scraping, and RSS feeds
- **Company-Specific Tracking**: Separate namespaces for each company

## Configuration

### Adding Companies

Edit `config.yaml`:

```yaml
companies:
  - name: "Your Company Name"
```

### Priority Keywords

Modify the `priorities` section to focus on specific topics:

```yaml
priorities:
  - "AI"
  - "Artificial Intelligence"
  - "Machine Learning"
  - "stock price"
  - "leadership change"
```

## Troubleshooting

### Common Issues

1. **Gmail Authentication**: Make sure you're using an App Password, not your regular password
2. **Pinecone Connection**: Verify your API key and index name
3. **NewsAPI Limits**: Free tier has 1000 requests/day
4. **Timezone**: Adjust the cron schedule in `.github/workflows/daily_news.yml`

### Manual Testing

```bash
# Test individual agents
python -c "from agents.news_collector import test_agent; test_agent()"
```

## Architecture Diagram

```
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│  News Collector │───▶│  Deduplicator    │───▶│  Storage Agent  │
│  (Web + APIs)   │    │  (Pinecone)      │    │  (Pinecone)     │
└─────────────────┘    └──────────────────┘    └─────────────────┘
                                                         │
                                                         ▼
                                                ┌─────────────────┐
                                                │  Email Agent    │
                                                │  (Gmail SMTP)   │
                                                └─────────────────┘
```

## License

MIT License

