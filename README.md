# Finance Agent - Stock Screener

A web app that finds stocks appearing in multiple trading strategies by scraping Screener.in.

## What it does

- Scrapes stock data from 7 different trading strategies
- Shows you stocks that appear in multiple strategies (higher confluence = potentially better opportunities)
- Clean, dark-themed UI with real-time data

## Quick Setup

**Backend:**
```bash
cd backend
pip install -r requirements.txt
python api.py
```

**Frontend:**
```bash
cd frontend
npm install
npm start
```

Then go to `http://localhost:3000`

## How to use

1. Set minimum strategies (2-7) with the slider
2. Click "Execute Scan" 
3. See results in the table
4. Higher strategy count = more confluence

## Strategies

- **S1**: Daily Volume + RSI + Moving Averages
- **S2**: Price Action + RSI + Moving Averages  
- **S3**: FII Holding Strategy
- **S4**: Volume + RSI + FII Based Analysis
- **S5**: SEPA-Based Screen
- **S6A**: MACD Bearish Convergence
- **S6B**: MACD Bullish Convergence

## Features

- ⚡ Auto-caching for faster results
- 🔄 Auto-refresh every 3 hours
- 📱 Mobile-friendly design
- 🎨 Professional dark theme

That's it! Pretty straightforward. 