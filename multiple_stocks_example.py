#!/usr/bin/env python3
"""
Example usage of the StockDataScraper with multiple ticker symbols
Gets 1 year of historical data from Yahoo Finance
"""

from stock_scraper import StockDataScraper

def main():
    """Example of using the scraper with multiple ticker symbols"""
    # Create scraper - files will be saved to csv_files directory
    scraper = StockDataScraper()
    
    # Load stock symbols from file instead of hardcoding
    symbols = scraper.load_symbols_from_file("stock_symbols.txt")
    
    if not symbols:
        print("No symbols found in stock_symbols.txt. Please add symbols to the file.")
        return
    
    print(f"Fetching 1 year of data for {len(symbols)} stocks...")
    print(f"Files will be saved to: csv_files/ directory")
    
    # Get data for all symbols (1 year of data with 1 second delay between requests)
    stock_data = scraper.get_multiple_stocks_data(symbols, period='1y', delay=1.0)
    
    if stock_data:
        # Print summary
        print(f"\n=== Successfully retrieved 1 year of data for {len(stock_data)} stocks ===")
        for symbol, df in stock_data.items():
            if not df.empty and 'Date' in df.columns:
                min_date = df['Date'].min()
                max_date = df['Date'].max()
                print(f"  {symbol}: {len(df)} rows ({min_date} to {max_date})")
            else:
                print(f"  {symbol}: No data")
        
        # Save individual files
        scraper.save_multiple_to_csv(stock_data, individual_files=True)
        
        # Save combined file
        scraper.save_multiple_to_csv(
            stock_data, 
            individual_files=False, 
            combined_file="portfolio_1year_data.csv"
        )
        
        print("\n✅ All 1 year data saved successfully!")
    else:
        print("❌ Failed to retrieve any stock data")

if __name__ == "__main__":
    main()
