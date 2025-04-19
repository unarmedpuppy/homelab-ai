import time
import datetime
import sqlite3
import pandas as pd
from flask import Flask, render_template, request
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from webdriver_manager.chrome import ChromeDriverManager
import os
import threading
import subprocess

app = Flask(__name__)

def initialize_database(db_name='tcgplayer_pricesv2.db'):
    print("Initializing database....")
    try:
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

def get_tcgplayer_price(url):
    print(f"\n=== Starting price fetch for URL: {url} ===")
    options = Options()
    # options.add_argument("--headless")  # Comment this line out
    options.add_argument("--disable-gpu")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--window-size=1920,1080")  # Set a larger window size
    options.add_argument("--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36")
    options.binary_location = os.getenv("CHROME_BIN", "/usr/bin/google-chrome")
    options.add_argument("--disable-blink-features=AutomationControlled")
    options.add_experimental_option("excludeSwitches", ["enable-automation"])
    options.add_experimental_option('useAutomationExtension', False)
    
    driver = None
    try:
        print("Initializing Chrome WebDriver...")
        service = Service(ChromeDriverManager().install())
        driver = webdriver.Chrome(service=service, options=options)
        driver.set_page_load_timeout(30)  # Increased timeout
        print("WebDriver initialized successfully")
    except Exception as e:
        print(f"Error initializing Selenium: {e}")
        return "Unknown", 0.00, "Image not found"
    
    try:
        print(f"Loading URL: {url}")
        driver.get(url)
        time.sleep(10)  # Increased wait time for JavaScript to load
        
        # Save page source for debugging
        with open('debug_page_source.html', 'w', encoding='utf-8') as f:
            f.write(driver.page_source)
        print("Page source saved to debug_page_source.html")
        
        # Take a screenshot for debugging
        driver.save_screenshot('debug_screenshot.png')
        print("Screenshot saved to debug_screenshot.png")
        
    except Exception as e:
        print(f"Error loading page: {e}")
        if driver:
            driver.quit()
        return "Unknown", 0.00, "Image not found"
    
    try:
        print("\nAttempting to find title...")
        # Try multiple possible selectors for title
        title_selectors = [
            "h1[class*='product-details__name']",
            "h1[class*='product-title']",
            "h1[class*='product-name']",
            "h1[class*='product__name']",
            "h1[class*='ProductDetails__name']",
            "h1[class*='ProductDetails__title']"
        ]
        title = "Unknown"
        for selector in title_selectors:
            try:
                print(f"Trying title selector: {selector}")
                elements = driver.find_elements(By.CSS_SELECTOR, selector)
                if elements:
                    title = elements[0].text.strip()
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
        # Try multiple possible selectors for price
        price_selectors = [
            "div[class*='product-details__price'] span[class*='price']",
            "div[class*='price'] span[class*='amount']",
            "div[class*='product-price'] span[class*='price']",
            "div[class*='market-price'] span[class*='price']",
            "div[class*='price__amount']",
            "div[class*='spotlight__price']",
            "div[class*='ProductDetails__price']",
            "span[class*='ProductDetails__price']",
            "div[class*='MarketPrice']",
            "span[class*='MarketPrice']"
        ]
        price = 0.00
        for selector in price_selectors:
            try:
                print(f"Trying price selector: {selector}")
                elements = driver.find_elements(By.CSS_SELECTOR, selector)
                if elements:
                    price_text = elements[0].text.strip()
                    print(f"Found price text: {price_text}")
                    if price_text and price_text != "$0.00":
                        price = float(price_text.replace("$", "").replace(",", ""))
                        print(f"Parsed price: {price}")
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
        # Try multiple possible selectors for image
        image_selectors = [
            "div[class*='product-details__image'] img",
            "div[class*='product-image'] img",
            "div[class*='product__image'] img",
            "img[class*='product-image']",
            "img[class*='product__image']",
            "div[class*='ProductDetails__image'] img",
            "img[class*='ProductDetails__image']"
        ]
        image_url = "Image not found"
        for selector in image_selectors:
            try:
                print(f"Trying image selector: {selector}")
                elements = driver.find_elements(By.CSS_SELECTOR, selector)
                if elements:
                    image_url = elements[0].get_attribute("src")
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

def save_prices_to_db(csv_file, db_name='tcgplayer_pricesv2.db'):
    print("Starting to process CSV file...")
    today = datetime.date.today().strftime("%Y-%m-%d")
    
    try:
        df = pd.read_csv(csv_file)
        print(f"Loaded {len(df)} rows from CSV file.")
    except Exception as e:
        print(f"Error reading CSV file: {e}")
        return
    
    conn = sqlite3.connect(db_name)
    cursor = conn.cursor()
    
    for _, row in df.iterrows():
        product_id = row['id']
        url = row['url'] if isinstance(row['url'], str) and row['url'].startswith('http') else None  # Ensure valid URLs
        purchase_date = row.get('date purchased', "Unknown")
        
        raw_cost_basis = row.get('cost basis', "0.00")
        print(f"Raw cost basis for ID {product_id}: {raw_cost_basis}")
        
        try:
            cost_basis = float(str(raw_cost_basis).replace("$", "").replace(",", ""))
        except:
            cost_basis = 0.00
        
        print(f"Processed cost basis for ID {product_id}: {cost_basis}")
        
        if url:
            title, price, image_url = get_tcgplayer_price(url)
            cursor.execute('''
                INSERT OR REPLACE INTO prices (id, date, product_title, market_price, image_url, url, purchase_date, cost_basis)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ''', (product_id, today, title, price, image_url, url, purchase_date, cost_basis))
            print(f"Updated in DB: {title} - {price} - {cost_basis} on {today}")
    
    conn.commit()
    conn.close()
    print("Finished processing CSV file.")

@app.route('/')
def dashboard():
    return render_template('dashboard.html')

@app.route('/sealed-products')
def sealed_products():
    print("Fetching latest prices for display...")
    initialize_database()
    conn = sqlite3.connect('tcgplayer_pricesv2.db')
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

def start_price_update():
    csv_file = os.path.join(os.path.dirname(__file__), "export.csv")
    save_prices_to_db(csv_file)

if __name__ == "__main__":
    print("Script execution started...")
    initialize_database()
    
    threading.Thread(target=start_price_update, daemon=True).start()
    
    print("Starting Flask application...")
    try:
        app.run(host="0.0.0.0", port=5000, debug=True, use_reloader=True)
    except Exception as e:
        print(f"Flask failed to start: {e}")
