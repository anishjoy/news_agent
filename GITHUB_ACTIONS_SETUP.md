# GitHub Actions Deployment Guide

This guide will help you deploy the News Agent System to GitHub Actions for automated daily execution.

## Prerequisites

1. **GitHub Repository**: Your code should be in a GitHub repository
2. **API Keys**: You need the following API keys:
   - OpenAI API Key
   - Pinecone API Key
   - NewsAPI Key
   - Gmail App Password

## Step 1: Set Up GitHub Secrets

Go to your GitHub repository → Settings → Secrets and variables → Actions → New repository secret

Add the following secrets:

### Required Secrets

| Secret Name | Description | Example |
|-------------|-------------|---------|
| `OPENAI_API_KEY` | Your OpenAI API key | `sk-...` |
| `PINECONE_API_KEY` | Your Pinecone API key | `abc123...` |
| `NEWS_API_KEY` | Your NewsAPI key | `abc123...` |
| `GMAIL_SENDER` | Your Gmail address | `your-email@gmail.com` |
| `GMAIL_APP_PASSWORD` | Gmail App Password (not regular password) | `abcd efgh ijkl mnop` |

### Optional Secrets

| Secret Name | Description | Default |
|-------------|-------------|---------|
| `PINECONE_INDEX_NAME` | Pinecone index name | `news-agent-index` |
| `PINECONE_ENVIRONMENT` | Pinecone environment | `us-east-1-aws` |

## Step 2: Configure Gmail App Password

1. Go to your Google Account settings
2. Navigate to Security → 2-Step Verification
3. At the bottom, click "App passwords"
4. Select "Mail" and "Other (Custom name)"
5. Enter "News Agent System" as the name
6. Copy the generated 16-character password
7. Add it to GitHub secrets as `GMAIL_APP_PASSWORD`

## Step 3: Verify Configuration

The system uses the following configuration files:

- `config.yaml` - Company names and email settings
- `github_actions_main.py` - Production script for GitHub Actions
- `.github/workflows/daily_news.yml` - GitHub Actions workflow

## Step 4: Test the Workflow

### Manual Trigger

1. Go to your GitHub repository
2. Click on "Actions" tab
3. Select "Daily News Collection" workflow
4. Click "Run workflow" button
5. Click "Run workflow" to trigger manually

### Check Results

1. Click on the workflow run to see detailed logs
2. Check the "Run News Agent System" step for execution details
3. Look for "Email sent successfully" in the logs
4. Check your email for the news summary

## Step 5: Schedule Configuration

The workflow is configured to run daily at 7:00 AM UTC. To adjust for your timezone:

1. Edit `.github/workflows/daily_news.yml`
2. Change the cron expression: `'0 7 * * *'`
3. Use [crontab.guru](https://crontab.guru/) to calculate your desired time

### Common Timezone Examples

| Timezone | Cron Expression | Local Time |
|----------|----------------|------------|
| UTC | `'0 7 * * *'` | 7:00 AM UTC |
| EST (UTC-5) | `'0 12 * * *'` | 7:00 AM EST |
| PST (UTC-8) | `'0 15 * * *'` | 7:00 AM PST |
| IST (UTC+5:30) | `'0 1 * * *'` | 7:00 AM IST |

## Step 6: Monitor and Debug

### Viewing Logs

1. Go to Actions tab in your repository
2. Click on the latest workflow run
3. Expand the "Run News Agent System" step
4. Check for any errors or warnings

### Common Issues

| Issue | Solution |
|-------|----------|
| "Missing required environment variables" | Check that all secrets are set correctly |
| "Gmail credentials not configured" | Verify Gmail App Password is correct |
| "Pinecone connection failed" | Check Pinecone API key and index name |
| "NewsAPI rate limit exceeded" | Wait for rate limit reset or upgrade plan |

### Log Files

The system creates log files in the `logs/` directory:
- `news_agent_YYYYMMDD.log` - Daily execution logs
- Logs are automatically uploaded as artifacts for 7 days

## Step 7: Customization

### Adding More Companies

Edit `config.yaml`:

```yaml
companies:
  - name: "Microsoft"
  - name: "Apple"
  - name: "Tesla"
  - name: "NVIDIA"
  - name: "Your Company"  # Add new companies here
```

### Changing Email Recipient

Edit `config.yaml`:

```yaml
email:
  recipient: "your-email@example.com"  # Change recipient
  sender: "your-email@gmail.com"
```

### Modifying News Priorities

Edit `config.yaml`:

```yaml
priorities:
  - "AI"
  - "Artificial Intelligence"
  - "Machine Learning"
  - "stock price"
  - "leadership change"
  - "Your Priority"  # Add custom priorities
```

## Production Considerations

### Resource Limits

- GitHub Actions provides 2,000 minutes/month for free
- Each run takes approximately 5-10 minutes
- Monitor usage in Settings → Billing

### Error Handling

The system includes comprehensive error handling:
- Failed API calls are logged and skipped
- Email failures are logged but don't stop execution
- Individual company failures don't affect others

### Security

- All API keys are stored as encrypted secrets
- No sensitive data is logged
- Gmail App Password is more secure than regular password

## Troubleshooting

### Workflow Not Running

1. Check if the workflow file is in `.github/workflows/`
2. Verify the cron syntax is correct
3. Check repository permissions

### Email Not Received

1. Check Gmail App Password is correct
2. Verify recipient email in `config.yaml`
3. Check spam folder
4. Look for "Email sent successfully" in logs

### No Articles Found

1. Check NewsAPI key is valid
2. Verify companies are in `config.yaml`
3. Check if articles meet relevance threshold (≥3.0)
4. Look for "Collected X articles" in logs

## Support

If you encounter issues:

1. Check the GitHub Actions logs first
2. Verify all secrets are set correctly
3. Test the system locally with `python github_actions_main.py`
4. Check the individual agent logs for specific errors

## Success Indicators

You'll know the system is working when you see:

1. ✅ "All environment variables present"
2. ✅ "Collected X articles for [Company]"
3. ✅ "Deduplicated X articles to Y unique articles"
4. ✅ "Stored X articles for [Company]"
5. ✅ "Email sent successfully to [email]"
6. ✅ "Pipeline completed successfully"

The system will send you a daily email with the latest news about your monitored companies!
