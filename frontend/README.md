# Cloud Resource Manager - Frontend

Modern React frontend for the Cloud Resource Manager with AI capabilities.

## Features

- **Dashboard**: Overview of your multi-cloud infrastructure
- **Provider Management**: Add, test, and sync cloud providers
- **Instance Management**: View, filter, and control instances
- **AI Chat**: Natural language queries about your infrastructure
- **Cost Forecast**: ML-powered cost predictions
- **Anomaly Detection**: Real-time alerts for unusual patterns

## Quick Start

### Prerequisites

- Node.js 16+ and npm
- Backend server running on http://localhost:8000

### Installation

```bash
# Install dependencies
npm install

# Create environment file
cp .env.example .env

# Start development server
npm start
```

The application will open at http://localhost:3000

### Build for Production

```bash
npm run build
```

The production build will be in the `build/` directory.

## Technology Stack

- **React 18** with TypeScript
- **Tailwind CSS** for styling
- **React Router** for navigation
- **Chart.js** for data visualization
- **Axios** for API communication

## Project Structure

```
frontend/
├── public/              # Static files
├── src/
│   ├── components/      # React components
│   │   ├── Dashboard.tsx
│   │   ├── Providers.tsx
│   │   ├── Instances.tsx
│   │   ├── AIChat.tsx
│   │   ├── CostForecast.tsx
│   │   └── Anomalies.tsx
│   ├── services/        # API client
│   │   └── api.ts
│   ├── App.tsx         # Main app component
│   ├── index.tsx       # Entry point
│   └── index.css       # Global styles
├── package.json
└── tailwind.config.js
```

## Available Pages

- `/` - Dashboard overview
- `/providers` - Cloud provider management
- `/instances` - Instance list and management
- `/ai-chat` - AI-powered chat interface
- `/forecast` - Cost forecasting
- `/anomalies` - Anomaly detection alerts

## Environment Variables

Create a `.env` file:

```
REACT_APP_API_URL=http://localhost:8000/api
```

## Development

### Running Tests

```bash
npm test
```

### Linting

```bash
npm run lint
```

## Deployment

### Docker

```bash
# Build Docker image
docker build -t cloud-manager-frontend .

# Run container
docker run -p 3000:80 cloud-manager-frontend
```

### Static Hosting

Build the app and deploy the `build/` directory to any static hosting service:

- Vercel
- Netlify
- AWS S3 + CloudFront
- GitHub Pages

## Key Features Explained

### AI Chat
The AI chat interface allows you to ask questions in natural language:
- "What is my total monthly cost?"
- "Show me expensive instances"
- "Find idle resources"

### Cost Forecast
Uses time series analysis to predict future costs based on historical patterns with confidence intervals.

### Anomaly Detection
ML-powered detection of unusual patterns in resource usage with severity classification and recommended actions.

## Troubleshooting

### "Cannot connect to backend"
- Ensure backend is running on http://localhost:8000
- Check REACT_APP_API_URL in .env file
- Verify CORS is enabled in backend

### "Build fails"
- Delete node_modules and package-lock.json
- Run `npm install` again
- Check Node.js version (16+ required)

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Submit a pull request

## License

MIT
