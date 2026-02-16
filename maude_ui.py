#!/usr/bin/env python3
"""
MAUDE Database Web UI
Simple web interface to search and view MAUDE data in tabular format
"""

import os
from datetime import datetime
import dash
from dash import dcc, html, dash_table, Input, Output, State
import dash_bootstrap_components as dbc
from dotenv import load_dotenv
import pandas as pd
from maude_api_fetch_v2 import MAUDEFetcher

# Load environment variables
load_dotenv()

# Initialize the Dash app
app = dash.Dash(
    __name__,
    external_stylesheets=[dbc.themes.BOOTSTRAP],
    suppress_callback_exceptions=True
)

# Initialize MAUDE fetcher
api_key = os.getenv('FDA_API_KEY')
fetcher = MAUDEFetcher(api_key=api_key)

# Sample queries for dropdown
SAMPLE_QUERIES = [
    {'label': 'Pacemaker Reports', 'value': 'device.generic_name:"pacemaker"'},
    {'label': 'Insulin Pump Reports', 'value': 'device.generic_name:"insulin+pump"'},
    {'label': 'Defibrillator Reports', 'value': 'device.generic_name:"defibrillator"'},
    {'label': 'Medtronic Devices', 'value': 'device.manufacturer_d_name:"medtronic"'},
    {'label': 'Death Events', 'value': 'event_type:"Death"'},
    {'label': 'Injury Events', 'value': 'event_type:"Injury"'},
    {'label': 'Recent Reports (Last Month)', 'value': 'date_received:[20240101+TO+20240131]'},
    {'label': 'Custom Query', 'value': 'custom'},
]

# App layout
app.layout = dbc.Container([
    dbc.Row([
        dbc.Col([
            html.H1("🏥 MAUDE Database Viewer", className="text-center mb-4 mt-4"),
            html.P("FDA Medical Device Adverse Event Reports", 
                   className="text-center text-muted mb-4"),
        ])
    ]),
    
    dbc.Row([
        dbc.Col([
            dbc.Card([
                dbc.CardBody([
                    html.H5("Search Parameters", className="card-title"),
                    
                    # Sample queries dropdown
                    html.Label("Sample Queries:", className="fw-bold mt-2"),
                    dcc.Dropdown(
                        id='sample-query-dropdown',
                        options=SAMPLE_QUERIES,
                        value='device.generic_name:"pacemaker"',
                        placeholder="Select a sample query...",
                        className="mb-3"
                    ),
                    
                    # Custom query input
                    html.Label("Custom Query:", className="fw-bold"),
                    dbc.Input(
                        id='custom-query-input',
                        type='text',
                        placeholder='e.g., device.generic_name:"stent"+AND+event_type:"Death"',
                        className="mb-3"
                    ),
                    
                    # Max results input
                    html.Label("Max Results:", className="fw-bold"),
                    dbc.Input(
                        id='max-results-input',
                        type='number',
                        value=100,
                        min=1,
                        max=5000,
                        step=100,
                        className="mb-3"
                    ),
                    
                    # Search button
                    dbc.Button(
                        "Search MAUDE Database",
                        id='search-button',
                        color="primary",
                        className="w-100 mb-2",
                        size="lg"
                    ),
                    
                    # Export button
                    dbc.Button(
                        "Export to CSV",
                        id='export-button',
                        color="secondary",
                        className="w-100",
                        disabled=True
                    ),
                    
                    # Download component
                    dcc.Download(id="download-csv"),
                ])
            ], className="mb-4")
        ], width=12, lg=4),
        
        dbc.Col([
            # Status messages
            html.Div(id='status-message', className="mb-3"),
            
            # Statistics cards
            html.Div(id='stats-cards', className="mb-3"),
            
            # Data table
            html.Div(id='data-table-container'),
            
        ], width=12, lg=8),
    ]),
    
    # Store for data
    dcc.Store(id='stored-data'),
    
    dbc.Row([
        dbc.Col([
            html.Hr(),
            html.P([
                "Data source: ",
                html.A("FDA openFDA API", href="https://open.fda.gov/apis/device/event/", target="_blank"),
                " | ",
                html.A("Query Syntax Guide", href="https://open.fda.gov/apis/query-syntax/", target="_blank"),
            ], className="text-center text-muted small")
        ])
    ])
    
], fluid=True)


@app.callback(
    Output('custom-query-input', 'value'),
    Input('sample-query-dropdown', 'value'),
    prevent_initial_call=True
)
def update_custom_query(selected_query):
    """Update custom query input when sample is selected"""
    if selected_query and selected_query != 'custom':
        return selected_query
    return dash.no_update


@app.callback(
    [Output('stored-data', 'data'),
     Output('status-message', 'children'),
     Output('export-button', 'disabled')],
    Input('search-button', 'n_clicks'),
    [State('custom-query-input', 'value'),
     State('max-results-input', 'value')],
    prevent_initial_call=True
)
def search_maude(n_clicks, query, max_results):
    """Search MAUDE database and store results"""
    if not query:
        alert = dbc.Alert("Please enter a search query", color="warning")
        return None, alert, True
    
    # Show loading message
    loading = dbc.Alert([
        dbc.Spinner(size="sm", spinnerClassName="me-2"),
        f"Searching MAUDE database... (max {max_results} results)"
    ], color="info")
    
    try:
        # Fetch data
        results = fetcher.fetch_all(query, max_results=max_results, delay=0.3)
        
        if not results:
            alert = dbc.Alert("No results found. Try a different query.", color="warning")
            return None, alert, True
        
        # Parse to DataFrame
        df = fetcher.parse_to_dataframe(results)
        
        # Success message
        success = dbc.Alert([
            html.I(className="bi bi-check-circle-fill me-2"),
            f"Found {len(df)} reports! Scroll down to view data."
        ], color="success")
        
        return df.to_json(date_format='iso', orient='split'), success, False
        
    except Exception as e:
        error = dbc.Alert([
            html.Strong("Error: "),
            str(e),
            html.Br(),
            html.Small("Try narrowing your search or combining with device/manufacturer filters.")
        ], color="danger")
        return None, error, True


@app.callback(
    [Output('stats-cards', 'children'),
     Output('data-table-container', 'children')],
    Input('stored-data', 'data'),
)
def update_display(json_data):
    """Update statistics cards and data table"""
    if not json_data:
        return None, None
    
    # Load data
    from io import StringIO
    df = pd.read_json(StringIO(json_data), orient='split')
    
    # Statistics cards
    stats = dbc.Row([
        dbc.Col([
            dbc.Card([
                dbc.CardBody([
                    html.H6("Total Reports", className="text-muted"),
                    html.H3(f"{len(df):,}", className="mb-0")
                ])
            ])
        ], width=6, lg=3),
        
        dbc.Col([
            dbc.Card([
                dbc.CardBody([
                    html.H6("Event Types", className="text-muted"),
                    html.H3(f"{df['event_type'].nunique()}", className="mb-0")
                ])
            ])
        ], width=6, lg=3),
        
        dbc.Col([
            dbc.Card([
                dbc.CardBody([
                    html.H6("Devices", className="text-muted"),
                    html.H3(f"{df['device_generic_name'].nunique()}", className="mb-0")
                ])
            ])
        ], width=6, lg=3),
        
        dbc.Col([
            dbc.Card([
                dbc.CardBody([
                    html.H6("Manufacturers", className="text-muted"),
                    html.H3(f"{df['device_manufacturer'].nunique()}", className="mb-0")
                ])
            ])
        ], width=6, lg=3),
    ], className="mb-3")
    
    # Prepare data for table (limit columns for readability)
    display_columns = [
        'report_number', 'date_received', 'event_type', 
        'device_generic_name', 'device_brand_name', 'device_manufacturer',
        'outcome'
    ]
    
    # Filter to available columns
    available_cols = [col for col in display_columns if col in df.columns]
    df_display = df[available_cols].copy()
    
    # Format date columns
    for col in ['date_received', 'date_of_event']:
        if col in df_display.columns:
            df_display[col] = pd.to_datetime(df_display[col], format='%Y%m%d', errors='coerce').dt.strftime('%Y-%m-%d')
    
    # Fill NaN values
    df_display = df_display.fillna('')
    
    # Create data table
    table = dash_table.DataTable(
        id='results-table',
        columns=[{"name": col.replace('_', ' ').title(), "id": col} for col in df_display.columns],
        data=df_display.to_dict('records'),
        
        # Styling
        style_table={'overflowX': 'auto'},
        style_cell={
            'textAlign': 'left',
            'padding': '10px',
            'whiteSpace': 'normal',
            'height': 'auto',
        },
        style_header={
            'backgroundColor': 'rgb(230, 230, 230)',
            'fontWeight': 'bold'
        },
        style_data_conditional=[
            {
                'if': {'row_index': 'odd'},
                'backgroundColor': 'rgb(248, 248, 248)'
            }
        ],
        
        # Features
        page_size=int(os.getenv('ROWS_PER_PAGE', 25)),
        filter_action="native",
        sort_action="native",
        sort_mode="multi",
        
        # Export
        export_format="csv",
        export_headers="display",
    )
    
    table_card = dbc.Card([
        dbc.CardBody([
            html.H5("Search Results", className="card-title mb-3"),
            table
        ])
    ])
    
    return stats, table_card


@app.callback(
    Output("download-csv", "data"),
    Input("export-button", "n_clicks"),
    State('stored-data', 'data'),
    prevent_initial_call=True,
)
def export_data(n_clicks, json_data):
    """Export data to CSV"""
    if json_data:
        df = pd.read_json(json_data, orient='split')
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        return dcc.send_data_frame(df.to_csv, f"maude_export_{timestamp}.csv", index=False)


if __name__ == '__main__':
    host = os.getenv('UI_HOST', 'localhost')
    port = int(os.getenv('UI_PORT', 8050))
    
    print("="*60)
    print("🏥 MAUDE Database Web UI")
    print("="*60)
    print(f"Starting server at http://{host}:{port}")
    print("\nPress Ctrl+C to stop the server")
    print("="*60)
    
    app.run(
        host=host,
        port=port,
        debug=True
    )
