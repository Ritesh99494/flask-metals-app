from flask import Flask, render_template, request, jsonify
import json
import os
from datetime import datetime, timedelta
import math
import random
import requests
import time

app = Flask(__name__)

# Cache for API responses to avoid rate limiting
cache = {
    'live_prices': {'data': None, 'timestamp': 0},
    'historical_data': {'data': None, 'timestamp': 0}
}

# Cache duration in seconds (15 minutes)
CACHE_DURATION = 900

def get_api_key():
    """Get API key from environment variable or return demo key"""
    api_key = os.environ.get('ALPHA_VANTAGE_API_KEY')
    if not api_key:
        # If no API key is provided, use a demo key with limited functionality
        print("Warning: No API key found. Using demo mode with limited functionality.")
        api_key = 'f65a0664489caab380348b6f6e2a3076'
    return api_key

def get_live_prices():
    """Get current metal prices from Alpha Vantage API"""
    # Check cache first
    current_time = time.time()
    if cache['live_prices']['data'] and current_time - cache['live_prices']['timestamp'] < CACHE_DURATION:
        return cache['live_prices']['data']
    
    api_key = get_api_key()
    prices = {}
    metals = {
        'gold': 'XAU',
        'silver': 'XAG',
        'Platinum': 'XPT'
    }
    
    try:
        # Get gold and silver prices (forex endpoint)
        for metal_name, symbol in metals.items():
            if metal_name in ['gold', 'silver']:
                # Gold and silver use forex endpoint
                url = f'https://api.metalpriceapi.com/v1/latest?api_key=f65a0664489caab380348b6f6e2a3076&base=USD&currencies=XAU,XAG'
            else:
                # Platinum uses commodities endpoint
                url = f'https://api.metalpriceapi.com/v1/latest?api_key=f65a0664489caab380348b6f6e2a3076&base=USD&currencies=XPT'
            
            response = requests.get(url)
            data = response.json()
            
            if metal_name in ['gold', 'silver'] and 'Realtime Currency Exchange Rate' in data:
                # Extract price from forex response
                exchange_data = data['Realtime Currency Exchange Rate']
                price = float(exchange_data['5. Exchange Rate'])
                prices[metal_name] = round(price, 2)
            elif metal_name == 'Platinum' and 'data' in data:
                # Extract price from commodities response
                price = float(data['data'][0]['value'])
                prices[metal_name] = round(price, 2)
            else:
                # If API fails, use fallback prices
                fallback_prices = {'gold': 2050.75, 'silver': 26.15, 'Platinum': 3.95}
                prices[metal_name] = fallback_prices[metal_name]
                print(f"Warning: Could not get {metal_name} price from API. Using fallback price.")
            
            # Add a small delay to avoid hitting rate limits
            time.sleep(0.5)
        
        # Add timestamp
        prices['date'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        
        # Update cache
        cache['live_prices'] = {
            'data': prices,
            'timestamp': current_time
        }
        
        return prices
    
    except Exception as e:
        print(f"Error fetching live prices: {str(e)}")
        # Fallback to mock data if API fails
        fallback_prices = {
            'gold': 2050.75,
            'silver': 26.15,
            'Platinum': 3.95,
            'date': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        }
        return fallback_prices

def get_historical_data(days=30):
    """Get historical price data from Alpha Vantage API"""
    # Check cache first
    current_time = time.time()
    if cache['historical_data']['data'] and current_time - cache['historical_data']['timestamp'] < CACHE_DURATION:
        return cache['historical_data']['data']
    
    api_key = get_api_key()
    
    # Define metals and their symbols
    metals = {
        'gold': 'XAU',
        'silver': 'XAG',
        'Platinum': 'XPT'
    }
    
    try:
        historical_data = []
        today = datetime.now()
        
        # For each metal, get time series data
        metal_data = {}
        
        for metal_name, symbol in metals.items():
            if metal_name in ['gold', 'silver']:
                # Gold and silver use forex endpoint with USD
                url = f'https://api.metalpriceapi.com/v1/latest?api_key=f65a0664489caab380348b6f6e2a3076&base=USD&currencies=XAU,XAG'
            else:
                # Platinum uses commodities endpoint
                url = f'https://api.metalpriceapi.com/v1/latest?api_key=f65a0664489caab380348b6f6e2a3076&base=USD&currencies=XPT'
            
            response = requests.get(url)
            data = response.json()
            
            # Extract time series data
            if metal_name in ['gold', 'silver'] and 'Time Series FX (Daily)' in data:
                time_series = data['Time Series FX (Daily)']
                metal_data[metal_name] = {date: float(values['4. close']) for date, values in time_series.items()}
            elif metal_name == 'Platinum' and 'data' in data:
                time_series = data['data']
                metal_data[metal_name] = {item['date']: float(item['value']) for item in time_series}
            else:
                # If API fails, generate mock data
                print(f"Warning: Could not get historical {metal_name} data from API. Using generated data.")
                return generate_historical_data(days)
            
            # Add a small delay to avoid hitting rate limits
            time.sleep(1)
        
        # Combine data for all metals
        all_dates = set()
        for metal in metal_data.values():
            all_dates.update(metal.keys())
        
        # Sort dates
        sorted_dates = sorted(all_dates)[-days:]
        
        # Create combined dataset
        for date in sorted_dates:
            entry = {'date': date}
            for metal_name in metals.keys():
                if date in metal_data[metal_name]:
                    entry[metal_name] = round(metal_data[metal_name][date], 2)
                else:
                    # If data is missing for this date, use previous day's data
                    prev_dates = [d for d in sorted_dates if d < date]
                    if prev_dates:
                        prev_date = prev_dates[-1]
                        if prev_date in metal_data[metal_name]:
                            entry[metal_name] = round(metal_data[metal_name][prev_date], 2)
                        else:
                            # Fallback values if no previous data
                            fallback_values = {'gold': 2000, 'silver': 25, 'Platinum': 4}
                            entry[metal_name] = fallback_values[metal_name]
                    else:
                        # Fallback values if no previous data
                        fallback_values = {'gold': 2000, 'silver': 25, 'Platinum': 4}
                        entry[metal_name] = fallback_values[metal_name]
            
            historical_data.append(entry)
        
        # Update cache
        cache['historical_data'] = {
            'data': historical_data,
            'timestamp': current_time
        }
        
        return historical_data
    
    except Exception as e:
        print(f"Error fetching historical data: {str(e)}")
        # Fallback to generated data if API fails
        return generate_historical_data(days)

def generate_historical_data(days=30):
    """Generate mock historical price data as fallback"""
    data = []
    today = datetime.now()
    
    # Base prices
    gold_base = 2000
    silver_base = 26
    Platinum_base = 4
    
    # Set seed for reproducibility
    random.seed(42)
    
    for i in range(days):
        date = (today - timedelta(days=days-i-1)).strftime('%Y-%m-%d')
        
        # Create realistic price movements with some randomness
        gold_change = (random.random() - 0.5) * 20  # +/- $10
        silver_change = (random.random() - 0.5) * 1  # +/- $0.5
        Platinum_change = (random.random() - 0.5) * 0.2  # +/- $0.1
        
        # Apply changes with some trend
        trend_factor = math.sin(i/10) * 0.5 + 0.5  # Creates a wave pattern
        gold_price = gold_base + gold_change + (i * 0.5 * trend_factor)
        silver_price = silver_base + silver_change + (i * 0.05 * trend_factor)
        Platinum_price = Platinum_base + Platinum_change + (i * 0.01 * trend_factor)
        
        data.append({
            'date': date,
            'gold': round(gold_price, 2),
            'silver': round(silver_price, 2),
            'Platinum': round(Platinum_price, 2)
        })
    
    return data

def predict_prices(historical_data):
    """Simple prediction based on recent trend"""
    if not historical_data:
        return {'gold': 0, 'silver': 0, 'Platinum': 0}
    
    # Get the last 7 days of data
    recent_data = historical_data[-7:]
    
    predictions = {}
    for metal in ['gold', 'silver', 'Platinum']:
        # Calculate average daily change
        changes = []
        for i in range(1, len(recent_data)):
            change = recent_data[i][metal] - recent_data[i-1][metal]
            changes.append(change)
        
        avg_change = sum(changes) / len(changes) if changes else 0
        
        # Predict next price based on last price + average change
        last_price = recent_data[-1][metal]
        predicted_price = last_price + avg_change
        
        predictions[metal] = round(predicted_price, 2)
    
    return predictions

def calculate_investment_return(initial_amount, years, current_prices, growth_rates):
    """Calculate expected investment returns"""
    results = {}
    
    for metal in ['gold', 'silver', 'Platinum']:
        # Calculate compound growth
        current_price = current_prices[metal]
        annual_growth = growth_rates[metal]
        
        # Future value calculation
        future_value = initial_amount * ((1 + annual_growth) ** years)
        
        # Units purchased
        units = initial_amount / current_price
        
        # Future value based on units
        future_price = current_price * ((1 + annual_growth) ** years)
        future_value_units = units * future_price
        
        results[metal] = {
            'initial_investment': round(initial_amount, 2),
            'units_purchased': round(units, 4),
            'future_value': round(future_value_units, 2),
            'total_return': round(future_value_units - initial_amount, 2),
            'percent_return': round(((future_value_units / initial_amount) - 1) * 100, 2)
        }
    
    return results

def estimate_growth_rates(data):
    """Calculate growth rates for each metal from historical data"""
    if len(data) < 2:
        return {'gold': 0, 'silver': 0, 'Platinum': 0}

    first = data[0]
    last = data[-1]
    growth_rates = {}

    for metal in ['gold', 'silver', 'Platinum']:
        start_price = first[metal]
        end_price = last[metal]
        start_date = datetime.strptime(first['date'], '%Y-%m-%d')
        last_date = datetime.strptime(last['date'], '%Y-%m-%d')

        years = (last_date - start_date).days / 365.0
        if years == 0 or start_price == 0:
            growth_rates[metal] = 0
        else:
            cagr = ((end_price / start_price) ** (1 / years)) - 1
            growth_rates[metal] = round(cagr, 4)

    return growth_rates



@app.route('/', methods=['GET', 'POST'])
def index():
    # Get current prices
    live_prices = get_live_prices()
    
    # Get historical data
    historical_data = get_historical_data(30)  # 30 days of data
    
    # Predict future prices
    predictions = predict_prices(historical_data)
    
    # Estimate growth rates
    growth_rates = estimate_growth_rates(historical_data)
    
    # Process investment calculation if form submitted
    investment_result = None
    if request.method == 'POST':
        try:
            amount = float(request.form['amount'])
            years = int(request.form['years'])
            
            if amount <= 0 or years <= 0:
                investment_result = {'error': 'Amount and years must be positive numbers'}
            else:
                investment_result = calculate_investment_return(
                    amount, years, live_prices, growth_rates
                )
        except ValueError:
            investment_result = {'error': 'Invalid input. Please enter valid numbers.'}
        except Exception as e:
            investment_result = {'error': f'An error occurred: {str(e)}'}
    
    # Prepare chart data
    chart_data = {
        'dates': [item['date'] for item in historical_data],
        'gold': [item['gold'] for item in historical_data],
        'silver': [item['silver'] for item in historical_data],
        'Platinum': [item['Platinum'] for item in historical_data]
    }
    
    return render_template('index.html', 
                          prices=live_prices,
                          predictions=predictions,
                          table=historical_data[-10:],  # Last 10 days
                          investment_result=investment_result,
                          chart_data=json.dumps(chart_data),
                          growth_rates={k: round(v*100, 2) for k, v in growth_rates.items()},
                          api_status="Live" if get_api_key() != "demo" else "Demo")

@app.route('/api/prices')
def api_prices():
    """API endpoint for current prices"""
    return jsonify(get_live_prices())

@app.route('/api/historical')
def api_historical():
    """API endpoint for historical data"""
    days = request.args.get('days', default=30, type=int)
    return jsonify(get_historical_data(days))

@app.route('/api/status')
def api_status():
    """API endpoint for checking API status"""
    api_key = get_api_key()
    status = {
        'status': 'ok',
        'mode': 'Live' if api_key != 'demo' else 'Demo',
        'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    }
    return jsonify(status)

if __name__ == '__main__':
    app.run(debug=True)
