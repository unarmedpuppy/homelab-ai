import time
import datetime
import sqlite3
import pandas as pd
from flask import Flask, render_template
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
import os

app = Flask(__name__)

def initialize_database(db_name='tcgplayer_pricesv1.db'):
    print("Initializing database...")
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
    print(f"Fetching price data from: {url}")
    options = Options()
    options.add_argument("--headless")
    options.add_argument("--disable-gpu")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.binary_location = os.getenv("CHROME_BIN", "/usr/bin/chromium")
    
    try:
        service = Service(os.getenv("CHROMEDRIVER_BIN", "/usr/bin/chromedriver"))  # Use system-installed chromedriver
        driver = webdriver.Chrome(service=service, options=options)
        driver.set_page_load_timeout(15)  # Prevent hanging if page is slow
    except Exception as e:
        print(f"Error initializing Selenium: {e}")
        return "Unknown", 0.00, "Image not found"
    
    try:
        driver.get(url)
        time.sleep(5)  # Allow time for JavaScript to load
    except Exception as e:
        print(f"Error loading page: {e}")
        driver.quit()
        return "Unknown", 0.00, "Image not found"
    
    try:
        title = driver.find_element(By.CSS_SELECTOR, "h1[data-testid='lblProductDetailsProductName']").text.strip()
    except Exception as e:
        print(f"Error fetching title: {e}")
        title = "Unknown"
    
    try:
        price_text = driver.find_element(By.CLASS_NAME, "spotlight__price").text.strip()
        price = float(price_text.replace("$", "").replace(",", ""))
    except Exception as e:
        print(f"Error fetching price: {e}")
        price = 0.00
    
    try:
        image_element = driver.find_element(By.CLASS_NAME, "lazy-image__wrapper")
        image_url = image_element.find_element(By.TAG_NAME, "img").get_attribute("src")
    except Exception as e:
        print(f"Error fetching image: {e}")
        image_url = "Image not found"
    
    driver.quit()
    print(f"Fetched: {title} - {price} - {image_url}")
    return title, price, image_url

def save_prices_to_db(csv_file, db_name='tcgplayer_pricesv1.db'):
    print("Checking last update date...")
    today = datetime.date.today().strftime("%Y-%m-%d")
    
    conn = sqlite3.connect(db_name)
    cursor = conn.cursor()
    
    cursor.execute("SELECT MAX(date) FROM prices")
    last_update = cursor.fetchone()[0]
    
    if last_update == today:
        print("Prices already updated today. Skipping update.")
        conn.close()
        return
    
    print("Starting to process CSV file...")
    
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
def display_prices():
    print("Fetching latest prices for display...")
    initialize_database()
    conn = sqlite3.connect('tcgplayer_pricesv1.db')
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

if __name__ == "__main__":
    print("Script execution started...")
    initialize_database()
    csv_file = os.path.join(os.path.dirname(__file__), "export.csv")
    
    if not os.path.exists(csv_file):
        print(f"Error: {csv_file} not found. Please ensure the file is in the same directory.")
        exit(1)
    
    print(f"Looking for CSV file at: {csv_file}")
    save_prices_to_db(csv_file)
    
    print("Starting Flask application...")
    try:
        app.run(debug=True, use_reloader=False)
    except Exception as e:
        print(f"Flask failed to start: {e}")
