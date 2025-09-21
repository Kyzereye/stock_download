#!/usr/bin/env python3
"""
Simple Stock Data Scraper for StockAnalysis.com
A lightweight version that focuses on the basic functionality
"""

import requests
from bs4 import BeautifulSoup
import pandas as pd
import re
from urllib.parse import urljoin

class SimpleStockScraper:
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        })
    
    def get_stock_data(self, symbol):
        """
        Get historical stock data for a given symbol
        
        Args:
            symbol (str): Stock symbol (e.g., 'A', 'AAPL')
            
        Returns:
            pandas.DataFrame: Historical stock data
        """
        url = f"https://stockanalysis.com/stocks/{symbol.lower()}/history/"
        
        try:
            print(f"Fetching data for {symbol}...")
            response = self.session.get(url)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Find the historical data table
            table = soup.find('table')
            
            if not table:
                print("No table found on the page")
                return None
            
            # Extract data
            data = []
            rows = table.find_all('tr')
            
            if not rows:
                return None
            
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
            
            if not data:
                print("No data extracted")
                return None
            
            # Convert to DataFrame
            df = pd.DataFrame(data)
            
            # Clean the data
            df = self._clean_data(df)
            
            print(f"Successfully extracted {len(df)} rows of data")
            return df
            
        except Exception as e:
            print(f"Error: {e}")
            return None
    
    def _clean_data(self, df):
        """Clean and format the data"""
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
                # Remove commas and dollar signs
                df[col] = df[col].str.replace(',', '').str.replace('$', '')
                df[col] = pd.to_numeric(df[col], errors='coerce')
        
        # Handle percentage change
        if 'Change' in df.columns:
            df['Change'] = df['Change'].str.replace('%', '')
            df['Change'] = pd.to_numeric(df['Change'], errors='coerce')
        
        return df
    
    def save_to_csv(self, df, symbol, filename=None):
        """Save to CSV file"""
        if filename is None:
            filename = f"{symbol}_stock_data.csv"
        
        df.to_csv(filename, index=False)
        print(f"Data saved to {filename}")
        return filename

def main():
    """Example usage"""
    scraper = SimpleStockScraper()
    
    # Get data for Agilent Technologies (A)
    df = scraper.get_stock_data("A")
    
    if df is not None:
        print("\nData preview:")
        print(df.head())
        print(f"\nShape: {df.shape}")
        
        # Save to CSV
        scraper.save_to_csv(df, "A")

if __name__ == "__main__":
    main()
