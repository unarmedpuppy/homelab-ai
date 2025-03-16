import csv
import time
import requests
from datetime import datetime
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

def get_doge_price(unix_ts):
    dt = datetime.utcfromtimestamp(unix_ts)
    date_str = dt.strftime("%d-%m-%Y")  # API expects dd-mm-yyyy
    url = f"https://api.coingecko.com/api/v3/coins/dogecoin/history?date={date_str}"
    resp = requests.get(url)
    if resp.ok:
        data = resp.json()
        return data.get("market_data", {}).get("current_price", {}).get("usd", None)
    return None

# Setup headless Chrome
chrome_opts = Options()
chrome_opts.add_argument("--headless")
chrome_opts.add_argument("--no-sandbox")
chrome_opts.add_argument("--disable-dev-shm-usage")
driver = webdriver.Chrome(options=chrome_opts)

url = "https://www.okx.com/web3/explorer/doge/address/DDriCfmsXW75ZDr1BJ38zmgb1UxXknmeWe"
driver.get(url)

# Wait for the transaction list container to load (update selector if needed)
try:
    WebDriverWait(driver, 30).until(
        EC.presence_of_element_located((By.CSS_SELECTOR, "div[data-testid='transaction-list']"))
    )
except Exception as e:
    print("Transaction list container did not load:", e)
    driver.quit()
    exit(1)

# Scroll to load all transactions
SCROLL_PAUSE_TIME = 2
last_height = driver.execute_script("return document.body.scrollHeight")
while True:
    driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
    time.sleep(SCROLL_PAUSE_TIME)
    new_height = driver.execute_script("return document.body.scrollHeight")
    if new_height == last_height:
        break
    last_height = new_height

# Wait for transaction rows to be present (update selector if needed)
try:
    tx_rows = WebDriverWait(driver, 30).until(
        EC.presence_of_all_elements_located((By.CSS_SELECTOR, "div[data-testid='tx-row']"))
    )
    print(f"Found {len(tx_rows)} transaction rows.")
except Exception as e:
    print("No transaction rows found:", e)
    tx_rows = []

transactions = []
for row in tx_rows:
    try:
        tx_hash = row.find_element(By.CSS_SELECTOR, "span[data-testid='tx-hash']").text.strip()
        timestamp_str = row.find_element(By.CSS_SELECTOR, "span[data-testid='tx-time']").text.strip()
        amount = row.find_element(By.CSS_SELECTOR, "span[data-testid='tx-amount']").text.strip()
        # Assuming the timestamp format is "MM/DD/YYYY, HH:MM:SS"
        dt = datetime.strptime(timestamp_str, "%m/%d/%Y, %H:%M:%S")
        unix_ts = int(dt.timestamp())
        price = get_doge_price(unix_ts)
        transactions.append({
            "tx_hash": tx_hash,
            "timestamp": timestamp_str,
            "amount": amount,
            "market_price_usd": price
        })
    except Exception as e:
        print("Error processing a transaction row:", e)
        continue

driver.quit()

# Write transactions to CSV
csv_file = "dogecoin_transactions.csv"
with open(csv_file, "w", newline="") as csvfile:
    fieldnames = ["tx_hash", "timestamp", "amount", "market_price_usd"]
    writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
    writer.writeheader()
    for tx in transactions:
        writer.writerow(tx)

print("CSV file '{}' created with {} transactions.".format(csv_file, len(transactions)))
