import React, { useState, useEffect } from 'react';
import './App.css';

console.log('=== DEBUG INFO ===');
console.log('NODE_ENV:', process.env.NODE_ENV);
console.log('REACT_APP_API_URL:', process.env.REACT_APP_API_URL);
console.log('API_BASE_URL will be:', process.env.REACT_APP_API_URL || 'http://localhost:8001');

// API Base URL - uses environment variable or defaults to localhost
const API_BASE_URL = process.env.REACT_APP_API_URL || 'http://localhost:8001';

function App() {
  const [minStrategies, setMinStrategies] = useState(2);
  const [results, setResults] = useState(null);
  const [loading, setLoading] = useState(false);
  const [serverStatus, setServerStatus] = useState(null);
  const [refreshing, setRefreshing] = useState(false);
  

  // Check server status on mount
  useEffect(() => {
    checkServerStatus();
  }, []);

  const checkServerStatus = async () => {
    try {
      const response = await fetch(`${API_BASE_URL}/status`);
      const data = await response.json();
      setServerStatus(data);
    } catch (error) {
      console.error('Status check error:', error);
    }
  };

  const handleSearch = async () => {
    setLoading(true);
    
    try {
      const response = await fetch(`${API_BASE_URL}/search`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          min_strategies: minStrategies
        })
      });
      
      const data = await response.json();
      setResults(data);
      
      // Update server status after search
      await checkServerStatus();
    } catch (err) {
      console.error('Search error:', err);
      setResults({
        success: false,
        message: 'Failed to fetch data',
        data: [],
        total: 0
      });
    } finally {
      setLoading(false);
    }
  };

  const handleRefreshCache = async () => {
    if (refreshing) return;
    
    setRefreshing(true);
    
    try {
      const response = await fetch(`${API_BASE_URL}/refresh-cache`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        }
      });
      
      const data = await response.json();
      if (data.success) {
        // Update server status after refresh
        setTimeout(() => {
          checkServerStatus();
        }, 1000);
      }
    } catch (error) {
      console.error('Error refreshing cache:', error);
    } finally {
      setRefreshing(false);
    }
  };



  return (
    <div className="app">
      {/* Left Panel - Controls */}
      <div className="left-panel">
        <div className="control-section">
          
          {/* Header */}
          <div className="panel-header">
            <h2>CONTROL PANEL</h2>
            <div className="status-indicator">
              <span className="status-dot"></span>
              <span>ONLINE</span>
            </div>
          </div>

          {/* Strategy Configuration */}
          <div className="config-section">
            <h3>STRATEGY FILTER</h3>
            <div className="strategies-control">
              <label>Minimum Strategies</label>
              <div className="slider-container">
                <input
                  type="range"
                  min="2"
                  max="7"
                  value={minStrategies}
                  onChange={(e) => setMinStrategies(parseInt(e.target.value))}
                  className="strategy-slider"
                />
                <div className="slider-value">{minStrategies}</div>
              </div>
              <div className="slider-labels">
                <span>2</span>
                <span>3</span>
                <span>4</span>
                <span>5</span>
                <span>6</span>
                <span>7</span>
              </div>
            </div>
          </div>

          {/* System Status */}
          <div className="system-status">
            <h3>SYSTEM STATUS</h3>
            <div className="status-grid">
              <div className="status-item">
                <span className="status-label">CACHE SIZE</span>
                <span className="status-value">{serverStatus?.cache_size || 0}</span>
              </div>
              <div className="status-item">
                <span className="status-label">CACHED STRATEGIES</span>
                <span className="status-value">{serverStatus?.cached_strategies.length || 0}</span>
              </div>
              <div className="status-item">
                <span className="status-label">LAST UPDATE</span>
                <span className="status-value">
                  {serverStatus?.last_updated ? 
                    new Date(serverStatus.last_updated).toLocaleTimeString() : 
                    'N/A'
                  }
                </span>
              </div>
            </div>
          </div>

          {/* Cache Status */}
          {serverStatus && (
            <div className="cache-status">
              <h3>CACHE STATUS</h3>
              {serverStatus.cached_strategies.includes(minStrategies) ? (
                <span className="cache-indicator cached">⚡ DATA CACHED</span>
              ) : (
                <span className="cache-indicator not-cached">🔄 WILL FETCH FRESH</span>
              )}
              {serverStatus.is_loading && (
                <span className="background-loading">📊 PRE-LOADING STRATEGIES...</span>
              )}
              <div className="cache-info">
                <span className="cache-refresh-info">🕐 Auto-refresh every 3 hours</span>
              </div>
            </div>
          )}
          
          {/* Action Buttons */}
          <div className="action-buttons">
            <button 
              onClick={handleSearch}
              disabled={loading}
              className="search-btn"
            >
              {loading ? 'SCANNING...' : 'EXECUTE SCAN'}
            </button>
            <button 
              onClick={handleRefreshCache}
              disabled={refreshing || serverStatus?.is_loading}
              className="refresh-btn"
              title="Refresh cache data"
            >
              {refreshing ? '🔄 REFRESHING...' : '🔄 REFRESH CACHE'}
            </button>
          </div>

          {/* Quick Stats */}
          {results && results.success && (
            <div className="quick-stats">
              <h3>SCAN RESULTS</h3>
              <div className="stats-grid">
                <div className="stat-item">
                  <span className="stat-number">{results.total}</span>
                  <span className="stat-label">STOCKS FOUND</span>
                </div>
                <div className="stat-item">
                  <span className="stat-number">{minStrategies}+</span>
                  <span className="stat-label">MIN STRATEGIES</span>
                </div>
              </div>
            </div>
          )}
        </div>
      </div>

      {/* Center Panel - Data */}
      <div className="center-panel">
        {results ? (
          <div className="results">
            <div className="results-header">
              <span className="results-count">{results.total} stocks found</span>
              {results.from_cache && (
                <span className="cache-badge">⚡ Cached</span>
              )}
            </div>
            
            {results.success && results.data.length > 0 ? (
              <div className="data-table">
                <table>
                  <thead>
                    <tr>
                      <th>Stock</th>
                      <th>Price</th>
                      <th>Strategies</th>
                      <th>Count</th>
                    </tr>
                  </thead>
                  <tbody>
                    {results.data.map((stock, index) => (
                      <tr key={index}>
                        <td className="stock-name">{stock.Name}</td>
                        <td className="stock-price">₹{stock['CMPRs.'] || '-'}</td>
                        <td className="stock-strategies">
                          {stock.Strategies && stock.Strategies.split(',').map((strategy, i) => (
                            <span key={i} className="strategy-tag">{strategy.trim()}</span>
                          ))}
                        </td>
                        <td className="strategy-count">{stock.Strategies_Count}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            ) : (
              <div className="no-results">
                <p>{results.message || 'No stocks found'}</p>
              </div>
            )}
          </div>
        ) : (
          <div className="welcome">
            <p>Select minimum strategies and search to view results</p>
          </div>
        )}
      </div>

      {/* Right Panel - Strategy Guide */}
      <div className="right-panel">
        <div className="strategy-guide">
          <div className="guide-header">
            <h2>STRATEGY GUIDE</h2>
            <div className="guide-status">
              <span className="guide-dot"></span>
              <span>7 ACTIVE</span>
            </div>
          </div>
          
          <div className="strategies-list">
            <div className="strategy-item">
              <div className="strategy-code">S1</div>
              <div className="strategy-info">
                <div className="strategy-name">Daily Volume + RSI + Moving Averages</div>
                <div className="strategy-desc">Technical analysis combining volume, RSI momentum, and MA trends</div>
              </div>
            </div>
            
            <div className="strategy-item">
              <div className="strategy-code">S2</div>
              <div className="strategy-info">
                <div className="strategy-name">Price Action + RSI + Moving Averages</div>
                <div className="strategy-desc">Price movement patterns with RSI and MA confirmation</div>
              </div>
            </div>
            
            <div className="strategy-item">
              <div className="strategy-code">S3</div>
              <div className="strategy-info">
                <div className="strategy-name">FII Holding Strategy</div>
                <div className="strategy-desc">Foreign Institutional Investor holding pattern analysis</div>
              </div>
            </div>
            
            <div className="strategy-item">
              <div className="strategy-code">S4</div>
              <div className="strategy-info">
                <div className="strategy-name">Volume + RSI + FII Based Analysis</div>
                <div className="strategy-desc">Combined volume, momentum, and institutional activity</div>
              </div>
            </div>
            
            <div className="strategy-item">
              <div className="strategy-code">S5</div>
              <div className="strategy-info">
                <div className="strategy-name">SEPA-Based Screen</div>
                <div className="strategy-desc">Systematic Equity Performance Analysis framework</div>
              </div>
            </div>
            
            <div className="strategy-item">
              <div className="strategy-code">S6A</div>
              <div className="strategy-info">
                <div className="strategy-name">MACD Bearish Convergence</div>
                <div className="strategy-desc">MACD indicator detecting bearish momentum signals</div>
              </div>
            </div>
            
            <div className="strategy-item">
              <div className="strategy-code">S6B</div>
              <div className="strategy-info">
                <div className="strategy-name">MACD Bullish Convergence</div>
                <div className="strategy-desc">MACD indicator detecting bullish momentum signals</div>
              </div>
            </div>
          </div>
          

        </div>
      </div>
    </div>
  );
}

export default App;
