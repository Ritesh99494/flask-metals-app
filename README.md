# Metal Prices Dashboard

A Flask application that displays real-time metal prices (Gold, Silver, Platinum) using the Alpha Vantage API.

## Features

- Real-time metal prices from Alpha Vantage API
- Historical price data visualization
- Price trend predictions
- Investment return calculator
- Responsive design

## Setup Instructions

### 1. Clone the repository

\`\`\`bash
git clone https://github.com/Ritesh99494/flask-metals-app.git
cd metal-prices-dashboard
\`\`\`

### 2. Create a virtual environment

\`\`\`bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
\`\`\`

### 3. Install dependencies

\`\`\`bash
pip install -r requirements.txt
\`\`\`

### 4. Get an Alpha Vantage API Key

1. Visit [Alpha Vantage](https://www.alphavantage.co/support/#api-key)
2. Sign up for a free API key

### 5. Set up environment variables

Create a `.env` file in the root directory:

\`\`\`
ALPHA_VANTAGE_API_KEY=your_api_key_here
\`\`\`

Or set the environment variable directly:

\`\`\`bash
# On Linux/Mac
export ALPHA_VANTAGE_API_KEY=your_api_key_here

# On Windows
set ALPHA_VANTAGE_API_KEY=your_api_key_here
\`\`\`

### 6. Run the application

\`\`\`bash
python app.py
\`\`\`

Visit `http://127.0.0.1:5000/` in your browser.

## Deployment on Vercel

1. Make sure you have the `vercel.json` file in your project
2. Set up the environment variable in Vercel dashboard
3. Deploy using the Vercel CLI or GitHub integration

## API Endpoints

- `/api/prices` - Get current metal prices
- `/api/historical` - Get historical price data
- `/api/status` - Check API status

## Notes

- The free tier of Alpha Vantage API has rate limits (typically 5 calls per minute and 500 calls per day)
- If no API key is provided, the application will run in demo mode with mock data
- The application includes caching to minimize API calls
