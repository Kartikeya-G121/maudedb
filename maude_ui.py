#!/usr/bin/env python3
"""
MAUDE Database Web UI - with Subscriptions
"""

import os, json, uuid
from datetime import datetime, date, timedelta
from io import StringIO
from pathlib import Path

import dash
from dash import dcc, html, dash_table, Input, Output, State, ctx
import dash_bootstrap_components as dbc
from dotenv import load_dotenv
import pandas as pd
from maude_api_fetch import MAUDEFetcher
from canada_fetch import CanadaRecallsFetcher, DEVICE_CATEGORIES

load_dotenv()

SUBS_FILE = Path(__file__).parent / "subscriptions.json"

app = dash.Dash(__name__, external_stylesheets=[dbc.themes.BOOTSTRAP],
                suppress_callback_exceptions=True)

api_key        = os.getenv("FDA_API_KEY")
fetcher        = MAUDEFetcher(api_key=api_key)
canada_fetcher = CanadaRecallsFetcher()

# ── Subscription file helpers ─────────────────────────────────────────────────

def load_subs():
    if SUBS_FILE.exists():
        try: return json.loads(SUBS_FILE.read_text())
        except: return []
    return []

def save_subs(subs):
    SUBS_FILE.write_text(json.dumps(subs, indent=2))

def sub_to_query(sub):
    parts = []
    if sub.get("device"):
        parts.append(f'device.generic_name:"{sub["device"].strip().replace(" ","+")}"')
    if sub.get("manufacturer"):
        parts.append(f'device.manufacturer_d_name:"{sub["manufacturer"].strip().replace(" ","+")}"')
    if sub.get("event_type"):
        parts.append(f'event_type:"{sub["event_type"]}"')
    return "+AND+".join(parts)

def _fmt(d):
    if isinstance(d, str): d = date.fromisoformat(d)
    return d.strftime("%Y%m%d")

def build_query(date_from, date_to, device, manufacturer, event_type):
    parts = []
    if date_from and date_to:
        parts.append(f"date_received:[{_fmt(date_from)}+TO+{_fmt(date_to)}]")
    elif date_from:
        parts.append(f"date_received:[{_fmt(date_from)}+TO+99991231]")
    elif date_to:
        parts.append(f"date_received:[19000101+TO+{_fmt(date_to)}]")
    if device and device.strip():
        parts.append(f'device.generic_name:"{device.strip().replace(" ","+")}"')
    if manufacturer and manufacturer.strip():
        parts.append(f'device.manufacturer_d_name:"{manufacturer.strip().replace(" ","+")}"')
    if event_type and event_type.strip():
        parts.append(f'event_type:"{event_type}"')
    return "+AND+".join(parts) if parts else 'event_type:"Malfunction"'

def render_sub_card(sub):
    country = sub.get("country", "US")  # Default to US for backward compatibility
    badges = []
    
    # Country badge
    if country == "Canada":
        badges.append(dbc.Badge("🍁 Canada", color="danger", className="me-1"))
    else:
        badges.append(dbc.Badge("🇺🇸 US", color="primary", className="me-1"))
    
    # Country-specific filter badges
    if country == "Canada":
        if sub.get("product"):
            badges.append(dbc.Badge(f"📦 {sub['product']}", color="info", className="me-1"))
        if sub.get("category"):
            badges.append(dbc.Badge(f"🏥 {sub['category']}", color="secondary", className="me-1"))
        if sub.get("recall_class"):
            cmap = {"Type I":"danger","Type II":"warning","Type III":"success"}
            badges.append(dbc.Badge(f"⚠️ {sub['recall_class']}", color=cmap.get(sub["recall_class"],"secondary"), className="me-1"))
        if sub.get("issue"):
            badges.append(dbc.Badge(f"🔧 {sub['issue']}", color="light", className="me-1"))
    else:  # US
        if sub.get("device"):
            badges.append(dbc.Badge(f"📦 {sub['device']}", color="info", className="me-1"))
        if sub.get("manufacturer"):
            badges.append(dbc.Badge(f"🏭 {sub['manufacturer']}", color="secondary", className="me-1"))
        if sub.get("event_type"):
            cmap = {"Death":"danger","Injury":"warning","Malfunction":"secondary","Other":"light"}
            badges.append(dbc.Badge(f"⚠️ {sub['event_type']}", color=cmap.get(sub["event_type"],"secondary"), className="me-1"))
        if sub.get("outcome"):
            badges.append(dbc.Badge(f"🩺 {sub['outcome']}", color="success", className="me-1"))

    created  = sub.get("created","")[:10]
    last_run = sub.get("last_run","Never")
    last_run = last_run[:16].replace("T"," ") if last_run != "Never" else "Never"
    hits     = sub.get("hit_count", 0)
    
    # Border color based on country
    border_color = "#dc3545" if country == "Canada" else "#0d6efd"

    return dbc.Card([
        dbc.CardBody([
            dbc.Row([
                dbc.Col([
                    html.H6(sub.get("name","Untitled"), className="mb-1 fw-bold"),
                    html.Div(badges, className="mb-2"),
                    html.Small([
                        html.Span(f"Created: {created}", className="text-muted me-3"),
                        html.Span(f"Last run: {last_run}", className="text-muted me-3"),
                        html.Span(f"Total hits: {hits:,}", className="text-muted"),
                    ]),
                ], width=8),
                dbc.Col([
                    dbc.Button("▶ Run Now", size="sm", color="primary",
                               id={"type":"run-sub","index":sub["id"]},
                               className="w-100 mb-1"),
                    dbc.Button("🗑 Delete", size="sm", color="outline-danger",
                               id={"type":"del-sub","index":sub["id"]},
                               className="w-100"),
                ], width=4),
            ]),
        ])
    ], className="mb-2", style={"borderLeft":f"4px solid {border_color}"})



# ── Layout ────────────────────────────────────────────────────────────────────

EVENT_OPTIONS = [
    {"label":"Any","value":""},
    {"label":"Death","value":"Death"},
    {"label":"Injury","value":"Injury"},
    {"label":"Malfunction","value":"Malfunction"},
    {"label":"Other","value":"Other"},
]

OUTCOME_OPTIONS = [
    {"label":"Any","value":""},
    {"label":"Death","value":"Death"},
    {"label":"Hospitalization","value":"Hospitalization"},
    {"label":"Life Threatening","value":"Life Threatening"},
    {"label":"Required Intervention","value":"Required Intervention"},
    {"label":"Disability","value":"Disability"},
    {"label":"Other","value":"Other"},
]

app.layout = dbc.Container([
    dbc.Row(dbc.Col([
        html.H1("🏥 Medical Device Recall Tracker", className="text-center mb-1 mt-4"),
        html.P("Track medical device recalls and adverse events from US FDA and Health Canada",
               className="text-center text-muted mb-3"),
    ])),

    dbc.Tabs(id="main-tabs", active_tab="tab-search", children=[

        # ── US FDA SEARCH TAB ─────────────────────────────────────────────────
        dbc.Tab(label="🇺🇸 US (FDA MAUDE)", tab_id="tab-search", children=[
            dbc.Row([
                dbc.Col([
                    # Date range
                    dbc.Card([
                        dbc.CardHeader(html.H6("🇺🇸 📅 Date Range Filter (US FDA)", className="mb-0 fw-bold")),
                        dbc.CardBody([
                            dbc.Row([
                                dbc.Col([html.Label("From", className="fw-bold small"),
                                         dcc.DatePickerSingle(id="date-from", date=date(2024,1,1),
                                                              display_format="YYYY-MM-DD")], width=6),
                                dbc.Col([html.Label("To", className="fw-bold small"),
                                         dcc.DatePickerSingle(id="date-to", date=date(2024,1,31),
                                                              display_format="YYYY-MM-DD")], width=6),
                            ], className="mb-2"),
                            html.Label("Quick Select:", className="fw-bold small mt-1"),
                            html.Div([
                                dbc.Button("Last 7 days",  id="btn-7d",    size="sm", color="outline-secondary", className="me-1 mb-1"),
                                dbc.Button("Last 30 days", id="btn-30d",   size="sm", color="outline-secondary", className="me-1 mb-1"),
                                dbc.Button("Last 90 days", id="btn-90d",   size="sm", color="outline-secondary", className="me-1 mb-1"),
                                dbc.Button("This year",    id="btn-ytd",   size="sm", color="outline-secondary", className="me-1 mb-1"),
                                dbc.Button("Last year",    id="btn-lasty", size="sm", color="outline-secondary", className="mb-1"),
                            ]),
                            html.Div(id="date-query-preview", className="mt-2"),
                        ]),
                    ], className="mb-3"),

                    # Filters
                    dbc.Card([
                        dbc.CardHeader(html.H6("🇺🇸 🔍 Device & Event Filters", className="mb-0 fw-bold")),
                        dbc.CardBody([
                            html.Label("Device Name (generic):", className="fw-bold small"),
                            dbc.Input(id="filter-device", type="text", placeholder="e.g. pacemaker",
                                      className="mb-2", size="sm"),
                            html.Label("Manufacturer:", className="fw-bold small"),
                            dbc.Input(id="filter-manufacturer", type="text", placeholder="e.g. medtronic",
                                      className="mb-2", size="sm"),
                            html.Label("Event Type:", className="fw-bold small"),
                            dcc.Dropdown(id="filter-event-type", options=EVENT_OPTIONS,
                                         value="", clearable=False, className="mb-2"),
                        ]),
                    ], className="mb-3"),

                    # Advanced query
                    dbc.Card([
                        dbc.CardHeader(html.H6("⚙️ Advanced Query", className="mb-0 fw-bold")),
                        dbc.CardBody([
                            html.Label("Full API Query:", className="fw-bold small"),
                            dbc.Textarea(id="custom-query-input", rows=3,
                                         className="mb-2 font-monospace",
                                         style={"fontSize":"0.78rem"}),
                            dbc.Button("↺ Rebuild from filters", id="btn-rebuild-query",
                                       size="sm", color="outline-primary", className="w-100"),
                        ]),
                    ], className="mb-3"),

                    # Run + save
                    dbc.Card([
                        dbc.CardHeader(html.H6("🚀 Search US FDA Database", className="mb-0 fw-bold")),
                        dbc.CardBody([
                            html.Label("Max Results:", className="fw-bold small"),
                            dbc.Input(id="max-results-input", type="number", value=100,
                                      min=1, max=5000, step=100, className="mb-3", size="sm"),
                            dbc.Button("Search MAUDE Database", id="search-button",
                                       color="primary", className="w-100 mb-2", size="lg"),
                            dbc.Button("⬇ Export to CSV", id="export-button",
                                       color="secondary", className="w-100", disabled=True),
                            dcc.Download(id="download-csv"),
                            html.Hr(className="my-3"),
                            html.Label("💾 Save as Subscription", className="fw-bold small"),
                            dbc.Input(id="sub-name-input", type="text",
                                      placeholder="Give this subscription a name…",
                                      className="mb-2 mt-1", size="sm"),
                            dbc.Button("+ Save Subscription", id="save-sub-btn",
                                       color="outline-success", size="sm", className="w-100"),
                            html.Div(id="save-sub-feedback", className="mt-2"),
                        ]),
                    ], className="mb-3"),
                ], width=12, lg=4),

                dbc.Col([
                    html.Div(id="status-message", className="mb-3"),
                    html.Div(id="stats-cards",    className="mb-3"),
                    html.Div(id="data-table-container"),
                ], width=12, lg=8),
            ], className="mt-3"),
        ]),

        # ── SUBSCRIPTIONS TAB ─────────────────────────────────────────────────
        dbc.Tab(label="🔔 Subscriptions", tab_id="tab-subs", children=[
            dbc.Row([
                # Left: create
                dbc.Col([
                    dbc.Card([
                        dbc.CardHeader(html.H6("➕ New Subscription", className="mb-0 fw-bold")),
                        dbc.CardBody([
                            html.Label("Subscription Name *", className="fw-bold small"),
                            dbc.Input(id="new-sub-name", type="text",
                                      placeholder="e.g. Pacemaker Recalls Canada",
                                      className="mb-2", size="sm"),

                            html.Label("Country / Data Source *", className="fw-bold small"),
                            dcc.Dropdown(
                                id="new-sub-country",
                                options=[
                                    {"label": "🇺🇸 United States (FDA MAUDE)", "value": "US"},
                                    {"label": "🍁 Canada (Health Canada)", "value": "Canada"},
                                ],
                                value="US",
                                clearable=False,
                                className="mb-3",
                            ),

                            html.P("Choose what to watch:", className="fw-bold small text-muted mb-1"),
                            html.Hr(className="mt-0 mb-2"),

                            # US-specific fields
                            html.Div(id="us-sub-fields", children=[

                            html.Label("📦 Product / Device", className="fw-bold small"),
                            dbc.Input(id="new-sub-device", type="text",
                                      placeholder="e.g. pacemaker, stent, insulin pump",
                                      className="mb-2", size="sm"),

                            html.Label("🏭 Manufacturer / Company", className="fw-bold small"),
                            dbc.Input(id="new-sub-manufacturer", type="text",
                                      placeholder="e.g. medtronic, abbott, zimmer",
                                      className="mb-2", size="sm"),

                            html.Label("⚠️ Event Type", className="fw-bold small"),
                            dcc.Dropdown(id="new-sub-event-type", options=EVENT_OPTIONS,
                                         value="", clearable=False, className="mb-2"),

                            html.Label("🩺 Patient Outcome", className="fw-bold small"),
                            dcc.Dropdown(id="new-sub-outcome", options=OUTCOME_OPTIONS,
                                         value="", clearable=False, className="mb-2"),
                            ]),

                            # Canada-specific fields
                            html.Div(id="canada-sub-fields", style={"display": "none"}, children=[
                                html.Label("📦 Product / Device Name", className="fw-bold small"),
                                dbc.Input(id="new-sub-ca-product", type="text",
                                          placeholder="e.g. pacemaker, infusion pump",
                                          className="mb-2", size="sm"),

                                html.Label("🏥 Device Category", className="fw-bold small"),
                                dcc.Dropdown(
                                    id="new-sub-ca-category",
                                    options=[{"label": "All categories", "value": ""}] +
                                            [{"label": c, "value": c} for c in sorted(DEVICE_CATEGORIES)],
                                    value="",
                                    clearable=False,
                                    className="mb-2",
                                ),

                                html.Label("⚠️ Recall Class", className="fw-bold small"),
                                dcc.Dropdown(
                                    id="new-sub-ca-recall-class",
                                    options=[
                                        {"label": "All classes", "value": ""},
                                        {"label": "Type I — most serious", "value": "Type I"},
                                        {"label": "Type II — serious", "value": "Type II"},
                                        {"label": "Type III — unlikely to cause harm", "value": "Type III"},
                                    ],
                                    value="",
                                    clearable=False,
                                    className="mb-2",
                                ),

                                html.Label("🔧 Issue / Hazard", className="fw-bold small"),
                                dbc.Input(id="new-sub-ca-issue", type="text",
                                          placeholder="e.g. Performance, Sterility",
                                          className="mb-2", size="sm"),
                            ]),

                            html.Div(id="new-sub-preview", className="mb-3"),


                            dbc.Button("+ Create Subscription", id="create-sub-btn",
                                       color="success", className="w-100", size="lg"),
                            html.Div(id="create-sub-feedback", className="mt-2"),
                        ]),
                    ]),
                ], width=12, lg=4),

                # Right: list + results
                dbc.Col([
                    dbc.Row([
                        dbc.Col(html.H5("Your Subscriptions", className="fw-bold"), width=8),
                        dbc.Col(dbc.Button("🔄 Refresh List", id="refresh-all-btn",
                                           color="outline-primary", size="sm",
                                           className="w-100"), width=4),
                    ], className="mb-3 align-items-center"),
                    html.Div(id="subs-list"),
                    html.Hr(),
                    html.H6("📊 Subscription Results", className="fw-bold mt-2"),
                    html.Div(id="sub-run-status", className="mb-2"),
                    html.Div(id="sub-results-container"),
                ], width=12, lg=8),
            ], className="mt-3"),
        ]),

        # ── CANADA TAB ────────────────────────────────────────────────────────
        dbc.Tab(label="🍁 Canada (Health Canada)", tab_id="tab-canada", children=[
            dbc.Row([
                # Left: filters
                dbc.Col([
                    dbc.Card([
                        dbc.CardHeader(html.H6("🍁 🔍 Filter Canadian Recalls", className="mb-0 fw-bold")),
                        dbc.CardBody([
                            html.Label("Product / Device Name:", className="fw-bold small"),
                            dbc.Input(id="ca-filter-product", type="text",
                                      placeholder="e.g. pacemaker, infusion pump",
                                      className="mb-2", size="sm"),

                            html.Label("Device Category:", className="fw-bold small"),
                            dcc.Dropdown(
                                id="ca-filter-category",
                                options=[{"label": "All categories", "value": ""}] +
                                        [{"label": c, "value": c} for c in sorted(DEVICE_CATEGORIES)],
                                value="", clearable=False, className="mb-2",
                            ),

                            html.Label("Recall Class:", className="fw-bold small"),
                            dcc.Dropdown(
                                id="ca-filter-class",
                                options=[
                                    {"label": "All classes",                         "value": ""},
                                    {"label": "Type I   — most serious risk",         "value": "Type I"},
                                    {"label": "Type II  — serious but not immediate", "value": "Type II"},
                                    {"label": "Type III — unlikely to cause harm",    "value": "Type III"},
                                ],
                                value="", clearable=False, className="mb-2",
                            ),

                            html.Label("Issue / Hazard:", className="fw-bold small"),
                            dcc.Dropdown(
                                id="ca-filter-issue",
                                options=[
                                    {"label": "Any issue",              "value": ""},
                                    {"label": "Performance",            "value": "Performance"},
                                    {"label": "Labelling and packaging","value": "Labelling and packaging"},
                                    {"label": "Sterility",              "value": "Sterility"},
                                    {"label": "Device compatibility",   "value": "Device compatibility"},
                                    {"label": "Software",               "value": "Software"},
                                    {"label": "Electrical",             "value": "Electrical"},
                                    {"label": "Mechanical",             "value": "Mechanical"},
                                    {"label": "Material",               "value": "Material"},
                                ],
                                value="", clearable=False, className="mb-2",
                            ),
                        ]),
                    ], className="mb-3"),

                    dbc.Card([
                        dbc.CardHeader(html.H6("🍁 📅 Date Range (Last Updated)", className="mb-0 fw-bold")),
                        dbc.CardBody([
                            dbc.Row([
                                dbc.Col([
                                    html.Label("From", className="fw-bold small"),
                                    dcc.DatePickerSingle(id="ca-date-from",
                                                         display_format="YYYY-MM-DD"),
                                ], width=6),
                                dbc.Col([
                                    html.Label("To", className="fw-bold small"),
                                    dcc.DatePickerSingle(id="ca-date-to",
                                                         display_format="YYYY-MM-DD"),
                                ], width=6),
                            ], className="mb-2"),
                            dbc.Checklist(
                                id="ca-include-archived",
                                options=[{"label": " Include archived recalls", "value": "yes"}],
                                value=[], className="small",
                            ),
                        ]),
                    ], className="mb-3"),

                    dbc.Card([
                        dbc.CardHeader(html.H6("🚀 Fetch Canadian Recalls", className="mb-0 fw-bold")),
                        dbc.CardBody([
                            dbc.Button("Fetch Canada Recalls", id="ca-search-btn",
                                       color="danger", className="w-100 mb-2", size="lg"),
                            dbc.Button("⬇ Export to CSV", id="ca-export-btn",
                                       color="secondary", className="w-100", disabled=True),
                            dcc.Download(id="ca-download-csv"),
                        ]),
                    ], className="mb-3"),

                    dbc.Card([
                        dbc.CardBody([
                            html.H6("ℹ️ About this data", className="fw-bold small mb-2"),
                            html.P([
                                "Source: ",
                                html.A("Health Canada Recalls & Safety Alerts",
                                       href="https://recalls-rappels.canada.ca/en",
                                       target="_blank"),
                            ], className="small mb-1"),
                            html.P("Updated daily. Medical devices only. "
                                   "Recall class Type I = most severe risk.",
                                   className="small text-muted mb-0"),
                        ]),
                    ]),
                ], width=12, lg=4),

                # Right: stats + table
                dbc.Col([
                    html.Div(id="ca-status-message", className="mb-3"),
                    html.Div(id="ca-stats-cards",    className="mb-3"),
                    html.Div(id="ca-table-container"),
                ], width=12, lg=8),
            ], className="mt-3"),
        ]),
    ]),

    dcc.Store(id="stored-data"),
    dcc.Store(id="subs-store"),
    dcc.Store(id="ca-stored-data"),

    dbc.Row(dbc.Col(html.P([
        "🇺🇸 ",
        html.A("FDA openFDA API", href="https://open.fda.gov/apis/device/event/", target="_blank"),
        " | ",
        html.A("Query Syntax", href="https://open.fda.gov/apis/query-syntax/", target="_blank"),
        "   🍁 ",
        html.A("Health Canada Recalls", href="https://recalls-rappels.canada.ca/en", target="_blank"),
    ], className="text-center text-muted small mt-3"))),
], fluid=True)


# ── Search tab callbacks ───────────────────────────────────────────────────────

@app.callback(
    Output("date-from","date"), Output("date-to","date"),
    Input("btn-7d","n_clicks"), Input("btn-30d","n_clicks"),
    Input("btn-90d","n_clicks"), Input("btn-ytd","n_clicks"),
    Input("btn-lasty","n_clicks"),
    prevent_initial_call=True,
)
def quick_date(*_):
    today = date.today()
    t = ctx.triggered_id
    if t == "btn-7d":    return today - timedelta(days=6), today
    if t == "btn-30d":   return today - timedelta(days=29), today
    if t == "btn-90d":   return today - timedelta(days=89), today
    if t == "btn-ytd":   return date(today.year,1,1), today
    if t == "btn-lasty": return date(today.year-1,1,1), date(today.year-1,12,31)
    return dash.no_update, dash.no_update


@app.callback(
    Output("date-query-preview","children"),
    Output("custom-query-input","value"),
    Input("date-from","date"), Input("date-to","date"),
    Input("filter-device","value"), Input("filter-manufacturer","value"),
    Input("filter-event-type","value"), Input("btn-rebuild-query","n_clicks"),
)
def update_query_preview(df, dt, device, mfr, etype, _):
    q = build_query(df, dt, device, mfr, etype)
    badge = (dbc.Badge(f"📅 {df}  →  {dt}", color="info",
                       className="w-100 p-2", style={"fontSize":"0.8rem"})
             if df and dt else None)
    return badge, q


@app.callback(
    Output("stored-data","data"),
    Output("status-message","children"),
    Output("export-button","disabled"),
    Input("search-button","n_clicks"),
    State("custom-query-input","value"),
    State("max-results-input","value"),
    prevent_initial_call=True,
)
def search_maude(_, query, max_results):
    if not query or not query.strip():
        return None, dbc.Alert("Please enter or build a search query.", color="warning"), True
    try:
        results = fetcher.fetch_all(query.strip(), max_results=max_results, delay=0.3)
        if not results:
            return None, dbc.Alert("No results found.", color="warning"), True
        df  = fetcher.parse_to_dataframe(results)
        msg = dbc.Alert(f"✅ Found {len(df):,} reports.", color="success", duration=4000)
        return df.to_json(date_format="iso", orient="split"), msg, False
    except Exception as e:
        return None, dbc.Alert([html.Strong("Error: "), str(e)], color="danger"), True


@app.callback(
    Output("stats-cards","children"),
    Output("data-table-container","children"),
    Input("stored-data","data"),
)
def update_display(json_data):
    if not json_data: return None, None
    df = pd.read_json(StringIO(json_data), orient="split")

    def scard(title, val, color):
        return dbc.Col(dbc.Card(dbc.CardBody([
            html.H6(title, className="text-muted small mb-1"),
            html.H3(str(val), className=f"mb-0 text-{color}"),
        ])), width=6, lg=3)

    stats = dbc.Row([
        scard("Total Reports", f"{len(df):,}", "primary"),
        scard("Event Types",   df["event_type"].nunique(), "success"),
        scard("Device Types",  df["device_generic_name"].nunique(), "warning"),
        scard("Manufacturers", df["device_manufacturer"].nunique(), "danger"),
    ], className="mb-3")

    cols = ["report_number","date_received","date_of_event","event_type",
            "device_generic_name","device_brand_name","device_manufacturer","outcome"]
    avail = [c for c in cols if c in df.columns]
    dfd   = df[avail].copy()
    for c in ["date_received","date_of_event"]:
        if c in dfd.columns:
            dfd[c] = pd.to_datetime(dfd[c], format="%Y%m%d", errors="coerce").dt.strftime("%Y-%m-%d")
    dfd = dfd.fillna("")

    tbl = dash_table.DataTable(
        id="results-table",
        columns=[{"name":c.replace("_"," ").title(),"id":c} for c in dfd.columns],
        data=dfd.to_dict("records"),
        style_table={"overflowX":"auto"},
        style_cell={"textAlign":"left","padding":"8px","whiteSpace":"normal",
                    "height":"auto","fontSize":"0.85rem"},
        style_header={"backgroundColor":"#e9ecef","fontWeight":"bold"},
        style_data_conditional=[
            {"if":{"row_index":"odd"},"backgroundColor":"#f8f9fa"},
            {"if":{"filter_query":'{event_type} = "Death"'},"backgroundColor":"#ffe0e0","color":"#c00"},
            {"if":{"filter_query":'{event_type} = "Injury"'},"backgroundColor":"#fff3cd"},
        ],
        page_size=int(os.getenv("ROWS_PER_PAGE",25)),
        filter_action="native", sort_action="native", sort_mode="multi",
        export_format="csv", export_headers="display",
    )
    return stats, dbc.Card(dbc.CardBody([html.H5("🇺🇸 US FDA Search Results", className="card-title mb-3"), tbl]))


@app.callback(
    Output("download-csv","data"),
    Input("export-button","n_clicks"),
    State("stored-data","data"),
    prevent_initial_call=True,
)
def export_data(_, jd):
    if jd:
        df = pd.read_json(StringIO(jd), orient="split")
        ts = datetime.now().strftime("%Y%m%d_%H%M%S")
        return dcc.send_data_frame(df.to_csv, f"maude_export_{ts}.csv", index=False)


@app.callback(
    Output("save-sub-feedback","children"),
    Output("subs-store","data", allow_duplicate=True),
    Input("save-sub-btn","n_clicks"),
    State("sub-name-input","value"),
    State("filter-device","value"),
    State("filter-manufacturer","value"),
    State("filter-event-type","value"),
    prevent_initial_call=True,
)
def save_sub_from_search(_, name, device, mfr, etype):
    if not name or not name.strip():
        return dbc.Alert("Please give this subscription a name.", color="warning", duration=3000), dash.no_update
    if not any([device, mfr, etype]):
        return dbc.Alert("Set at least one filter before saving.", color="warning", duration=3000), dash.no_update
    subs = load_subs()
    subs.append({"id":str(uuid.uuid4())[:8],"name":name.strip(),
                 "device":(device or "").strip(),"manufacturer":(mfr or "").strip(),
                 "event_type":etype or "","outcome":"",
                 "created":datetime.now().isoformat(),"last_run":"","hit_count":0})
    save_subs(subs)
    return dbc.Alert(f"✅ Saved '{name}'!", color="success", duration=3000), str(datetime.now())


# ── Subscriptions tab callbacks ───────────────────────────────────────────────


@app.callback(
    Output("us-sub-fields", "style"),
    Output("canada-sub-fields", "style"),
    Input("new-sub-country", "value"),
)
def toggle_sub_fields(country):
    if country == "Canada":
        return {"display": "none"}, {"display": "block"}
    else:  # US
        return {"display": "block"}, {"display": "none"}


@app.callback(
    Output("new-sub-preview","children"),
    Input("new-sub-country","value"),
    Input("new-sub-device","value"), Input("new-sub-manufacturer","value"),
    Input("new-sub-event-type","value"), Input("new-sub-outcome","value"),
    Input("new-sub-ca-product","value"), Input("new-sub-ca-category","value"),
    Input("new-sub-ca-recall-class","value"), Input("new-sub-ca-issue","value"),
)
def preview_new_sub(country, device, mfr, etype, outcome, ca_product, ca_category, ca_recall_class, ca_issue):
    if country == "Canada":
        # Preview Canada subscription
        filters = []
        if ca_product: filters.append(f"Product: {ca_product}")
        if ca_category: filters.append(f"Category: {ca_category}")
        if ca_recall_class: filters.append(f"Class: {ca_recall_class}")
        if ca_issue: filters.append(f"Issue: {ca_issue}")
        
        if not filters:
            return html.Small("Fill in at least one field above.", className="text-muted")
        
        return dbc.Alert([
            html.Small("🍁 Canada subscription filters:", className="d-block text-muted mb-1"),
            html.Ul([html.Li(f) for f in filters], className="mb-0 small"),
        ], color="light", className="p-2")
    else:
        # Preview US subscription
        q = sub_to_query({"device":device or "","manufacturer":mfr or "","event_type":etype or ""})
        if not q:
            return html.Small("Fill in at least one field above.", className="text-muted")
        return dbc.Alert([
            html.Small("🇺🇸 US query preview:", className="d-block text-muted mb-1"),
            html.Code(q, style={"fontSize":"0.75rem","wordBreak":"break-all"}),
        ], color="light", className="p-2")




@app.callback(
    Output("create-sub-feedback","children"),
    Output("subs-store","data"),
    Input("create-sub-btn","n_clicks"),
    State("new-sub-name","value"),
    State("new-sub-country","value"),
    # US fields
    State("new-sub-device","value"),
    State("new-sub-manufacturer","value"),
    State("new-sub-event-type","value"),
    State("new-sub-outcome","value"),
    # Canada fields
    State("new-sub-ca-product","value"),
    State("new-sub-ca-category","value"),
    State("new-sub-ca-recall-class","value"),
    State("new-sub-ca-issue","value"),
    prevent_initial_call=True,
)
def create_subscription(_, name, country, device, mfr, etype, outcome, ca_product, ca_category, ca_recall_class, ca_issue):
    if not name or not name.strip():
        return dbc.Alert("A name is required.", color="warning", duration=3000), dash.no_update
    
    subs = load_subs()
    
    if country == "Canada":
        # Canada subscription
        if not any([ca_product and ca_product.strip(), ca_category and ca_category.strip(),
                    ca_recall_class and ca_recall_class.strip(), ca_issue and ca_issue.strip()]):
            return dbc.Alert("Set at least one filter.", color="warning", duration=3000), dash.no_update
        
        subs.append({
            "id": str(uuid.uuid4())[:8],
            "name": name.strip(),
            "country": "Canada",
            "product": (ca_product or "").strip(),
            "category": (ca_category or "").strip(),
            "recall_class": ca_recall_class or "",
            "issue": (ca_issue or "").strip(),
            "created": datetime.now().isoformat(),
            "last_run": "",
            "hit_count": 0
        })
    else:
        # US subscription
        if not any([device and device.strip(), mfr and mfr.strip(),
                    etype and etype.strip(), outcome and outcome.strip()]):
            return dbc.Alert("Set at least one filter.", color="warning", duration=3000), dash.no_update
        
        subs.append({
            "id": str(uuid.uuid4())[:8],
            "name": name.strip(),
            "country": "US",
            "device": (device or "").strip(),
            "manufacturer": (mfr or "").strip(),
            "event_type": etype or "",
            "outcome": outcome or "",
            "created": datetime.now().isoformat(),
            "last_run": "",
            "hit_count": 0
        })
    
    save_subs(subs)
    return dbc.Alert(f"✅ '{name}' created!", color="success", duration=3000), str(datetime.now())


@app.callback(
    Output("subs-list","children"),
    Input("subs-store","data"),
    Input("main-tabs","active_tab"),
)
def render_subs_list(_, tab):
    subs = load_subs()
    if not subs:
        return dbc.Alert(
            "No subscriptions yet. Create one on the left, or save a search from the Search tab.",
            color="light", className="text-muted",
        )
    return [render_sub_card(s) for s in subs]


@app.callback(
    Output("sub-run-status","children"),
    Output("sub-results-container","children"),
    Output("subs-store","data", allow_duplicate=True),
    Input({"type":"run-sub","index":dash.ALL},"n_clicks"),
    prevent_initial_call=True,
)
def run_subscription(n_clicks_list):
    triggered = ctx.triggered_id
    if not triggered or not any(n for n in n_clicks_list if n):
        return dash.no_update, dash.no_update, dash.no_update

    sub_id = triggered["index"]
    subs   = load_subs()
    sub    = next((s for s in subs if s["id"] == sub_id), None)
    if not sub:
        return dbc.Alert("Subscription not found.", color="danger"), None, dash.no_update

    country = sub.get("country", "US")
    
    try:
        if country == "Canada":
            # Run Canada subscription
            df = canada_fetcher.search(
                product=sub.get("product", ""),
                category=sub.get("category", ""),
                recall_class=sub.get("recall_class", ""),
                issue=sub.get("issue", ""),
                date_from="",  # No date filter for subscriptions
                date_to="",
                include_archived=False,
            )
            count = len(df) if not df.empty else 0
            
            for s in subs:
                if s["id"] == sub_id:
                    s["last_run"]  = datetime.now().isoformat()
                    s["hit_count"] = s.get("hit_count", 0) + count
            save_subs(subs)
            
            if df.empty:
                return (dbc.Alert(f"🍁 '{sub['name']}' — No Canadian recalls found.", color="info"),
                        None, str(datetime.now()))
            
            # Display Canada results
            show_cols = ["recall_id","last_updated","recall_class","product","issue","category"]
            avail     = [c for c in show_cols if c in df.columns]
            dfd       = df[avail].copy()
            
            if "last_updated" in dfd.columns:
                dfd["last_updated"] = pd.to_datetime(
                    dfd["last_updated"], errors="coerce"
                ).dt.strftime("%Y-%m-%d")
            
            dfd = dfd.fillna("")
            
            tbl = dash_table.DataTable(
                columns=[{"name":c.replace("_"," ").title(),"id":c} for c in dfd.columns],
                data=dfd.to_dict("records"),
                style_table={"overflowX":"auto"},
                style_cell={"textAlign":"left","padding":"6px","fontSize":"0.82rem"},
                style_header={"backgroundColor":"#e9ecef","fontWeight":"bold"},
                style_data_conditional=[
                    {"if":{"row_index":"odd"},"backgroundColor":"#f8f9fa"},
                    {"if":{"filter_query":'{recall_class} = "Type I"'},
                     "backgroundColor":"#ffe0e0","color":"#c00","fontWeight":"bold"},
                ],
                page_size=20, sort_action="native", filter_action="native", export_format="csv",
            )
            status = dbc.Alert(f"✅ 🍁 '{sub['name']}' — {count:,} Canadian recalls found.",
                               color="success", duration=5000)
            return status, dbc.Card(dbc.CardBody([
                html.H6(f"🍁 Results for: {sub['name']}", className="fw-bold mb-3"), tbl
            ])), str(datetime.now())
            
        else:
            # Run US subscription
            query = sub_to_query(sub)
            if not query:
                return dbc.Alert("Subscription has no valid filters.", color="warning"), None, dash.no_update

            today     = date.today()
            from_date = (today - timedelta(days=90)).strftime("%Y%m%d")
            to_date   = today.strftime("%Y%m%d")
            full_q    = f"date_received:[{from_date}+TO+{to_date}]+AND+{query}"

            results = fetcher.fetch_all(full_q, max_results=200, delay=0.3)
            count   = len(results) if results else 0

            for s in subs:
                if s["id"] == sub_id:
                    s["last_run"]  = datetime.now().isoformat()
                    s["hit_count"] = s.get("hit_count", 0) + count
            save_subs(subs)

            if not results:
                return (dbc.Alert(f"🇺🇸 '{sub['name']}' — No results in last 90 days.", color="info"),
                        None, str(datetime.now()))

            df = fetcher.parse_to_dataframe(results)
            dcols = ["report_number","date_received","event_type",
                     "device_generic_name","device_manufacturer","outcome"]
            avail = [c for c in dcols if c in df.columns]
            dfd   = df[avail].copy()
            if "date_received" in dfd.columns:
                dfd["date_received"] = pd.to_datetime(
                    dfd["date_received"], format="%Y%m%d", errors="coerce"
                ).dt.strftime("%Y-%m-%d")
            dfd = dfd.fillna("")

            tbl = dash_table.DataTable(
                columns=[{"name":c.replace("_"," ").title(),"id":c} for c in dfd.columns],
                data=dfd.to_dict("records"),
                style_table={"overflowX":"auto"},
                style_cell={"textAlign":"left","padding":"6px","fontSize":"0.82rem"},
                style_header={"backgroundColor":"#e9ecef","fontWeight":"bold"},
                style_data_conditional=[
                    {"if":{"row_index":"odd"},"backgroundColor":"#f8f9fa"},
                    {"if":{"filter_query":'{event_type} = "Death"'},"backgroundColor":"#ffe0e0","color":"#c00"},
                ],
                page_size=20, sort_action="native", filter_action="native", export_format="csv",
            )
            status = dbc.Alert(f"✅ 🇺🇸 '{sub['name']}' — {count:,} results (last 90 days).",
                               color="success", duration=5000)
            return status, dbc.Card(dbc.CardBody([
                html.H6(f"🇺🇸 Results for: {sub['name']}", className="fw-bold mb-3"), tbl
            ])), str(datetime.now())

    except Exception as e:
        return dbc.Alert([html.Strong("Error: "), str(e)], color="danger"), None, dash.no_update


@app.callback(
    Output("subs-store","data", allow_duplicate=True),
    Input({"type":"del-sub","index":dash.ALL},"n_clicks"),
    prevent_initial_call=True,
)
def delete_subscription(n_clicks_list):
    triggered = ctx.triggered_id
    if not triggered or not any(n for n in n_clicks_list if n):
        return dash.no_update
    subs = [s for s in load_subs() if s["id"] != triggered["index"]]
    save_subs(subs)
    return str(datetime.now())


@app.callback(
    Output("subs-store","data", allow_duplicate=True),
    Input("refresh-all-btn","n_clicks"),
    prevent_initial_call=True,
)
def refresh_all(_):
    return str(datetime.now())


# ── Canada tab callbacks ───────────────────────────────────────────────────────

@app.callback(
    Output("ca-stored-data",    "data"),
    Output("ca-status-message", "children"),
    Output("ca-export-btn",     "disabled"),
    Input("ca-search-btn",      "n_clicks"),
    State("ca-filter-product",  "value"),
    State("ca-filter-category", "value"),
    State("ca-filter-class",    "value"),
    State("ca-filter-issue",    "value"),
    State("ca-date-from",       "date"),
    State("ca-date-to",         "date"),
    State("ca-include-archived","value"),
    prevent_initial_call=True,
)
def fetch_canada(_, product, category, recall_class, issue, date_from, date_to, archived):
    try:
        df = canada_fetcher.search(
            product=product or "",
            category=category or "",
            recall_class=recall_class or "",
            issue=issue or "",
            date_from=date_from or "",
            date_to=date_to or "",
            include_archived="yes" in (archived or []),
        )
        if df.empty:
            return None, dbc.Alert("No recalls found matching your filters.", color="warning"), True

        msg = dbc.Alert(
            f"🍁 Found {len(df):,} Canadian medical device recalls.",
            color="success", duration=4000,
        )
        return df.to_json(date_format="iso", orient="split"), msg, False

    except Exception as e:
        return None, dbc.Alert([html.Strong("Error: "), str(e)], color="danger"), True


@app.callback(
    Output("ca-stats-cards",    "children"),
    Output("ca-table-container","children"),
    Input("ca-stored-data",     "data"),
)
def update_canada_display(json_data):
    if not json_data:
        return None, None

    df = pd.read_json(StringIO(json_data), orient="split")
    stats_data = canada_fetcher.summary_stats(df)

    def scard(title, val, color, border=""):
        style = {"borderTop": f"4px solid {border}"} if border else {}
        return dbc.Col(dbc.Card(dbc.CardBody([
            html.H6(title, className="text-muted small mb-1"),
            html.H3(str(val), className=f"mb-0 text-{color}"),
        ]), style=style), width=6, lg=3)

    stats = dbc.Row([
        scard("Total Recalls",   stats_data["total"],      "primary"),
        scard("Type I",          stats_data["type_i"],     "danger",  "#dc3545"),
        scard("Type II",         stats_data["type_ii"],    "warning", "#ffc107"),
        scard("Type III",        stats_data["type_iii"],   "success", "#198754"),
    ], className="mb-3")

    # Display columns
    show_cols = ["recall_id","last_updated","recall_class","product","issue","category","url"]
    avail     = [c for c in show_cols if c in df.columns]
    dfd       = df[avail].copy()

    if "last_updated" in dfd.columns:
        dfd["last_updated"] = pd.to_datetime(
            dfd["last_updated"], errors="coerce"
        ).dt.strftime("%Y-%m-%d")

    dfd = dfd.fillna("")

    col_defs = []
    for c in dfd.columns:
        if c == "url":
            col_defs.append({"name": "Detail Link", "id": c, "presentation": "markdown"})
            dfd[c] = dfd[c].apply(lambda u: f"[View ↗]({u})" if u else "")
        else:
            col_defs.append({"name": c.replace("_", " ").title(), "id": c})

    table = dash_table.DataTable(
        id="ca-results-table",
        columns=col_defs,
        data=dfd.to_dict("records"),
        style_table={"overflowX": "auto"},
        style_cell={"textAlign":"left","padding":"8px","whiteSpace":"normal",
                    "height":"auto","fontSize":"0.85rem"},
        style_header={"backgroundColor":"#e9ecef","fontWeight":"bold"},
        style_data_conditional=[
            {"if":{"row_index":"odd"},"backgroundColor":"#f8f9fa"},
            {"if":{"filter_query":'{recall_class} = "Type I"'},
             "backgroundColor":"#ffe0e0","color":"#c00","fontWeight":"bold"},
            {"if":{"filter_query":'{recall_class} = "Type II"'},
             "backgroundColor":"#fff3cd"},
        ],
        page_size=int(os.getenv("ROWS_PER_PAGE", 25)),
        filter_action="native",
        sort_action="native",
        sort_mode="multi",
        export_format="csv",
        export_headers="display",
        markdown_options={"link_target": "_blank"},
    )

    return stats, dbc.Card(dbc.CardBody([
        html.H5("🍁 Canada Medical Device Recalls", className="card-title mb-3"),
        table,
    ]))


@app.callback(
    Output("ca-download-csv", "data"),
    Input("ca-export-btn",    "n_clicks"),
    State("ca-stored-data",   "data"),
    prevent_initial_call=True,
)
def export_canada(_, json_data):
    if json_data:
        df = pd.read_json(StringIO(json_data), orient="split")
        ts = datetime.now().strftime("%Y%m%d_%H%M%S")
        return dcc.send_data_frame(df.to_csv, f"canada_recalls_{ts}.csv", index=False)


# ── Entry point ───────────────────────────────────────────────────────────────
if __name__ == "__main__":
    host = os.getenv("UI_HOST","localhost")
    port = int(os.getenv("UI_PORT",8050))
    print("="*60)
    print("🏥 Medical Device Recall Tracker")
    print("   US FDA MAUDE + Health Canada")
    print("="*60)
    print(f"Starting server at http://{host}:{port}")
    print(f"Subscriptions stored at: {SUBS_FILE}")
    print("="*60)
    app.run(host=host, port=port, debug=True)