#!/usr/bin/env python3
"""
Advanced Stock Data Scraper for StockAnalysis.com
Uses Selenium for JavaScript interaction and direct URL manipulation
"""

import requests
from bs4 import BeautifulSoup
import pandas as pd
import time
import json
from urllib.parse import urljoin, urlparse, parse_qs
import re
import urllib.parse
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from selenium.common.exceptions import TimeoutException, NoSuchElementException

class AdvancedStockAnalysisScraper:
    def __init__(self, use_selenium=True):
        """
        Initialize the scraper
        
        Args:
            use_selenium (bool): Whether to use Selenium for JavaScript interaction
        """
        self.use_selenium = use_selenium
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Accept-Encoding': 'gzip, deflate',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
        })
        
        if self.use_selenium:
            self._setup_selenium()
    
    def _setup_selenium(self):
        """Setup Selenium WebDriver"""
        chrome_options = Options()
        chrome_options.add_argument('--headless')  # Run in background
        chrome_options.add_argument('--no-sandbox')
        chrome_options.add_argument('--disable-dev-shm-usage')
        chrome_options.add_argument('--disable-gpu')
        chrome_options.add_argument('--window-size=1920,1080')
        
        try:
            self.driver = webdriver.Chrome(options=chrome_options)
            self.driver.implicitly_wait(10)
        except Exception as e:
            print(f"Warning: Could not initialize Selenium: {e}")
            print("Falling back to requests-only mode")
            self.use_selenium = False
    
    def get_stock_data(self, symbol, period='1y'):
        """
        Get historical stock data for a given symbol
        
        Args:
            symbol (str): Stock symbol (e.g., 'A', 'AAPL')
            period (str): Time period - '1y' for 1 year, '6m' for 6 months, 'daily' for daily
            
        Returns:
            pandas.DataFrame: Historical stock data
        """
        if self.use_selenium:
            return self._get_data_with_selenium(symbol, period)
        else:
            return self._get_data_with_requests(symbol, period)
    
    def _get_data_with_selenium(self, symbol, period):
        """Get data using Selenium for JavaScript interaction"""
        base_url = f"https://stockanalysis.com/stocks/{symbol.lower()}/history/"
        
        try:
            print(f"Fetching data for {symbol} with Selenium...")
            self.driver.get(base_url)
            
            # Wait for the page to load
            WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.TAG_NAME, "table"))
            )
            
            # Try to click on the 1 year button
            if period == '1y':
                self._click_date_range_button('1 year')
            
            # Wait a moment for the page to update
            time.sleep(2)
            
            # Get the updated page source
            soup = BeautifulSoup(self.driver.page_source, 'html.parser')
            
            # Extract data from the table
            table = self._find_data_table(soup)
            if table is None:
                print("Could not find historical data table")
                return None
            
            data = self._extract_table_data(table)
            if not data:
                print("No data extracted from table")
                return None
            
            df = pd.DataFrame(data)
            df = self._clean_data(df)
            
            print(f"Successfully extracted {len(df)} rows of data")
            return df
            
        except Exception as e:
            print(f"Error with Selenium: {e}")
            return None
    
    def _get_data_with_requests(self, symbol, period):
        """Get data using requests (fallback method)"""
        base_url = f"https://stockanalysis.com/stocks/{symbol.lower()}/history/"
        
        # Try different URL patterns for different periods
        if period == '1y':
            # Try various URL patterns that might work
            urls_to_try = [
                base_url,
                f"{base_url}?period=1y",
                f"{base_url}?range=1y",
                f"{base_url}?timeframe=1y",
                f"{base_url}?period=1Y",
                f"{base_url}?range=1Y",
                f"{base_url}?timeframe=1Y"
            ]
        else:
            urls_to_try = [base_url]
        
        for url in urls_to_try:
            try:
                print(f"Trying URL: {url}")
                response = self.session.get(url)
                response.raise_for_status()
                
                soup = BeautifulSoup(response.content, 'html.parser')
                table = self._find_data_table(soup)
                
                if table is not None:
                    data = self._extract_table_data(table)
                    if data:
                        df = pd.DataFrame(data)
                        df = self._clean_data(df)
                        print(f"Successfully extracted {len(df)} rows of data from {url}")
                        return df
                
            except Exception as e:
                print(f"Error with URL {url}: {e}")
                continue
        
        print("All URL attempts failed")
        return None
    
    def _click_date_range_button(self, button_text):
        """Click on a date range button"""
        try:
            # Look for buttons or links with the specified text
            elements = self.driver.find_elements(By.XPATH, f"//*[contains(text(), '{button_text}')]")
            
            for element in elements:
                try:
                    # Scroll to element and click
                    self.driver.execute_script("arguments[0].scrollIntoView();", element)
                    time.sleep(0.5)
                    element.click()
                    print(f"Clicked on {button_text} button")
                    return True
                except Exception as e:
                    print(f"Could not click element: {e}")
                    continue
            
            # Alternative: look for buttons with specific attributes
            buttons = self.driver.find_elements(By.TAG_NAME, "button")
            for button in buttons:
                if button_text.lower() in button.text.lower():
                    try:
                        self.driver.execute_script("arguments[0].scrollIntoView();", button)
                        time.sleep(0.5)
                        button.click()
                        print(f"Clicked on {button_text} button")
                        return True
                    except Exception as e:
                        continue
            
            print(f"Could not find {button_text} button")
            return False
            
        except Exception as e:
            print(f"Error clicking date range button: {e}")
            return False
    
    def _find_data_table(self, soup):
        """Find the historical data table in the HTML"""
        # Look for tables with historical data
        tables = soup.find_all('table')
        
        for table in tables:
            # Check if this looks like a historical data table
            headers = table.find_all('th')
            if headers:
                header_text = ' '.join([th.get_text().strip() for th in headers])
                if any(word in header_text.lower() for word in ['date', 'open', 'high', 'low', 'close']):
                    return table
        
        # Alternative: look for specific div or section containing the table
        historical_section = soup.find('h2', string=re.compile(r'Historical Data', re.I))
        if historical_section:
            # Look for table in the same section or nearby
            parent = historical_section.parent
            while parent and parent.name != 'body':
                table = parent.find('table')
                if table:
                    return table
                parent = parent.parent
        
        return None
    
    def _extract_table_data(self, table):
        """Extract data from the HTML table"""
        data = []
        rows = table.find_all('tr')
        
        if not rows:
            return data
            
        # Get headers
        headers = []
        header_row = rows[0]
        for th in header_row.find_all(['th', 'td']):
            headers.append(th.get_text().strip())
        
        # Extract data rows
        for row in rows[1:]:
            cells = row.find_all(['td', 'th'])
            if len(cells) >= len(headers):
                row_data = {}
                for i, cell in enumerate(cells):
                    if i < len(headers):
                        row_data[headers[i]] = cell.get_text().strip()
                data.append(row_data)
        
        return data
    
    def _clean_data(self, df):
        """Clean and format the extracted data"""
        if df.empty:
            return df
            
        # Clean column names
        df.columns = [col.strip() for col in df.columns]
        
        # Convert date column
        if 'Date' in df.columns:
            df['Date'] = pd.to_datetime(df['Date'], errors='coerce')
        
        # Convert numeric columns
        numeric_columns = ['Open', 'High', 'Low', 'Close', 'Adj. Close', 'Volume']
        for col in numeric_columns:
            if col in df.columns:
                # Remove commas and convert to numeric
                df[col] = df[col].str.replace(',', '').str.replace('$', '')
                df[col] = pd.to_numeric(df[col], errors='coerce')
        
        # Handle percentage change column
        if 'Change' in df.columns:
            df['Change'] = df['Change'].str.replace('%', '')
            df['Change'] = pd.to_numeric(df['Change'], errors='coerce')
        
        # Sort by date (newest first)
        if 'Date' in df.columns:
            df = df.sort_values('Date', ascending=False)
        
        return df
    
    def save_to_csv(self, df, symbol, filename=None):
        """Save DataFrame to CSV file"""
        if filename is None:
            filename = f"{symbol}_historical_data.csv"
        
        df.to_csv(filename, index=False)
        print(f"Data saved to {filename}")
        return filename
    
    def close(self):
        """Close the Selenium driver if it exists"""
        if hasattr(self, 'driver'):
            self.driver.quit()

def main():
    """Main function to demonstrate usage"""
    # Try with Selenium first, fall back to requests if it fails
    scraper = AdvancedStockAnalysisScraper(use_selenium=True)
    
    try:
        # Example: Get data for Agilent Technologies (A)
        symbol = "A"
        df = scraper.get_stock_data(symbol, period='1y')
        
        if df is not None:
            print("\nFirst 5 rows of data:")
            print(df.head())
            
            print(f"\nData shape: {df.shape}")
            print(f"Columns: {list(df.columns)}")
            
            # Save to CSV
            scraper.save_to_csv(df, symbol)
        else:
            print("Failed to retrieve data")
    
    finally:
        scraper.close()

if __name__ == "__main__":
    main()
