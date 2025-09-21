#!/usr/bin/env python3
"""
Example usage of the stock scraper
"""

from simple_scraper import SimpleStockScraper

def main():
    scraper = SimpleStockScraper()
    
    # List of stock symbols to scrape
    symbols = ["A", "AAPL", "MSFT", "GOOGL"]
    
    for symbol in symbols:
        print(f"\n{'='*50}")
        print(f"Scraping data for {symbol}")
        print(f"{'='*50}")
        
        df = scraper.get_stock_data(symbol)
        
        if df is not None:
            print(f"Successfully scraped {len(df)} rows for {symbol}")
            print("\nFirst 3 rows:")
            print(df.head(3))
            
            # Save to CSV
            filename = scraper.save_to_csv(df, symbol)
            print(f"Data saved to: {filename}")
        else:
            print(f"Failed to scrape data for {symbol}")
        
        # Be respectful - add a small delay between requests
        import time
        time.sleep(1)

if __name__ == "__main__":
    main()
