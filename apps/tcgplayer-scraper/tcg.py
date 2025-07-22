import time
import datetime
import sqlite3
import pandas as pd
from flask import Flask, render_template, request, jsonify
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
import os
import threading
import subprocess
import re
import json

app = Flask(__name__)

# Use consistent database name
DB_NAME = 'data/tcgplayer_prices.db'

def initialize_database(db_name=DB_NAME):
    print("Initializing database....")
    try:
        # Ensure data directory exists
        data_dir = os.path.dirname(db_name)
        if data_dir and not os.path.exists(data_dir):
            os.makedirs(data_dir)
            print(f"Created data directory: {data_dir}")
        
        conn = sqlite3.connect(db_name)
        cursor = conn.cursor()
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS prices (
                id INTEGER,
                date TEXT,
                product_title TEXT,
                market_price REAL,
                image_url TEXT,
                url TEXT,
                purchase_date TEXT,
                cost_basis REAL,
                PRIMARY KEY (id, date)
            )
        ''')
        conn.commit()
        conn.close()
        print("Database initialized.")
    except Exception as e:
        print(f"Error initializing database: {e}")

def extract_price_from_text(price_text):
    """Extract numeric price from various text formats"""
    if not price_text:
        return 0.00
    
    # Remove common currency symbols and formatting
    cleaned = re.sub(r'[^\d.,]', '', price_text)
    
    # Handle different decimal separators
    if ',' in cleaned and '.' in cleaned:
        # Format like "1,234.56"
        cleaned = cleaned.replace(',', '')
    elif ',' in cleaned and '.' not in cleaned:
        # Format like "1,234" or "1,234,56"
        parts = cleaned.split(',')
        if len(parts) > 2:
            # European format: "1,234,56" -> "1234.56"
            cleaned = ''.join(parts[:-1]) + '.' + parts[-1]
        else:
            # US format: "1,234" -> "1234"
            cleaned = cleaned.replace(',', '')
    
    try:
        return float(cleaned)
    except ValueError:
        return 0.00

def get_tcgplayer_price(url):
    print(f"\n=== Starting price fetch for URL: {url} ===")
    options = Options()
    options.add_argument("--headless")  # Run in headless mode for production
    options.add_argument("--disable-gpu")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--window-size=1920,1080")
    options.add_argument("--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")
    # Set Chrome binary location based on OS
    if os.name == 'posix' and os.uname().sysname == 'Darwin':  # macOS
        chrome_path = "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"
    else:
        # Docker/Linux environment
        chrome_path = os.getenv("CHROME_BIN", "/usr/bin/google-chrome-stable")
    
    options.binary_location = chrome_path
    options.add_argument("--disable-blink-features=AutomationControlled")
    options.add_experimental_option("excludeSwitches", ["enable-automation"])
    options.add_experimental_option('useAutomationExtension', False)
    
    # Additional options for Docker environment
    options.add_argument("--disable-extensions")
    options.add_argument("--disable-plugins")
    
    driver = None
    try:
        print("Initializing Chrome WebDriver...")
        service = Service(ChromeDriverManager().install())
        driver = webdriver.Chrome(service=service, options=options)
        driver.set_page_load_timeout(30)
        print("WebDriver initialized successfully")
    except Exception as e:
        print(f"Error initializing Selenium: {e}")
        return "Unknown", 0.00, "Image not found"
    
    try:
        print(f"Loading URL: {url}")
        driver.get(url)
        
        # Wait for page to load with explicit wait
        wait = WebDriverWait(driver, 30)
        
        # Wait for the app to load (look for the main app div)
        try:
            wait.until(EC.presence_of_element_located((By.ID, "app")))
            print("App container loaded")
        except:
            print("App container not found, continuing anyway")
        
        # Wait longer for JavaScript to render content
        time.sleep(10)
        
        # Try to wait for any content to appear - be more specific
        try:
            wait.until(lambda driver: len(driver.find_elements(By.CSS_SELECTOR, "h1.product-details__name")) > 0 or 
                                     len(driver.find_elements(By.CSS_SELECTOR, "[class*='market-price']")) > 0 or
                                     len(driver.find_elements(By.CSS_SELECTOR, ".lazy-image__wrapper")) > 0)
            print("Content appears to be loaded")
        except:
            print("No specific content found after waiting, continuing anyway")
            
        # Additional wait for dynamic content
        time.sleep(3)
        
        # Save page source for debugging
        with open('debug_page_source.html', 'w', encoding='utf-8') as f:
            f.write(driver.page_source)
        print("Page source saved to debug_page_source.html")
        
        # Take a screenshot for debugging
        driver.save_screenshot('debug_screenshot.png')
        print("Screenshot saved to debug_screenshot.png")
        
        # Debug: Check what elements are actually present
        print(f"Debug: Found {len(driver.find_elements(By.TAG_NAME, 'h1'))} h1 elements")
        print(f"Debug: Found {len(driver.find_elements(By.CSS_SELECTOR, '[class*=\"price\"]'))} price elements")
        print(f"Debug: Found {len(driver.find_elements(By.CSS_SELECTOR, '[class*=\"image\"]'))} image elements")
        print(f"Debug: Found {len(driver.find_elements(By.CSS_SELECTOR, '.lazy-image__wrapper'))} lazy-image__wrapper elements")
        
        # Debug: Print first few h1 elements if any exist
        h1_elements = driver.find_elements(By.TAG_NAME, 'h1')
        if h1_elements:
            print("Debug: First few h1 elements:")
            for i, h1 in enumerate(h1_elements[:3]):
                print(f"  {i+1}: '{h1.text}' (class: {h1.get_attribute('class')})")
        
    except Exception as e:
        print(f"Error loading page: {e}")
        if driver:
            driver.quit()
        return "Unknown", 0.00, "Image not found"
    
    try:
        print("\nAttempting to find title...")
        # Updated title selectors for current TCGPlayer site
        title_selectors = [
            "h1.product-details__name",  # Primary selector as mentioned
            "h1[class*='product-details__name']",
            "h1[class*='product-title']",
            "h1[class*='product-name']",
            "h1[class*='product__name']",
            "h1[class*='ProductDetails__name']",
            "h1[class*='ProductDetails__title']",
            "h1[class*='spotlight__title']",
            "h1[class*='ProductTitle']",
            "[data-testid*='product-title']",
            "[class*='product-title']",
            "h1",  # Fallback to any h1
        ]
        title = "Unknown"
        for selector in title_selectors:
            try:
                print(f"Trying title selector: {selector}")
                elements = driver.find_elements(By.CSS_SELECTOR, selector)
                if elements:
                    title = elements[0].text.strip()
                    if title:  # Make sure we got actual text
                        print(f"Found title: {title}")
                        break
            except Exception as e:
                print(f"Error with selector {selector}: {e}")
                continue
        if title == "Unknown":
            print("Warning: Could not find title with any selector")
    except Exception as e:
        print(f"Error fetching title: {e}")
        title = "Unknown"
    
    try:
        print("\nAttempting to find price...")
        # Updated price selectors with spotlight__price as priority
        price_selectors = [
            "div[class*='spotlight__price']",  # Priority selector as mentioned
            "div[class*='spotlight__price'] span",
            "div[class*='spotlight__price'] div",
            "[data-testid*='price']",
            "[class*='market-price']",
            "[class*='price']",
            "div[class*='product-details__price'] span[class*='price']",
            "div[class*='price'] span[class*='amount']",
            "div[class*='product-price'] span[class*='price']",
            "div[class*='market-price'] span[class*='price']",
            "div[class*='price__amount']",
            "div[class*='ProductDetails__price']",
            "span[class*='ProductDetails__price']",
            "div[class*='MarketPrice']",
            "span[class*='MarketPrice']",
            "div[class*='price']",
            "span[class*='spotlight__price']",
            "[class*='spotlight__price']",  # Very broad fallback
        ]
        price = 0.00
        for selector in price_selectors:
            try:
                print(f"Trying price selector: {selector}")
                elements = driver.find_elements(By.CSS_SELECTOR, selector)
                if elements:
                    for element in elements:
                        price_text = element.text.strip()
                        print(f"Found price text: {price_text}")
                        if price_text and price_text != "$0.00" and price_text != "0.00":
                            extracted_price = extract_price_from_text(price_text)
                            if extracted_price > 0:
                                price = extracted_price
                                print(f"Parsed price: {price}")
                                break
                    if price > 0:
                        break
            except Exception as e:
                print(f"Error with selector {selector}: {e}")
                continue
        if price == 0.00:
            print("Warning: Could not find price with any selector")
    except Exception as e:
        print(f"Error fetching price: {e}")
        price = 0.00
    
    try:
        print("\nAttempting to find image...")
        # Updated image selectors
        image_selectors = [
            ".lazy-image__wrapper img",  # Primary selector as mentioned
            "div[class*='lazy-image__wrapper'] img",
            "div[class*='product-details__image'] img",
            "div[class*='product-image'] img",
            "div[class*='product__image'] img",
            "img[class*='product-image']",
            "img[class*='product__image']",
            "div[class*='ProductDetails__image'] img",
            "img[class*='ProductDetails__image']",
            "div[class*='spotlight__image'] img",
            "img[class*='spotlight__image']",
            "img[class*='product']",  # Broad fallback
        ]
        image_url = "Image not found"
        for selector in image_selectors:
            try:
                print(f"Trying image selector: {selector}")
                elements = driver.find_elements(By.CSS_SELECTOR, selector)
                if elements:
                    image_url = elements[0].get_attribute("src")
                    if image_url and image_url != "data:image/svg+xml;base64,":
                        print(f"Found image URL: {image_url}")
                        break
            except Exception as e:
                print(f"Error with selector {selector}: {e}")
                continue
        if image_url == "Image not found":
            print("Warning: Could not find image with any selector")
    except Exception as e:
        print(f"Error fetching image: {e}")
        image_url = "Image not found"
    
    if driver:
        driver.quit()
    
    print(f"\n=== Final results for {url} ===")
    print(f"Title: {title}")
    print(f"Price: {price}")
    print(f"Image URL: {image_url}")
    print("================================\n")
    
    return title, price, image_url

def save_prices_to_db(csv_file, db_name=DB_NAME, limit=None):
    print("Starting to process CSV file...")
    today = datetime.date.today().strftime("%Y-%m-%d")
    
    try:
        df = pd.read_csv(csv_file)
        print(f"Loaded {len(df)} rows from CSV file.")
        
        # Apply limit if specified
        if limit:
            df = df.head(limit)
            print(f"Limited to first {limit} items for testing.")
            
    except Exception as e:
        print(f"Error reading CSV file: {e}")
        return
    
    conn = sqlite3.connect(db_name)
    cursor = conn.cursor()
    
    processed_count = 0
    for _, row in df.iterrows():
        product_id = row['id']
        
        # Handle missing URLs - skip entries without valid URLs
        url = row.get('url', '')
        if not url or not isinstance(url, str) or not url.startswith('http'):
            print(f"Skipping ID {product_id}: No valid URL found")
            continue
            
        purchase_date = row.get('date purchased', "Unknown")
        
        raw_cost_basis = row.get('cost basis', "0.00")
        print(f"Raw cost basis for ID {product_id}: {raw_cost_basis}")
        
        try:
            cost_basis = extract_price_from_text(str(raw_cost_basis))
        except:
            cost_basis = 0.00
        
        print(f"Processed cost basis for ID {product_id}: {cost_basis}")
        
        print(f"Processing URL for ID {product_id}: {url}")
        title, price, image_url = get_tcgplayer_price(url)
        
        cursor.execute('''
            INSERT OR REPLACE INTO prices (id, date, product_title, market_price, image_url, url, purchase_date, cost_basis)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        ''', (product_id, today, title, price, image_url, url, purchase_date, cost_basis))
        print(f"Updated in DB: {title} - {price} - {cost_basis} on {today}")
        processed_count += 1
        
        # Add a small delay between requests to be respectful
        time.sleep(2)
    
    conn.commit()
    conn.close()
    print(f"Finished processing CSV file. Processed {processed_count} items.")

@app.route('/')
def dashboard():
    return render_template('dashboard.html')

@app.route('/sealed-products')
def sealed_products():
    print("Fetching latest prices for display...")
    initialize_database()
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("""
        SELECT date, product_title, market_price, image_url, url, purchase_date, cost_basis 
        FROM prices 
        WHERE (id, date) IN (
            SELECT id, MAX(date) FROM prices GROUP BY id
        ) 
        ORDER BY id ASC
    """)
    data = cursor.fetchall()
    conn.close()
    print("Data fetched successfully.")
    return render_template('prices.html', data=data)

@app.route('/decks')
def decks():
    return render_template('decks.html')

@app.route('/update-prices')
def update_prices():
    """Manual trigger for price updates"""
    try:
        csv_file = os.path.join(os.path.dirname(__file__), "export.csv")
        save_prices_to_db(csv_file)
        return jsonify({"status": "success", "message": "Price update completed successfully"})
    except Exception as e:
        return jsonify({"status": "error", "message": f"Price update failed: {str(e)}"})

@app.route('/api/prices')
def api_prices():
    """API endpoint to get current prices"""
    try:
        initialize_database()
        conn = sqlite3.connect(DB_NAME)
        cursor = conn.cursor()
        cursor.execute("""
            SELECT id, date, product_title, market_price, image_url, url, purchase_date, cost_basis 
            FROM prices 
            WHERE (id, date) IN (
                SELECT id, MAX(date) FROM prices GROUP BY id
            ) 
            ORDER BY id ASC
        """)
        data = cursor.fetchall()
        conn.close()
        
        # Convert to list of dictionaries for JSON response
        prices = []
        for row in data:
            prices.append({
                'id': row[0],
                'date': row[1],
                'product_title': row[2],
                'market_price': row[3],
                'image_url': row[4],
                'url': row[5],
                'purchase_date': row[6],
                'cost_basis': row[7]
            })
        
        return jsonify({"status": "success", "data": prices})
    except Exception as e:
        return jsonify({"status": "error", "message": f"Failed to fetch prices: {str(e)}"})

def start_price_update():
    csv_file = os.path.join(os.path.dirname(__file__), "export.csv")
    save_prices_to_db(csv_file)

if __name__ == "__main__":
    print("Script execution started...")
    initialize_database()
    
    # Start price update in background thread
    threading.Thread(target=start_price_update, daemon=True).start()
    
    print("Starting Flask application...")
    try:
        app.run(host="0.0.0.0", port=5000, debug=True, use_reloader=False)  # Disable reloader to avoid duplicate threads
    except Exception as e:
        print(f"Flask failed to start: {e}")
