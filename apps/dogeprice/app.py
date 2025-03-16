from flask import Flask, send_file
import csv
import time
import requests
from datetime import datetime
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By

app = Flask(__name__)

def get_doge_price(unix_ts):
    dt = datetime.utcfromtimestamp(unix_ts)
    date_str = dt.strftime("%d-%m-%Y")  # API expects dd-mm-yyyy
    url = f"https://api.coingecko.com/api/v3/coins/dogecoin/history?date={date_str}"
    resp = requests.get(url)
    if resp.ok:
        data = resp.json()
        return data.get("market_data", {}).get("current_price", {}).get("usd", None)
    return None

def scrape_data():
    chrome_opts = Options()
    chrome_opts.add_argument("--headless")
    chrome_opts.add_argument("--no-sandbox")
    chrome_opts.add_argument("--disable-dev-shm-usage")
    driver = webdriver.Chrome(options=chrome_opts)
    url = "https://www.okx.com/web3/explorer/doge/address/DDriCfmsXW75ZDr1BJ38zmgb1UxXknmeWe"
    driver.get(url)
    time.sleep(5)  # Allow JS to load
    SCROLL_PAUSE_TIME = 2
    last_height = driver.execute_script("return document.body.scrollHeight")
    while True:
        driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        time.sleep(SCROLL_PAUSE_TIME)
        new_height = driver.execute_script("return document.body.scrollHeight")
        if new_height == last_height:
            break
        last_height = new_height

    tx_rows = driver.find_elements(By.CSS_SELECTOR, "div[data-testid='tx-row']")
    transactions = []
    for row in tx_rows:
        try:
            tx_hash = row.find_element(By.CSS_SELECTOR, "span[data-testid='tx-hash']").text.strip()
            timestamp_str = row.find_element(By.CSS_SELECTOR, "span[data-testid='tx-time']").text.strip()
            amount = row.find_element(By.CSS_SELECTOR, "span[data-testid='tx-amount']").text.strip()
            dt = datetime.strptime(timestamp_str, "%m/%d/%Y, %H:%M:%S")
            unix_ts = int(dt.timestamp())
            price = get_doge_price(unix_ts)
            transactions.append({
                "tx_hash": tx_hash,
                "timestamp": timestamp_str,
                "amount": amount,
                "market_price_usd": price
            })
        except Exception:
            continue
    driver.quit()

    csv_file = "dogecoin_transactions.csv"
    with open(csv_file, "w", newline="") as csvfile:
        fieldnames = ["tx_hash", "timestamp", "amount", "market_price_usd"]
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()
        for tx in transactions:
            writer.writerow(tx)
    return csv_file

@app.route("/")
def index():
    csv_file = scrape_data()
    # Read CSV content and show in a preformatted block
    with open(csv_file, "r") as f:
        csv_content = f.read()
    return f"""
    <html>
      <head><title>Dogecoin Transactions</title></head>
      <body>
        <h1>Dogecoin Transactions CSV</h1>
        <pre>{csv_content}</pre>
        <a href="/download">Download CSV</a>
      </body>
    </html>
    """

@app.route("/download")
def download():
    return send_file("dogecoin_transactions.csv", as_attachment=True)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
