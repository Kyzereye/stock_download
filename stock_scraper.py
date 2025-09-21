#!/usr/bin/env python3
"""
Stock Data Scraper for StockAnalysis.com
Scrapes historical stock data and can modify date ranges
"""

import requests
from bs4 import BeautifulSoup
import pandas as pd
import time
import json
from urllib.parse import urljoin, urlparse, parse_qs
import re
import urllib.parse

class StockAnalysisScraper:
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Accept-Encoding': 'gzip, deflate',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
        })
        
    def get_stock_data(self, symbol, period='1y'):
        """
        Get historical stock data for a given symbol
        
        Args:
            symbol (str): Stock symbol (e.g., 'A', 'AAPL')
            period (str): Time period - '1y' for 1 year, '6m' for 6 months, 'daily' for daily
            
        Returns:
            pandas.DataFrame: Historical stock data
        """
        base_url = f"https://stockanalysis.com/stocks/{symbol.lower()}/history/"
        
        try:
            print(f"Fetching data for {symbol} with period {period}...")
            
            # First, get the initial page to understand the structure
            response = self.session.get(base_url)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Try to find and interact with date range buttons
            updated_url = self._handle_date_range_selection(soup, base_url, period)
            
            # Get the page with the selected date range
            if updated_url != base_url:
                print(f"Fetching data with updated URL: {updated_url}")
                response = self.session.get(updated_url)
                response.raise_for_status()
                soup = BeautifulSoup(response.content, 'html.parser')
            
            # Look for the historical data table
            table = self._find_data_table(soup)
            
            if table is None:
                print("Could not find historical data table")
                return None
                
            # Extract data from the table
            data = self._extract_table_data(table)
            
            if not data:
                print("No data extracted from table")
                return None
                
            # Convert to DataFrame
            df = pd.DataFrame(data)
            
            # Clean and format the data
            df = self._clean_data(df)
            
            print(f"Successfully extracted {len(df)} rows of data")
            return df
            
        except requests.RequestException as e:
            print(f"Error fetching data: {e}")
            return None
        except Exception as e:
            print(f"Unexpected error: {e}")
            return None
    
    def _handle_date_range_selection(self, soup, base_url, period):
        """
        Handle date range selection by finding the appropriate URL or parameters
        
        Args:
            soup: BeautifulSoup object of the page
            base_url: Base URL for the stock history page
            period: Desired period ('1y', '6m', 'daily')
            
        Returns:
            str: Updated URL with the selected period
        """
        # Look for buttons or links that control the date range
        # Common patterns: buttons with data attributes, links with query parameters
        
        # Method 1: Look for buttons with specific text or data attributes
        buttons = soup.find_all(['button', 'a'], string=re.compile(r'1\s*year|1\s*y|year', re.I))
        if buttons:
            for button in buttons:
                if 'href' in button.attrs:
                    return urljoin(base_url, button['href'])
                elif 'data-url' in button.attrs:
                    return urljoin(base_url, button['data-url'])
        
        # Method 2: Look for JavaScript functions or API endpoints
        scripts = soup.find_all('script')
        for script in scripts:
            if script.string:
                # Look for API endpoints or URL patterns
                api_matches = re.findall(r'["\']([^"\']*api[^"\']*history[^"\']*)["\']', script.string)
                if api_matches:
                    api_url = api_matches[0]
                    if not api_url.startswith('http'):
                        api_url = urljoin(base_url, api_url)
                    
                    # Try to modify the API URL for different periods
                    if period == '1y':
                        # Common patterns for 1 year: ?period=1y, ?range=1y, ?timeframe=1y
                        if '?' in api_url:
                            api_url += f"&period=1y"
                        else:
                            api_url += f"?period=1y"
                        return api_url
        
        # Method 3: Try common URL patterns for different periods
        if period == '1y':
            # Try different common patterns
            patterns = [
                f"{base_url}?period=1y",
                f"{base_url}?range=1y", 
                f"{base_url}?timeframe=1y",
                f"{base_url}?period=1Y",
                f"{base_url}?range=1Y",
                f"{base_url}?timeframe=1Y"
            ]
            
            # Test which pattern works by making a quick request
            for pattern in patterns:
                try:
                    test_response = self.session.head(pattern)
                    if test_response.status_code == 200:
                        return pattern
                except:
                    continue
        
        # If no specific period handling found, return original URL
        return base_url
    
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

def main():
    """Main function to demonstrate usage"""
    scraper = StockAnalysisScraper()
    
    # Example: Get data for Agilent Technologies (A)
    symbol = "A"
    df = scraper.get_stock_data(symbol)
    
    if df is not None:
        print("\nFirst 5 rows of data:")
        print(df.head())
        
        print(f"\nData shape: {df.shape}")
        print(f"Columns: {list(df.columns)}")
        
        # Save to CSV
        scraper.save_to_csv(df, symbol)
    else:
        print("Failed to retrieve data")

if __name__ == "__main__":
    main()
