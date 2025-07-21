# TCGPlayer Price Scraper v2

A Flask web application that scrapes pricing data from TCGPlayer.com and tracks price history over time.

## Features

- **Automated Price Scraping**: Scrapes current market prices from TCGPlayer.com
- **Price History Tracking**: Stores historical price data with timestamps
- **CSV Data Source**: Uses `export.csv` as the data source for product URLs
- **Web Dashboard**: View current prices and historical trends
- **API Endpoints**: RESTful API for programmatic access
- **Manual Updates**: Trigger price updates on demand

## Setup

1. **Install Dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

2. **Prepare Data**:
   - Ensure `export.csv` contains your product data with columns: `id`, `url`, `date purchased`, `cost basis`
   - All URLs should be valid TCGPlayer.com product links

3. **Run the Application**:
   ```bash
   python tcg.py
   ```

## Usage

### Web Interface

- **Dashboard**: `http://localhost:5000/` - Main dashboard
- **Sealed Products**: `http://localhost:5000/sealed-products` - View current prices
- **Decks**: `http://localhost:5000/decks` - Deck management (placeholder)

### API Endpoints

- **Get Current Prices**: `GET /api/prices`
- **Manual Price Update**: `GET /update-prices`

### Testing

Run the test script to verify functionality:
```bash
python test_scraper.py
```

## Database Schema

The application uses SQLite with the following schema:

```sql
CREATE TABLE prices (
    id INTEGER,
    date TEXT,
    product_title TEXT,
    market_price REAL,
    image_url TEXT,
    url TEXT,
    purchase_date TEXT,
    cost_basis REAL,
    PRIMARY KEY (id, date)
);
```

## Recent Improvements

### Price Scraping Fixes

1. **Enhanced Selectors**: Added priority for `spotlight__price` class as mentioned
2. **Better Price Parsing**: Improved price extraction from various text formats
3. **Robust Error Handling**: Better handling of missing URLs and failed scrapes
4. **Database Consistency**: Fixed database name inconsistencies
5. **Rate Limiting**: Added delays between requests to be respectful

### Technical Improvements

1. **Explicit Waits**: Replaced fixed sleep with WebDriverWait for better reliability
2. **Headless Mode**: Enabled headless Chrome for production use
3. **Updated User Agent**: Modern Chrome user agent string
4. **Better Logging**: Enhanced debug output and error reporting
5. **API Endpoints**: Added RESTful API for external integrations

## Troubleshooting

### Common Issues

1. **Chrome Driver Issues**: The app uses `webdriver-manager` to automatically download the correct Chrome driver
2. **Missing Prices**: Check the debug output files (`debug_page_source.html`, `debug_screenshot.png`) for troubleshooting
3. **Rate Limiting**: The app includes 2-second delays between requests to avoid being blocked

### Debug Files

When scraping fails, the app creates:
- `debug_page_source.html`: The HTML source of the page
- `debug_screenshot.png`: A screenshot of the page

These files help diagnose selector issues and website changes.

## Docker Support

The application includes Docker support for easy deployment:

```bash
docker-compose up -d
```

## License

This project is for personal use. Please respect TCGPlayer's terms of service when scraping their website. 