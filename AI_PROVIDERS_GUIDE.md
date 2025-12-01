# AI Providers Guide - OpenAI GPT & Anthropic Claude

Your Cloud Resource Manager now supports **both OpenAI GPT and Anthropic Claude** for AI-powered features!

## Overview

The AI Chat feature can now use either:
- **Anthropic Claude** (Claude 3.5 Sonnet) - Default
- **OpenAI GPT** (GPT-4 Turbo)

## Setup Instructions

### 1. Configure API Keys

Edit the `backend/.env` file and add your API keys:

```env
# Anthropic Claude API - Get from: https://console.anthropic.com
ANTHROPIC_API_KEY=sk-ant-your-key-here

# OpenAI GPT API - Get from: https://platform.openai.com/api-keys
OPENAI_API_KEY=sk-your-openai-key-here
```

### 2. Choose Your AI Provider

In `backend/.env`, set the `AI_PROVIDER` variable:

```env
# Choose: "anthropic" or "openai"
AI_PROVIDER=anthropic    # Use Claude (default)
# or
AI_PROVIDER=openai       # Use GPT
```

### 3. Restart the Backend Server

After making changes to `.env`, restart the backend:

```bash
# If running manually
cd backend
python -m uvicorn app.main:app --reload

# Or if using the background process, it should auto-reload
```

## Getting API Keys

### Anthropic Claude API Key

1. Go to [https://console.anthropic.com](https://console.anthropic.com)
2. Sign up or log in
3. Navigate to API Keys section
4. Create a new API key
5. Copy the key (starts with `sk-ant-`)
6. Paste it into `ANTHROPIC_API_KEY` in `.env`

### OpenAI GPT API Key

1. Go to [https://platform.openai.com/api-keys](https://platform.openai.com/api-keys)
2. Sign up or log in
3. Click "Create new secret key"
4. Give it a name (e.g., "Cloud Resource Manager")
5. Copy the key (starts with `sk-`)
6. Paste it into `OPENAI_API_KEY` in `.env`

## Features Supported by Each Provider

### Anthropic Claude (Default)
- **Model**: Claude 3.5 Sonnet (claude-3-5-sonnet-20241022)
- **Max Tokens**: 1024
- **Best for**: Complex reasoning, detailed analysis, multi-step queries
- **Cost**: ~$3 per million input tokens, ~$15 per million output tokens

### OpenAI GPT
- **Model**: GPT-4 Turbo Preview
- **Max Tokens**: 1024
- **Temperature**: 0.7 (balanced creativity)
- **Best for**: General queries, familiar interface, broad knowledge
- **Cost**: ~$10 per million input tokens, ~$30 per million output tokens

## Switching Between Providers

You can switch between providers at any time:

1. Open `backend/.env`
2. Change `AI_PROVIDER=anthropic` to `AI_PROVIDER=openai` (or vice versa)
3. Save the file
4. The backend server will auto-reload (if using `--reload` flag)
5. Your AI Chat will now use the new provider

## Testing the Configuration

### 1. Check Backend Logs

When the backend starts, you'll see:
```
>> Cloud Resource Manager v0.1.0 started
>> AI Natural Language Query: Enabled
```

### 2. Test in AI Chat

Go to [http://localhost:3000/ai-chat](http://localhost:3000/ai-chat) and try a query:
```
"What is my total monthly cost?"
```

The response will include which provider was used.

### 3. Error Messages

If you see an error like:
- **"Anthropic AI is selected but not configured"** → Add `ANTHROPIC_API_KEY` to `.env`
- **"OpenAI is selected but not configured"** → Add `OPENAI_API_KEY` to `.env`

## Cost Comparison

### Example: 100 AI Chat queries per month

**Anthropic Claude:**
- Input: ~100,000 tokens = $0.30
- Output: ~50,000 tokens = $0.75
- **Total: ~$1.05/month**

**OpenAI GPT-4 Turbo:**
- Input: ~100,000 tokens = $1.00
- Output: ~50,000 tokens = $1.50
- **Total: ~$2.50/month**

> Note: Both are very affordable for typical use. Choose based on quality of responses for your use case.

## Recommendations

### Use Anthropic Claude If:
- You need detailed cost analysis and optimization recommendations
- You want more nuanced, context-aware responses
- You prefer cutting-edge AI capabilities
- You're okay with slightly higher setup complexity

### Use OpenAI GPT If:
- You're already familiar with ChatGPT
- You want broader general knowledge access
- You prefer OpenAI's ecosystem
- You need multi-language support

## Advanced Configuration

### Changing Models

Edit `backend/app/ai/nl_query_service.py`:

For **Anthropic**, change the model in `_query_anthropic` method:
```python
model="claude-3-5-sonnet-20241022"  # Current
# or
model="claude-3-opus-20240229"      # More powerful, slower
```

For **OpenAI**, change the model in `_query_openai` method:
```python
model="gpt-4-turbo-preview"  # Current
# or
model="gpt-4"                # More stable
# or
model="gpt-3.5-turbo"        # Faster, cheaper
```

### Adjusting Response Length

In both methods, adjust `max_tokens`:
```python
max_tokens=1024  # Default
# or
max_tokens=2048  # Longer responses
# or
max_tokens=512   # Shorter, cheaper
```

## Troubleshooting

### Problem: "AI is not enabled"
**Solution**: Make sure you have set the appropriate API key in `.env` and restarted the backend.

### Problem: API key not working
**Solution**:
1. Check that the key is correctly copied (no extra spaces)
2. Verify the key is active in your provider's dashboard
3. Check if you have billing set up (both providers require payment info)

### Problem: Backend won't start after changes
**Solution**:
1. Check `.env` file syntax (no quotes around values)
2. Make sure `AI_PROVIDER` is exactly "anthropic" or "openai"
3. Check backend console for error messages

### Problem: Responses are slow
**Solution**:
- This is normal for complex queries
- Claude 3.5 Sonnet is faster than GPT-4 Turbo
- Consider using GPT-3.5-turbo for faster responses

## Security Notes

**IMPORTANT**:
- Never commit your `.env` file to Git
- Keep your API keys secret
- Rotate keys regularly
- Monitor usage in provider dashboards
- Set spending limits in both Anthropic and OpenAI dashboards

## What's Next?

Now that you have dual AI provider support:
1. Test both providers with the same queries
2. Compare response quality and speed
3. Choose your preferred provider
4. Set up billing alerts in provider dashboards
5. Enjoy AI-powered cloud management!

## Support

- **Anthropic Support**: https://support.anthropic.com
- **OpenAI Support**: https://help.openai.com
- **API Documentation**:
  - Anthropic: https://docs.anthropic.com
  - OpenAI: https://platform.openai.com/docs

---

**You now have the flexibility to choose the best AI provider for your needs!** 🚀
