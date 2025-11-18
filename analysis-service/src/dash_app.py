from dash import Dash, dcc, html, Input, Output, ClientsideFunction
import requests
from fastapi import FastAPI
from starlette.middleware.wsgi import WSGIMiddleware
import json

def mount_dash(fastapi_app: FastAPI):
    dash_app = Dash(__name__)
    
    # Modern styling
    dash_app.index_string = '''
    <!DOCTYPE html>
    <html>
        <head>
            {%metas%}
            <title>{%title%}</title>
            {%favicon%}
            {%css%}
            <style>
                * {
                    margin: 0;
                    padding: 0;
                    box-sizing: border-box;
                }
                body {
                    font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif;
                    background: linear-gradient(135deg, #0a0e27 0%, #1a1f3a 25%, #16213e 50%, #0f3460 75%, #0a1929 100%);
                    background-size: 400% 400%;
                    animation: gradientShift 20s ease infinite;
                    min-height: 100vh;
                    padding: 20px;
                    position: relative;
                    overflow-x: hidden;
                }
                body::before {
                    content: '';
                    position: fixed;
                    top: 0;
                    left: 0;
                    right: 0;
                    bottom: 0;
                    background: 
                        radial-gradient(circle at 20% 30%, rgba(0, 255, 255, 0.15) 0%, transparent 50%),
                        radial-gradient(circle at 80% 70%, rgba(147, 51, 234, 0.15) 0%, transparent 50%),
                        radial-gradient(circle at 50% 50%, rgba(59, 130, 246, 0.1) 0%, transparent 60%);
                    pointer-events: none;
                    z-index: 0;
                }
                @keyframes gradientShift {
                    0% { background-position: 0% 50%; }
                    50% { background-position: 100% 50%; }
                    100% { background-position: 0% 50%; }
                }
                .dashboard-container {
                    max-width: 1400px;
                    margin: 0 auto;
                    background: rgba(15, 23, 42, 0.85);
                    backdrop-filter: blur(20px);
                    border-radius: 24px;
                    box-shadow: 
                        0 20px 60px rgba(0, 0, 0, 0.5),
                        0 0 0 1px rgba(0, 255, 255, 0.1),
                        0 0 40px rgba(0, 255, 255, 0.1);
                    overflow: hidden;
                    position: relative;
                    z-index: 1;
                    animation: slideUp 0.6s ease-out;
                }
                @keyframes slideUp {
                    from {
                        opacity: 0;
                        transform: translateY(30px);
                    }
                    to {
                        opacity: 1;
                        transform: translateY(0);
                    }
                }
                .dashboard-header {
                    background: linear-gradient(135deg, #0ea5e9 0%, #3b82f6 25%, #8b5cf6 50%, #a855f7 75%, #ec4899 100%);
                    background-size: 300% 300%;
                    animation: gradientShift 8s ease infinite;
                    color: white;
                    padding: 40px 50px;
                    display: flex;
                    justify-content: space-between;
                    align-items: center;
                    position: relative;
                    overflow: hidden;
                    box-shadow: 0 4px 30px rgba(0, 255, 255, 0.3), inset 0 1px 0 rgba(255, 255, 255, 0.1);
                }
                .dashboard-header::before {
                    content: '';
                    position: absolute;
                    top: -50%;
                    right: -50%;
                    width: 200%;
                    height: 200%;
                    background: radial-gradient(circle, rgba(0, 255, 255, 0.2) 0%, transparent 70%);
                    animation: rotate 15s linear infinite;
                }
                @keyframes rotate {
                    from { transform: rotate(0deg); }
                    to { transform: rotate(360deg); }
                }
                .dashboard-title {
                    font-size: 32px;
                    font-weight: 800;
                    letter-spacing: -1px;
                    position: relative;
                    z-index: 1;
                    text-shadow: 0 2px 10px rgba(0,0,0,0.2);
                }
                .ticker-selector {
                    min-width: 220px;
                    position: relative;
                    z-index: 1;
                }
                .ticker-selector .Select-control,
                .ticker-selector .Select-value,
                .ticker-selector .Select-input {
                    background-color: rgba(0, 255, 255, 0.15) !important;
                    border: 1px solid rgba(0, 255, 255, 0.4) !important;
                    border-radius: 12px !important;
                    color: white !important;
                    font-weight: 600 !important;
                    transition: all 0.3s ease !important;
                    backdrop-filter: blur(10px) !important;
                }
                .ticker-selector .Select-control:hover {
                    background-color: rgba(0, 255, 255, 0.25) !important;
                    border-color: rgba(0, 255, 255, 0.6) !important;
                    box-shadow: 0 4px 20px rgba(0, 255, 255, 0.4) !important;
                }
                .ticker-selector .Select-menu-outer {
                    background-color: #0f172a !important;
                    border-radius: 12px !important;
                    box-shadow: 0 8px 32px rgba(0, 0, 0, 0.6), 0 0 0 1px rgba(0, 255, 255, 0.2) !important;
                    border: none !important;
                    margin-top: 8px !important;
                }
                .ticker-selector .Select-option {
                    color: #e2e8f0 !important;
                    font-weight: 600 !important;
                    padding: 12px 16px !important;
                }
                .ticker-selector .Select-option:hover,
                .ticker-selector .Select-option.is-focused {
                    background-color: rgba(0, 255, 255, 0.2) !important;
                    color: #00ffff !important;
                }
                .ticker-selector .Select-option.is-selected {
                    background: linear-gradient(135deg, #0ea5e9 0%, #8b5cf6 100%) !important;
                    color: white !important;
                }
                .ticker-selector .Select-arrow-zone {
                    color: white !important;
                }
                .dashboard-content {
                    padding: 50px;
                    background: linear-gradient(to bottom, #0f172a 0%, #1e293b 100%);
                }
                .chart-container {
                    background: rgba(15, 23, 42, 0.6);
                    backdrop-filter: blur(10px);
                    border-radius: 16px;
                    padding: 30px;
                    margin-bottom: 30px;
                    box-shadow: 
                        0 8px 32px rgba(0, 0, 0, 0.4),
                        0 0 0 1px rgba(0, 255, 255, 0.2),
                        inset 0 1px 0 rgba(255, 255, 255, 0.05);
                    transition: transform 0.3s ease, box-shadow 0.3s ease;
                    position: relative;
                    overflow: hidden;
                }
                .chart-container::before {
                    content: '';
                    position: absolute;
                    top: 0;
                    left: 0;
                    right: 0;
                    height: 4px;
                    background: linear-gradient(90deg, #00ffff 0%, #0ea5e9 25%, #3b82f6 50%, #8b5cf6 75%, #ec4899 100%);
                    background-size: 200% 100%;
                    animation: gradientShift 3s ease infinite;
                }
                .chart-container:hover {
                    transform: translateY(-4px);
                    box-shadow: 
                        0 12px 40px rgba(0, 0, 0, 0.6),
                        0 0 0 1px rgba(0, 255, 255, 0.4),
                        0 0 30px rgba(0, 255, 255, 0.2);
                }
                .fundamentals-container {
                    display: grid;
                    grid-template-columns: repeat(auto-fit, minmax(280px, 1fr));
                    gap: 24px;
                    margin-top: 30px;
                }
                .metric-card {
                    background: rgba(15, 23, 42, 0.7);
                    backdrop-filter: blur(10px);
                    border-radius: 16px;
                    padding: 28px;
                    box-shadow: 
                        0 8px 24px rgba(0, 0, 0, 0.4),
                        0 0 0 1px rgba(0, 255, 255, 0.15),
                        inset 0 1px 0 rgba(255, 255, 255, 0.05);
                    transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
                    position: relative;
                    overflow: hidden;
                    border: 1px solid rgba(0, 255, 255, 0.15);
                }
                .metric-card::before {
                    content: '';
                    position: absolute;
                    top: 0;
                    left: 0;
                    right: 0;
                    height: 3px;
                    background: linear-gradient(90deg, #00ffff 0%, #0ea5e9 25%, #8b5cf6 50%, #ec4899 100%);
                    background-size: 200% 100%;
                    transform: scaleX(0);
                    transition: transform 0.3s ease;
                    animation: gradientShift 3s ease infinite;
                }
                .metric-card:hover {
                    transform: translateY(-6px) scale(1.02);
                    box-shadow: 
                        0 16px 48px rgba(0, 0, 0, 0.6),
                        0 0 0 1px rgba(0, 255, 255, 0.4),
                        0 0 40px rgba(0, 255, 255, 0.3),
                        inset 0 1px 0 rgba(255, 255, 255, 0.1);
                }
                .metric-card:hover::before {
                    transform: scaleX(1);
                }
                .metric-label {
                    font-size: 11px;
                    color: #94a3b8;
                    text-transform: uppercase;
                    letter-spacing: 1.5px;
                    margin-bottom: 12px;
                    font-weight: 700;
                    display: flex;
                    align-items: center;
                    gap: 8px;
                }
                .metric-icon {
                    font-size: 14px;
                    opacity: 0.8;
                    filter: drop-shadow(0 0 4px rgba(0, 255, 255, 0.5));
                }
                .metric-value {
                    font-size: 32px;
                    font-weight: 800;
                    line-height: 1.2;
                    letter-spacing: -0.5px;
                    background: linear-gradient(135deg, #00ffff 0%, #0ea5e9 25%, #3b82f6 50%, #8b5cf6 75%, #ec4899 100%);
                    background-size: 200% 100%;
                    -webkit-background-clip: text;
                    -webkit-text-fill-color: transparent;
                    background-clip: text;
                    animation: gradientShift 5s ease infinite;
                    filter: drop-shadow(0 0 8px rgba(0, 255, 255, 0.3));
                }
                .metric-value.none {
                    color: #64748b;
                    font-style: italic;
                    -webkit-text-fill-color: #64748b;
                    background: none;
                    filter: none;
                }
                .status-indicator {
                    display: inline-block;
                    width: 12px;
                    height: 12px;
                    border-radius: 50%;
                    margin-right: 10px;
                    background: #00ffff;
                    animation: pulse 2s infinite;
                    box-shadow: 0 0 15px rgba(0, 255, 255, 0.8), 0 0 30px rgba(0, 255, 255, 0.4);
                }
                @keyframes pulse {
                    0%, 100% { 
                        opacity: 1;
                        transform: scale(1);
                    }
                    50% { 
                        opacity: 0.7;
                        transform: scale(1.2);
                    }
                }
                .price-indicator {
                    display: inline-flex;
                    align-items: center;
                    gap: 4px;
                    margin-left: 8px;
                    font-size: 14px;
                    font-weight: 600;
                    text-shadow: 0 0 8px currentColor;
                }
                .price-up {
                    color: #00ff88;
                    filter: drop-shadow(0 0 6px rgba(0, 255, 136, 0.6));
                }
                .price-down {
                    color: #ff0080;
                    filter: drop-shadow(0 0 6px rgba(255, 0, 128, 0.6));
                }
                .last-update {
                    position: absolute;
                    bottom: 20px;
                    right: 30px;
                    font-size: 11px;
                    color: #6c757d;
                    opacity: 0.7;
                }
            </style>
            <script>
                const originalLog = console.log;
                const originalError = console.error;
                const originalWarn = console.warn;
                
                console.log = function(...args) {
                    originalLog.apply(console, args);
                    if (!window.dashLogs) window.dashLogs = [];
                    window.dashLogs.push({type: 'log', message: args.join(' '), timestamp: new Date().toISOString()});
                };
                
                console.error = function(...args) {
                    originalError.apply(console, args);
                    if (!window.dashLogs) window.dashLogs = [];
                    window.dashLogs.push({type: 'error', message: args.join(' '), timestamp: new Date().toISOString()});
                };
                
                console.warn = function(...args) {
                    originalWarn.apply(console, args);
                    if (!window.dashLogs) window.dashLogs = [];
                    window.dashLogs.push({type: 'warn', message: args.join(' '), timestamp: new Date().toISOString()});
                };
                
                // Monitor Plotly chart updates
                document.addEventListener('DOMContentLoaded', function() {
                    console.log('🔍 Setting up chart monitoring...');
                    
                    // Wait for Dash/Plotly to be ready
                    setTimeout(function() {
                        let lastChartData = null;
                        let checkCount = 0;
                        
                        const checkChart = function() {
                            try {
                                const chartElement = document.querySelector('#price .js-plotly-plot');
                                if (chartElement) {
                                    // Access Plotly's internal data via the element
                                    const plotDiv = chartElement.querySelector('.plotly');
                                    if (plotDiv && window.Plotly && plotDiv._fullData) {
                                        const traces = plotDiv._fullData;
                                        const currentData = JSON.stringify(traces.map(t => ({
                                            name: t.name,
                                            pointCount: t.x ? t.x.length : 0
                                        })));
                                        
                                        // Only log if data changed
                                        if (currentData !== lastChartData) {
                                            lastChartData = currentData;
                                            console.group('📈 Chart Rendered/Updated');
                                            console.log('Timestamp:', new Date().toISOString());
                                            console.log('Number of traces:', traces.length);
                                            traces.forEach(function(trace, idx) {
                                                const yValues = trace.y ? trace.y.filter(v => v !== null && v !== undefined) : [];
                                                console.log(`Trace ${idx + 1}: ${trace.name || 'Unnamed'}`, {
                                                    type: trace.type,
                                                    mode: trace.mode,
                                                    pointCount: trace.x ? trace.x.length : 0,
                                                    firstTimestamp: trace.x ? trace.x[0] : 'N/A',
                                                    lastTimestamp: trace.x ? trace.x[trace.x.length - 1] : 'N/A',
                                                    firstValue: yValues.length > 0 ? yValues[0] : 'N/A',
                                                    lastValue: yValues.length > 0 ? yValues[yValues.length - 1] : 'N/A',
                                                    yRange: yValues.length > 0 ? {
                                                        min: Math.min(...yValues).toFixed(2),
                                                        max: Math.max(...yValues).toFixed(2)
                                                    } : 'N/A'
                                                });
                                            });
                                            console.groupEnd();
                                        }
                                    }
                                } else if (checkCount < 5) {
                                    checkCount++;
                                    // Keep checking if chart element not found yet
                                    setTimeout(checkChart, 500);
                                }
                            } catch (e) {
                                // Silently ignore errors (chart might not be rendered yet)
                            }
                        };
                        
                        // Start checking after initial delay
                        setTimeout(function() {
                            checkChart();
                            // Poll every 2 seconds
                            setInterval(checkChart, 2000);
                            console.log('✅ Chart monitoring active');
                        }, 1000);
                        
                    }, 500);
                });
            </script>
        </head>
        <body>
            {%app_entry%}
            <footer>
                {%config%}
                {%scripts%}
                {%renderer%}
            </footer>
        </body>
    </html>
    '''
    
    dash_app.layout = html.Div([
        html.Div([
            html.Div([
                html.Div([
                    html.Span(className="status-indicator"),
                    html.H1("Real-Time Stock Fusion Dashboard", className="dashboard-title")
                ], style={"display": "flex", "alignItems": "center"}),
                html.Div([
                    dcc.Dropdown(
                        id="ticker",
                        options=[{"label": t, "value": t} for t in ["AAPL", "MSFT", "GOOGL"]],
                        value="AAPL",
                        className="ticker-selector",
                        style={
                            "backgroundColor": "rgba(255,255,255,0.2)",
                            "border": "none",
                            "borderRadius": "8px",
                            "color": "white"
                        }
                    )
                ])
            ], className="dashboard-header"),
            html.Div([
                html.Div([
                    dcc.Graph(id="price", style={"height": "500px"})
                ], className="chart-container"),
                html.Div(id="funds", className="fundamentals-container")
            ], className="dashboard-content"),
            dcc.Interval(id="refresh", interval=60*1000, n_intervals=0),
            dcc.Store(id="debug-store", data={})
        ], className="dashboard-container")
    ])
    
    # Clientside callback to log debug info to console
    # This uses a dummy output to avoid duplicate outputs
    dash_app.clientside_callback(
        """
        function(debugData) {
            if (debugData && Object.keys(debugData).length > 0) {
                console.group('📊 Dashboard Update');
                console.log('🕐 Time:', new Date().toISOString());
                
                if (debugData.ticker) {
                    console.log('📈 Ticker:', debugData.ticker);
                }
                if (debugData.refresh_count !== undefined) {
                    console.log('🔄 Refresh Count:', debugData.refresh_count);
                }
                
                // API Endpoints
                console.group('🔗 API Endpoints');
                if (debugData.series_url) console.log('Series:', debugData.series_url);
                if (debugData.fundamentals_url) console.log('Fundamentals:', debugData.fundamentals_url);
                console.groupEnd();
                
                // Series Data Status
                console.group('📉 Price Data Status');
                if (debugData.series_status) {
                    const status = debugData.series_status === 'success' ? '✅' : '❌';
                    console.log('Status:', status, debugData.series_status);
                }
                if (debugData.series_points_count !== undefined) {
                    console.log('Points Count:', debugData.series_points_count);
                    if (debugData.series_points_count === 0) {
                        console.warn('⚠️ No price data points available!');
                    }
                }
                if (debugData.series_has_sma20 !== undefined) {
                    console.log('Has SMA20:', debugData.series_has_sma20 ? '✅ Yes' : '❌ No');
                }
                if (debugData.price_range) {
                    console.log('Price Range: $' + debugData.price_range.min.toFixed(2) + ' - $' + debugData.price_range.max.toFixed(2));
                }
                if (debugData.timestamps_sample && debugData.timestamps_sample.length > 0) {
                    console.log('Sample Timestamps:', debugData.timestamps_sample);
                }
                console.groupEnd();
                
                // Chart Construction Details
                console.group('📊 Chart Construction');
                if (debugData.chart_points_count !== undefined) {
                    console.log('Chart Points:', debugData.chart_points_count);
                }
                if (debugData.chart_traces_count !== undefined) {
                    console.log('Chart Traces:', debugData.chart_traces_count);
                }
                if (debugData.first_timestamp) {
                    console.log('First Timestamp:', debugData.first_timestamp);
                }
                if (debugData.last_timestamp) {
                    console.log('Last Timestamp:', debugData.last_timestamp);
                }
                if (debugData.sma20_array_length !== undefined) {
                    console.log('SMA20 Array Length:', debugData.sma20_array_length);
                }
                if (debugData.sma20_points_count !== undefined) {
                    console.log('SMA20 Points (after filtering):', debugData.sma20_points_count);
                    if (debugData.sma20_range) {
                        console.log('SMA20 Range: $' + debugData.sma20_range.min.toFixed(2) + ' - $' + debugData.sma20_range.max.toFixed(2));
                    }
                } else if (debugData.sma20_available === false) {
                    console.warn('⚠️ SMA20 data not available or all values are null');
                }
                if (debugData.no_data) {
                    console.warn('⚠️ Chart has no data points!');
                }
                console.groupEnd();
                
                // Fundamentals Data Status
                console.group('💰 Fundamentals Data Status');
                if (debugData.fundamentals_status) {
                    const status = debugData.fundamentals_status === 'success' ? '✅' : '❌';
                    console.log('Status:', status, debugData.fundamentals_status);
                }
                if (debugData.fundamentals_data) {
                    const f = debugData.fundamentals_data;
                    console.log('P/E Ratio:', f.pe_ttm !== null && f.pe_ttm !== undefined ? f.pe_ttm : 'N/A');
                    console.log('Market Cap:', f.market_cap !== null && f.market_cap !== undefined ? '$' + (f.market_cap / 1e9).toFixed(2) + 'B' : 'N/A');
                    console.log('52W High:', f.fifty_two_week_high !== null && f.fifty_two_week_high !== undefined ? '$' + f.fifty_two_week_high.toFixed(2) : 'N/A');
                    console.log('52W Low:', f.fifty_two_week_low !== null && f.fifty_two_week_low !== undefined ? '$' + f.fifty_two_week_low.toFixed(2) : 'N/A');
                    console.log('As of:', f.as_of || 'N/A');
                }
                console.groupEnd();
                
                // Raw Data (expanded on click in console)
                if (debugData.series_data) {
                    console.group('📦 Raw Series Data');
                    console.log(debugData.series_data);
                    if (debugData.series_data.points && debugData.series_data.points.length > 0) {
                        console.log('First 3 Points:', debugData.series_data.points.slice(0, 3));
                        console.log('Last 3 Points:', debugData.series_data.points.slice(-3));
                    }
                    if (debugData.series_data.sma20) {
                        const sma20 = debugData.series_data.sma20;
                        const nonNullCount = sma20.filter(v => v !== null && v !== undefined).length;
                        console.log('SMA20 Array Length:', sma20.length);
                        console.log('SMA20 Non-null Values:', nonNullCount);
                        console.log('SMA20 Sample (first 5):', sma20.slice(0, 5));
                    }
                    console.groupEnd();
                }
                
                // Errors
                if (debugData.status === 'error') {
                    console.group('❌ Error Details');
                    console.error('Error Message:', debugData.error);
                    if (debugData.error_type) {
                        console.error('Error Type:', debugData.error_type);
                    }
                    console.groupEnd();
                } else if (debugData.status === 'success') {
                    console.log('✅ Update Complete');
                }
                
                console.groupEnd();
                console.log(''); // Empty line for readability
            }
            return null;
        }
        """,
        Output("debug-store", "data", allow_duplicate=True),
        Input("debug-store", "data"),
        prevent_initial_call=True
    )

    @dash_app.callback(
        Output("price","figure"), Output("funds","children"), Output("debug-store","data"),
        Input("ticker","value"), Input("refresh","n_intervals")
    )
    def update(ticker, n_intervals):
        import plotly.graph_objects as go
        import os
        
        # Debug info - will be sent to clientside callback
        api_base = os.getenv("API_BASE_URL", "http://localhost:8050")
        series_url = f"{api_base}/api/series/{ticker}"
        fundamentals_url = f"{api_base}/api/fundamentals/{ticker}"
        
        debug_info = {
            "ticker": ticker,
            "refresh_count": n_intervals,
            "series_url": series_url,
            "fundamentals_url": fundamentals_url
        }
        
        try:
            # Fetch series data
            print(f"[DEBUG] Fetching series data for {ticker} from {series_url}")
            series_response = requests.get(series_url, timeout=10)
            series_response.raise_for_status()
            s = series_response.json()
            
            debug_info["series_status"] = "success"
            debug_info["series_points_count"] = len(s.get("points", []))
            debug_info["series_has_sma20"] = bool(s.get("sma20"))
            debug_info["series_data"] = s
            
            # Fetch fundamentals data
            print(f"[DEBUG] Fetching fundamentals data for {ticker} from {fundamentals_url}")
            fundamentals_response = requests.get(fundamentals_url, timeout=10)
            fundamentals_response.raise_for_status()
            f = fundamentals_response.json()
            
            debug_info["fundamentals_status"] = "success"
            debug_info["fundamentals_data"] = f
            
            # Build figure
            fig = go.Figure()
            points = s.get("points", [])
            current_price = None
            
            print(f"[DEBUG] Building chart with {len(points)} points")
            
            if points:
                timestamps = [p["ts"] for p in points]
                closes = [p["close"] for p in points]
                
                print(f"[DEBUG] Extracted {len(timestamps)} timestamps and {len(closes)} close prices")
                print(f"[DEBUG] First timestamp: {timestamps[0] if timestamps else 'N/A'}, Last: {timestamps[-1] if timestamps else 'N/A'}")
                print(f"[DEBUG] Price range: ${min(closes):.2f} - ${max(closes):.2f}")
                
                # Calculate current price for display
                current_price = closes[-1] if closes else None
                
                # Add Close Price trace with enhanced styling
                fig.add_trace(go.Scatter(
                    x=timestamps, 
                    y=closes, 
                    name="Close Price", 
                    mode="lines",
                    line=dict(color='#00ffff', width=3.5, shape='spline', smoothing=1.3),
                    fill='tozeroy',
                    fillcolor='rgba(0, 255, 255, 0.12)',
                    hovertemplate='<b>%{fullData.name}</b><br>Time: %{x}<br>Price: $%{y:,.2f}<extra></extra>',
                    showlegend=True
                ))
                print("[DEBUG] Added Close Price trace to chart")
                
                # Add SMA20 trace if available
                sma20_data = s.get("sma20", [])
                debug_info["sma20_array_length"] = len(sma20_data) if sma20_data else 0
                
                if sma20_data and any(v is not None for v in sma20_data):
                    # Filter out None values for SMA20
                    sma20_filtered = [(ts, val) for ts, val in zip(timestamps, sma20_data) if val is not None]
                    print(f"[DEBUG] SMA20 data: {len(sma20_data)} total values, {len(sma20_filtered)} non-null values")
                    
                    if sma20_filtered:
                        sma20_times = [t[0] for t in sma20_filtered]
                        sma20_values = [t[1] for t in sma20_filtered]
                        
                        fig.add_trace(go.Scatter(
                            x=sma20_times, 
                            y=sma20_values, 
                            name="SMA20", 
                            mode="lines",
                            line=dict(color='#ec4899', width=3, dash='dash', shape='spline', smoothing=1.3),
                            hovertemplate='<b>%{fullData.name}</b><br>Time: %{x}<br>Price: $%{y:,.2f}<extra></extra>',
                            showlegend=True
                        ))
                        print(f"[DEBUG] Added SMA20 trace with {len(sma20_filtered)} points")
                        
                        debug_info["sma20_points_count"] = len(sma20_filtered)
                        debug_info["sma20_range"] = {
                            "min": min(sma20_values) if sma20_values else None,
                            "max": max(sma20_values) if sma20_values else None
                        }
                else:
                    print("[DEBUG] No SMA20 data available or all values are None")
                    debug_info["sma20_available"] = False
                
                debug_info["chart_points_count"] = len(points)
                debug_info["chart_traces_count"] = len(fig.data)
                debug_info["price_range"] = {
                    "min": min(closes) if closes else None,
                    "max": max(closes) if closes else None
                }
                
                debug_info["timestamps_sample"] = timestamps[:5] if timestamps else []
                debug_info["first_timestamp"] = timestamps[0] if timestamps else None
                debug_info["last_timestamp"] = timestamps[-1] if timestamps else None
            else:
                print("[DEBUG] WARNING: No points available for chart")
                debug_info["no_data"] = True
                debug_info["chart_traces_count"] = 0
            
            # Calculate price change for indicator
            price_change = None
            price_change_pct = None
            if len(closes) >= 2:
                price_change = closes[-1] - closes[0]
                price_change_pct = (price_change / closes[0]) * 100
            
            fig.update_layout(
                title=dict(
                    text=f"{ticker} Price Chart{' ' + ('↑' if price_change and price_change > 0 else '↓') if price_change else ''}",
                    font=dict(size=28, color='#e2e8f0', family='-apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif'),
                    x=0.5,
                    xanchor='center',
                    pad=dict(t=10, b=20)
                ),
                xaxis=dict(
                    title="Time",
                    titlefont=dict(size=13, color='#94a3b8'),
                    gridcolor='rgba(0, 255, 255, 0.1)',
                    gridwidth=1,
                    showgrid=True,
                    zeroline=False,
                    showline=True,
                    linecolor='rgba(0, 255, 255, 0.2)',
                    linewidth=1,
                    tickfont=dict(size=11, color='#94a3b8')
                ),
                yaxis=dict(
                    title="Price ($)",
                    titlefont=dict(size=13, color='#94a3b8'),
                    gridcolor='rgba(0, 255, 255, 0.1)',
                    gridwidth=1,
                    showgrid=True,
                    zeroline=False,
                    showline=True,
                    linecolor='rgba(0, 255, 255, 0.2)',
                    linewidth=1,
                    tickfont=dict(size=11, color='#94a3b8'),
                    tickformat='$,.2f'
                ),
                hovermode='x unified',
                template='plotly_dark',
                plot_bgcolor='rgba(15, 23, 42, 0.4)',
                paper_bgcolor='rgba(15, 23, 42, 0.4)',
                font=dict(family='-apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif', size=12, color='#e2e8f0'),
                legend=dict(
                    orientation="h",
                    yanchor="bottom",
                    y=1.02,
                    xanchor="right",
                    x=1,
                    bgcolor='rgba(15, 23, 42, 0.9)',
                    bordercolor='rgba(0, 255, 255, 0.3)',
                    borderwidth=1,
                    font=dict(size=12, color='#e2e8f0')
                ),
                margin=dict(l=70, r=50, t=90, b=70),
                hoverlabel=dict(
                    bgcolor='rgba(15, 23, 42, 0.95)',
                    bordercolor='#00ffff',
                    font=dict(size=12, family='-apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif', color='#e2e8f0')
                )
            )
            
            # Modern fundamentals cards
            def format_value(val, is_currency=False, is_percent=False):
                if val is None or val == 'N/A':
                    return html.Span("N/A", className="metric-value none")
                try:
                    if is_currency:
                        if val >= 1e12:
                            return html.Span(f"${val/1e12:.2f}T", className="metric-value")
                        elif val >= 1e9:
                            return html.Span(f"${val/1e9:.2f}B", className="metric-value")
                        elif val >= 1e6:
                            return html.Span(f"${val/1e6:.2f}M", className="metric-value")
                        else:
                            return html.Span(f"${val:,.2f}", className="metric-value")
                    elif is_percent:
                        return html.Span(f"{val:.2f}%", className="metric-value")
                    else:
                        return html.Span(f"{val:,.2f}", className="metric-value")
                except:
                    return html.Span(str(val), className="metric-value")
            
            # Calculate price change indicator
            price_change_html = None
            if price_change is not None and price_change_pct is not None:
                is_positive = price_change > 0
                price_change_html = html.Span([
                    "↑" if is_positive else "↓",
                    f" ${abs(price_change):.2f} ({abs(price_change_pct):.2f}%)"
                ], className=f"price-indicator {'price-up' if is_positive else 'price-down'}")
            
            funds = html.Div([
                html.Div([
                    html.Div([
                        html.Span("📊", className="metric-icon"),
                        "P/E Ratio (TTM)"
                    ], className="metric-label"),
                    html.Div([
                        format_value(f.get('pe_ttm')),
                        price_change_html if price_change_html and f.get('pe_ttm') else None
                    ], style={"display": "flex", "alignItems": "center"})
                ], className="metric-card"),
                html.Div([
                    html.Div([
                        html.Span("💰", className="metric-icon"),
                        "Market Cap"
                    ], className="metric-label"),
                    format_value(f.get('market_cap'), is_currency=True)
                ], className="metric-card"),
                html.Div([
                    html.Div([
                        html.Span("📈", className="metric-icon"),
                        "52-Week High"
                    ], className="metric-label"),
                    format_value(f.get('fifty_two_week_high'), is_currency=True)
                ], className="metric-card"),
                html.Div([
                    html.Div([
                        html.Span("📉", className="metric-icon"),
                        "52-Week Low"
                    ], className="metric-label"),
                    format_value(f.get('fifty_two_week_low'), is_currency=True)
                ], className="metric-card"),
                html.Div([
                    html.Div([
                        html.Span("🕐", className="metric-icon"),
                        "Current Price"
                    ], className="metric-label"),
                    html.Div([
                        html.Span(f"${current_price:,.2f}" if current_price else "N/A", className="metric-value"),
                        price_change_html if price_change_html and current_price else None
                    ], style={"display": "flex", "alignItems": "center", "flexWrap": "wrap"})
                ], className="metric-card"),
                html.Div([
                    html.Div([
                        html.Span("🔄", className="metric-icon"),
                        "Last Updated"
                    ], className="metric-label"),
                    html.Span(f.get('as_of', 'N/A'), className="metric-value", style={"fontSize": "20px"})
                ], className="metric-card")
            ])
            
            debug_info["status"] = "success"
            return fig, funds, debug_info
            
        except requests.exceptions.RequestException as e:
            error_msg = str(e)
            print(f"[DEBUG] Request error: {error_msg}")
            debug_info["status"] = "error"
            debug_info["error"] = error_msg
            debug_info["error_type"] = "RequestException"
            error_fig = go.Figure()
            error_fig.add_annotation(
                text=f"Error loading data: {error_msg}<br>Please check if services are running.",
                xref="paper", yref="paper",
                x=0.5, y=0.5, showarrow=False,
                font=dict(size=16, color='#dc3545')
            )
            error_fig.update_layout(
                template='plotly_white',
                plot_bgcolor='white',
                paper_bgcolor='white'
            )
            return error_fig, html.Div([
                html.Div([
                    html.Div("Error", className="metric-label"),
                    html.Span(error_msg, className="metric-value", style={"color": "#dc3545"})
                ], className="metric-card")
            ], className="fundamentals-container"), debug_info
            
        except Exception as e:
            error_msg = str(e)
            print(f"[DEBUG] Unexpected error: {error_msg}")
            debug_info["status"] = "error"
            debug_info["error"] = error_msg
            debug_info["error_type"] = type(e).__name__
            error_fig = go.Figure()
            error_fig.add_annotation(
                text=f"Unexpected error: {error_msg}",
                xref="paper", yref="paper",
                x=0.5, y=0.5, showarrow=False,
                font=dict(size=16, color='#dc3545')
            )
            error_fig.update_layout(
                template='plotly_white',
                plot_bgcolor='white',
                paper_bgcolor='white'
            )
            return error_fig, html.Div([
                html.Div([
                    html.Div("Error", className="metric-label"),
                    html.Span(error_msg, className="metric-value", style={"color": "#dc3545"})
                ], className="metric-card")
            ], className="fundamentals-container"), debug_info

    fastapi_app.mount("/", WSGIMiddleware(dash_app.server))

