#!/bin/bash
#
# Trading Bot API Usage Examples (cURL)
# ======================================
#
# This script demonstrates how to use the Trading Bot API from the command line.
# Set BASE_URL and API_KEY variables as needed.
#

BASE_URL="http://localhost:8000"
API_KEY=""  # Set your API key here if authentication is enabled

# Helper function to make API requests
api_request() {
    local method=$1
    local endpoint=$2
    shift 2
    local headers=()
    
    # Add API key if provided
    if [ -n "$API_KEY" ]; then
        headers+=(-H "X-API-Key: $API_KEY")
    fi
    
    # Make request
    curl -s -X "$method" "$BASE_URL$endpoint" \
        "${headers[@]}" \
        "$@" \
        -w "\n%{http_code}\n" | \
    awk 'NR==1{body=$0} NR==2{code=$0} END{
        if (code >= 200 && code < 300) {
            print body
        } else {
            print "Error " code ": " body > "/dev/stderr"
            exit 1
        }
    }'
}

# Print section header
section() {
    echo ""
    echo "============================================================"
    echo "$1"
    echo "============================================================"
}

# ==================== Sentiment Analysis ====================

section "Twitter Sentiment"
api_request GET "/api/sentiment/twitter/AAPL?hours=24" | jq '.'

section "Reddit Sentiment"
api_request GET "/api/sentiment/reddit/AAPL?hours=24" | jq '.'

section "Aggregated Sentiment"
api_request GET "/api/sentiment/aggregated/AAPL?hours=24" | jq '.'

section "Detailed Aggregated Sentiment"
api_request GET "/api/sentiment/aggregated/AAPL/detailed?hours=24" | jq '.'

# ==================== Options Flow ====================

section "Options Flow"
api_request GET "/api/options-flow/SPY?hours=24" | jq '.[0:3]'  # First 3 results

section "Sweeps"
api_request GET "/api/options-flow/SPY/sweeps?hours=24" | jq '.[0:3]'

section "Put/Call Ratio"
api_request GET "/api/options-flow/SPY/pc-ratio?hours=24" | jq '.'

section "Options Metrics"
api_request GET "/api/options-flow/SPY/metrics?hours=24" | jq '.'

# ==================== Confluence ====================

section "Confluence Score"
api_request GET "/api/confluence/AAPL?hours=24" | jq '.'

# ==================== Market Data ====================

section "Market Quote"
api_request GET "/api/market-data/quote/AAPL" | jq '.'

section "Historical Data"
api_request GET "/api/market-data/historical/AAPL?days=30&interval=1d" | jq '.[0:5]'  # First 5 days

# ==================== Monitoring ====================

section "Health Check"
api_request GET "/health" | jq '.'

section "Provider Status"
api_request GET "/api/monitoring/providers/status" | jq '.'

section "Rate Limits"
api_request GET "/api/monitoring/rate-limits" | jq '.'

# ==================== Complete Workflow Example ====================

section "Complete Trading Workflow Example"

echo "1. Check system health..."
api_request GET "/health" | jq '.status'

echo -e "\n2. Get current quote..."
api_request GET "/api/market-data/quote/AAPL" | jq '{symbol: .symbol, price: .price}'

echo -e "\n3. Get aggregated sentiment..."
api_request GET "/api/sentiment/aggregated/AAPL?hours=24" | jq '{sentiment: .unified_sentiment, confidence: .confidence}'

echo -e "\n4. Get options flow metrics..."
api_request GET "/api/options-flow/AAPL/metrics?hours=24" | jq '{bullish_flow: .bullish_flow, bearish_flow: .bearish_flow}'

echo -e "\n5. Get confluence score..."
confluence=$(api_request GET "/api/confluence/AAPL?hours=24")
echo "$confluence" | jq '{confluence_score: .confluence_score, meets_threshold: .meets_minimum_threshold}'

echo -e "\n6. Trading decision..."
meets_threshold=$(echo "$confluence" | jq -r '.meets_minimum_threshold')
if [ "$meets_threshold" = "true" ]; then
    echo "✅ Trade signal: BUY AAPL"
else
    echo "❌ Trade signal: HOLD"
fi

echo -e "\n============================================================"
echo "All examples completed!"
echo "============================================================"

