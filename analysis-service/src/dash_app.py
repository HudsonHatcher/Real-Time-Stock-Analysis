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
                    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                    min-height: 100vh;
                    padding: 20px;
                }
                .dashboard-container {
                    max-width: 1400px;
                    margin: 0 auto;
                    background: white;
                    border-radius: 20px;
                    box-shadow: 0 20px 60px rgba(0,0,0,0.3);
                    overflow: hidden;
                }
                .dashboard-header {
                    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                    color: white;
                    padding: 30px 40px;
                    display: flex;
                    justify-content: space-between;
                    align-items: center;
                }
                .dashboard-title {
                    font-size: 28px;
                    font-weight: 700;
                    letter-spacing: -0.5px;
                }
                .ticker-selector {
                    min-width: 200px;
                }
                .dashboard-content {
                    padding: 40px;
                }
                .chart-container {
                    background: #f8f9fa;
                    border-radius: 12px;
                    padding: 20px;
                    margin-bottom: 30px;
                    box-shadow: 0 2px 8px rgba(0,0,0,0.1);
                }
                .fundamentals-container {
                    display: grid;
                    grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
                    gap: 20px;
                    margin-top: 30px;
                }
                .metric-card {
                    background: linear-gradient(135deg, #f5f7fa 0%, #c3cfe2 100%);
                    border-radius: 12px;
                    padding: 20px;
                    box-shadow: 0 4px 6px rgba(0,0,0,0.1);
                    transition: transform 0.2s;
                }
                .metric-card:hover {
                    transform: translateY(-2px);
                    box-shadow: 0 6px 12px rgba(0,0,0,0.15);
                }
                .metric-label {
                    font-size: 12px;
                    color: #6c757d;
                    text-transform: uppercase;
                    letter-spacing: 1px;
                    margin-bottom: 8px;
                    font-weight: 600;
                }
                .metric-value {
                    font-size: 24px;
                    font-weight: 700;
                    color: #212529;
                }
                .metric-value.none {
                    color: #adb5bd;
                    font-style: italic;
                }
                .status-indicator {
                    display: inline-block;
                    width: 10px;
                    height: 10px;
                    border-radius: 50%;
                    margin-right: 8px;
                    background: #28a745;
                    animation: pulse 2s infinite;
                }
                @keyframes pulse {
                    0%, 100% { opacity: 1; }
                    50% { opacity: 0.5; }
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
                console.log('=== Dashboard Update ===');
                if (debugData.ticker) console.log('Ticker:', debugData.ticker);
                if (debugData.refresh_count !== undefined) console.log('Refresh Count:', debugData.refresh_count);
                if (debugData.series_url) console.log('Series API URL:', debugData.series_url);
                if (debugData.fundamentals_url) console.log('Fundamentals API URL:', debugData.fundamentals_url);
                if (debugData.series_status) console.log('Series API Status:', debugData.series_status);
                if (debugData.series_points_count !== undefined) console.log('Number of price points:', debugData.series_points_count);
                if (debugData.series_has_sma20 !== undefined) console.log('Has SMA20 data:', debugData.series_has_sma20);
                if (debugData.fundamentals_status) console.log('Fundamentals API Status:', debugData.fundamentals_status);
                if (debugData.chart_points_count !== undefined) console.log('Chart Data Points:', debugData.chart_points_count);
                if (debugData.price_range) {
                    console.log('Price Range:', debugData.price_range.min, '-', debugData.price_range.max);
                }
                if (debugData.sma20_points_count !== undefined) console.log('SMA20 data points:', debugData.sma20_points_count);
                if (debugData.series_data) {
                    console.log('Series Data:', debugData.series_data);
                }
                if (debugData.fundamentals_data) {
                    console.log('Fundamentals Data:', debugData.fundamentals_data);
                }
                if (debugData.status === 'error') {
                    console.error('Error:', debugData.error);
                    if (debugData.error_type) console.error('Error Type:', debugData.error_type);
                }
                if (debugData.status === 'success') {
                    console.log('=== Update Complete ===');
                }
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
            
            if points:
                timestamps = [p["ts"] for p in points]
                closes = [p["close"] for p in points]
                
                fig.add_trace(go.Scatter(
                    x=timestamps, 
                    y=closes, 
                    name="Close Price", 
                    mode="lines",
                    line=dict(color='#667eea', width=3),
                    fill='tozeroy',
                    fillcolor='rgba(102, 126, 234, 0.1)',
                    hovertemplate='<b>%{fullData.name}</b><br>Time: %{x}<br>Price: $%{y:.2f}<extra></extra>'
                ))
                
                sma20_data = s.get("sma20", [])
                if sma20_data and any(v is not None for v in sma20_data):
                    # Filter out None values for SMA20
                    sma20_filtered = [(ts, val) for ts, val in zip(timestamps, sma20_data) if val is not None]
                    if sma20_filtered:
                        sma20_times = [t[0] for t in sma20_filtered]
                        sma20_values = [t[1] for t in sma20_filtered]
                        fig.add_trace(go.Scatter(
                            x=sma20_times, 
                            y=sma20_values, 
                            name="SMA20", 
                            mode="lines",
                            line=dict(color='#f093fb', width=2.5, dash='dash'),
                            hovertemplate='<b>%{fullData.name}</b><br>Time: %{x}<br>Price: $%{y:.2f}<extra></extra>'
                        ))
                        
                        debug_info["sma20_points_count"] = len(sma20_filtered)
                        debug_info["sma20_range"] = {
                            "min": min(sma20_values) if sma20_values else None,
                            "max": max(sma20_values) if sma20_values else None
                        }
                
                debug_info["chart_points_count"] = len(points)
                debug_info["price_range"] = {
                    "min": min(closes) if closes else None,
                    "max": max(closes) if closes else None
                }
                
                debug_info["timestamps_sample"] = timestamps[:5] if timestamps else []
            else:
                debug_info["no_data"] = True
            
            fig.update_layout(
                title=dict(
                    text=f"{ticker} Price Chart",
                    font=dict(size=24, color='#212529', family='Arial, sans-serif')
                ),
                xaxis=dict(
                    title="Time",
                    titlefont=dict(size=14, color='#6c757d'),
                    gridcolor='#e9ecef',
                    showgrid=True
                ),
                yaxis=dict(
                    title="Price ($)",
                    titlefont=dict(size=14, color='#6c757d'),
                    gridcolor='#e9ecef',
                    showgrid=True
                ),
                hovermode='x unified',
                template='plotly_white',
                plot_bgcolor='white',
                paper_bgcolor='white',
                font=dict(family='Arial, sans-serif', size=12),
                legend=dict(
                    orientation="h",
                    yanchor="bottom",
                    y=1.02,
                    xanchor="right",
                    x=1
                ),
                margin=dict(l=60, r=40, t=80, b=60)
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
            
            funds = html.Div([
                html.Div([
                    html.Div("P/E Ratio (TTM)", className="metric-label"),
                    format_value(f.get('pe_ttm'))
                ], className="metric-card"),
                html.Div([
                    html.Div("Market Cap", className="metric-label"),
                    format_value(f.get('market_cap'), is_currency=True)
                ], className="metric-card"),
                html.Div([
                    html.Div("52-Week High", className="metric-label"),
                    format_value(f.get('fifty_two_week_high'), is_currency=True)
                ], className="metric-card"),
                html.Div([
                    html.Div("52-Week Low", className="metric-label"),
                    format_value(f.get('fifty_two_week_low'), is_currency=True)
                ], className="metric-card"),
                html.Div([
                    html.Div("Last Updated", className="metric-label"),
                    html.Span(f.get('as_of', 'N/A'), className="metric-value")
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

