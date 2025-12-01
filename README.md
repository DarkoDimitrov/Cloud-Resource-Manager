 # Cloud Resource Manager

AI-powered multi-cloud resource management platform that provides unified visibility and intelligent optimization across OpenStack, AWS, and Azure environments.

## Features

### Core Features
- **Multi-Cloud Support**: Unified interface for OpenStack, AWS, and Azure
- **Real-time Monitoring**: Track VM status, resource utilization, and performance metrics
- **Cost Analysis**: Track spending, analyze cost trends, and forecast future costs
- **Smart Recommendations**: AI-powered optimization suggestions to reduce costs

### AI-Powered Features
- **Natural Language Queries**: Ask questions about your infrastructure in plain English
- **Anomaly Detection**: ML-based detection of unusual patterns in resource usage and costs
- **Predictive Cost Forecasting**: Time series analysis to predict future cloud costs
- **Intelligent Recommendations**: Context-aware optimization suggestions with confidence scores

## Quick Start

### Prerequisites

- Python 3.10 or higher
- Docker and Docker Compose (optional, for containerized deployment)
- Redis (for caching)
- PostgreSQL (optional, for production; SQLite used by default)

### Installation

#### 1. Clone the Repository

```bash
git clone <repository-url>
cd Cloud-Resource-Manager
```

#### 2. Backend Setup

```bash
cd backend

# Create virtual environment
python -m venv venv

# Activate virtual environment
# On Windows:
venv\Scripts\activate
# On macOS/Linux:
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Create .env file from example
cp .env.example .env

# Edit .env and add your configuration
# IMPORTANT: Set your ANTHROPIC_API_KEY for AI features
```

#### 3. Configure Environment Variables

Edit `backend/.env`:

```bash
# Required for AI features
ANTHROPIC_API_KEY=sk-ant-your-api-key-here

# Optional: Configure cloud provider credentials
# Or add them later via the API
```

#### 4. Run the Application

**Option A: Using Python directly**

```bash
cd backend
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

**Option B: Using Docker Compose**

```bash
# From the project root
docker-compose up -d
```

#### 5. Access the Application

- **API Documentation**: http://localhost:8000/docs
- **ReDoc Documentation**: http://localhost:8000/redoc
- **Health Check**: http://localhost:8000/health

## Usage

### 1. Add Cloud Provider

```bash
curl -X POST "http://localhost:8000/api/providers" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "My OpenStack",
    "provider_type": "openstack",
    "credentials": {
      "auth_url": "https://openstack.example.com:5000/v3",
      "username": "admin",
      "password": "secret",
      "project_name": "demo",
      "user_domain_name": "Default",
      "project_domain_name": "Default"
    },
    "regions": ["RegionOne"]
  }'
```

### 2. Sync Instances

```bash
curl -X POST "http://localhost:8000/api/providers/{provider_id}/sync"
```

### 3. List Instances

```bash
curl "http://localhost:8000/api/instances"
```

### 4. Natural Language Query (AI)

```bash
curl -X POST "http://localhost:8000/api/ai/query" \
  -H "Content-Type: application/json" \
  -d '{
    "query": "Show me all instances that cost more than $100 per month"
  }'
```

### 5. Cost Forecast (AI)

```bash
curl "http://localhost:8000/api/ai/forecast?days=30"
```

### 6. Anomaly Detection (AI)

```bash
curl -X POST "http://localhost:8000/api/ai/anomalies/detect/{instance_id}?metric_type=cpu"
```

## API Endpoints

### Providers
- `POST /api/providers` - Add cloud provider
- `GET /api/providers` - List providers
- `GET /api/providers/{id}` - Get provider details
- `PUT /api/providers/{id}` - Update provider
- `DELETE /api/providers/{id}` - Delete provider
- `POST /api/providers/{id}/test` - Test connection
- `POST /api/providers/{id}/sync` - Sync instances

### Instances
- `GET /api/instances` - List instances (with filters)
- `GET /api/instances/{id}` - Get instance details
- `GET /api/instances/stats` - Get aggregate statistics
- `POST /api/instances/{id}/refresh` - Refresh instance data
- `POST /api/instances/{id}/start` - Start instance
- `POST /api/instances/{id}/stop` - Stop instance

### AI Features
- `POST /api/ai/query` - Natural language query
- `GET /api/ai/anomalies` - List detected anomalies
- `POST /api/ai/anomalies/detect/{instance_id}` - Run anomaly detection
- `POST /api/ai/anomalies/{id}/resolve` - Mark anomaly as resolved
- `GET /api/ai/forecast` - Get cost forecast
- `GET /api/ai/insights` - Get AI-generated insights

## Architecture

```
┌─────────────────────────────────────┐
│         Frontend UI                 │
│  - Dashboard                        │
│  - Instance Management              │
│  - AI Chat Interface                │
└────────────┬────────────────────────┘
             │ REST API
             │
┌────────────▼────────────────────────┐
│      Backend (FastAPI)              │
├─────────────────────────────────────┤
│  ┌──────────────┐  ┌─────────────┐ │
│  │  API Routers │  │ AI Services │ │
│  └──────────────┘  └─────────────┘ │
│  ┌──────────────┐  ┌─────────────┐ │
│  │   Services   │  │   Cache     │ │
│  └──────────────┘  └─────────────┘ │
└────────────┬────────────────────────┘
             │
┌────────────▼────────────────────────┐
│    Cloud Provider Adapters          │
│  - OpenStack  - AWS  - Azure        │
└─────────────────────────────────────┘
```

## AI Features Details

### Natural Language Query
Ask questions about your infrastructure in plain English:
- "What's my most expensive resource?"
- "Show me instances in AWS us-east-1"
- "Which instances have been running for more than 90 days?"

### Anomaly Detection
ML-based detection using Isolation Forest algorithm:
- Detects unusual patterns in CPU, memory, cost, and network usage
- Severity classification (Critical, Warning, Info)
- Root cause suggestions and recommended actions

### Cost Forecasting
Predictive analysis using Facebook Prophet:
- Forecast costs for 7, 30, or 90 days
- Confidence intervals and trend analysis
- Budget overrun alerts
- "What-if" scenario planning

## Development

### Project Structure

```
Cloud-Resource-Manager/
├── backend/
│   ├── app/
│   │   ├── __init__.py
│   │   ├── main.py              # FastAPI application
│   │   ├── config.py            # Configuration
│   │   ├── database.py          # Database setup
│   │   ├── models/              # SQLAlchemy models
│   │   ├── schemas/             # Pydantic schemas
│   │   ├── routers/             # API endpoints
│   │   ├── services/            # Business logic
│   │   ├── adapters/            # Cloud provider adapters
│   │   ├── ai/                  # AI/ML services
│   │   └── utils/               # Utilities
│   ├── requirements.txt
│   └── Dockerfile
├── frontend/                    # To be implemented
├── docker-compose.yml
└── README.md
```

### Running Tests

```bash
cd backend
pytest
```

### Code Quality

```bash
# Format code
black app/

# Lint
flake8 app/

# Type checking
mypy app/
```

## Configuration

### Environment Variables

Key environment variables (see `.env.example` for full list):

```bash
# AI/ML
ANTHROPIC_API_KEY=sk-ant-xxxxx
ENABLE_NL_QUERY=true
ENABLE_ANOMALY_DETECTION=true
ENABLE_ML_RECOMMENDATIONS=true
ENABLE_COST_FORECASTING=true

# ML Settings
ML_MODEL_RETRAIN_DAYS=7
ANOMALY_DETECTION_SENSITIVITY=0.1
MIN_TRAINING_DAYS=30

# Database
DATABASE_URL=sqlite:///./cloud_manager.db

# Redis
REDIS_URL=redis://localhost:6379
```

## Deployment

### Docker Deployment

```bash
# Build and start all services
docker-compose up -d

# View logs
docker-compose logs -f

# Stop services
docker-compose down

# Rebuild after code changes
docker-compose up -d --build
```

### Production Considerations

1. **Database**: Use PostgreSQL instead of SQLite
2. **Security**:
   - Change SECRET_KEY and ENCRYPTION_KEY
   - Use strong passwords
   - Enable HTTPS
3. **Scaling**:
   - Use Redis for caching
   - Consider Celery for background tasks
4. **Monitoring**: Set up logging and monitoring

## Troubleshooting

### Common Issues

**Issue**: "ANTHROPIC_API_KEY not set"
- Solution: Set your Anthropic API key in `.env`

**Issue**: "Failed to connect to OpenStack"
- Solution: Verify your credentials and auth_url

**Issue**: "Redis connection failed"
- Solution: Ensure Redis is running (`docker-compose up redis`)

**Issue**: "Insufficient data for ML training"
- Solution: Need at least 30 days of metrics data for anomaly detection

## Roadmap

### Phase 1 (Current)
- ✅ Multi-cloud provider management
- ✅ Instance discovery and monitoring
- ✅ Natural language query interface
- ✅ Anomaly detection
- ✅ Cost forecasting

### Phase 2 (Planned)
- [ ] Frontend React application
- [ ] Real-time metrics collection
- [ ] Enhanced ML recommendations
- [ ] Billing and cost breakdown
- [ ] Email/Slack notifications

### Phase 3 (Future)
- [ ] Kubernetes support
- [ ] Automated optimization
- [ ] Multi-user and teams
- [ ] Mobile app
- [ ] Advanced AI insights

## Contributing

Contributions are welcome! Please:
1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Submit a pull request

## License

MIT License - see LICENSE file for details

## Support

For issues, questions, or feature requests, please open an issue on GitHub.

## Acknowledgments

- Built with [FastAPI](https://fastapi.tiangolo.com/)
- AI powered by [Anthropic Claude](https://www.anthropic.com/)
- ML models using [scikit-learn](https://scikit-learn.org/) and [Prophet](https://facebook.github.io/prophet/)
- Cloud SDKs: OpenStack SDK, AWS Boto3, Azure SDK

---

**Built for AI Hackathon** 🚀

This platform demonstrates how AI can transform traditional cloud management from reactive dashboards to proactive, predictive, and conversational infrastructure management.
