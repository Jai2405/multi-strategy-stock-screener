import requests
from bs4 import BeautifulSoup, Tag
import pandas as pd
import time
import logging
from typing import Dict, List, Set, Optional, Tuple, Union
from dataclasses import dataclass
from enum import Enum
import sys
from urllib.parse import urljoin, urlparse

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('finance_agent.log')
    ]
)
logger = logging.getLogger(__name__)


class StrategyType(Enum):
    """Enumeration of available investment strategies"""
    STRATEGY1 = "Strategy1"
    STRATEGY2 = "Strategy2"
    STRATEGY3 = "Strategy3"
    STRATEGY4 = "Strategy4"
    STRATEGY5 = "Strategy5"
    STRATEGY6A = "Strategy6a"
    STRATEGY6B = "Strategy6b"


@dataclass
class StrategyConfig:
    """Configuration for a single strategy"""
    name: str
    url: str
    display_name: str
    short_name: str


@dataclass
class StockData:
    """Represents a single stock with its data"""
    name: str
    cmp: str
    strategies: List[str]
    strategy_count: int
    
    def to_dict(self) -> Dict[str, Union[str, int]]:
        """Convert to dictionary for API responses"""
        return {
            'Name': self.name,
            'CMPRs.': self.cmp,
            'Strategies_Count': self.strategy_count,
            'Strategies': ', '.join(self.strategies)
        }


class StrategyManager:
    """Manages all strategy configurations and mappings"""
    
    def __init__(self):
        self.strategies: Dict[str, StrategyConfig] = {
            StrategyType.STRATEGY1.value: StrategyConfig(
                name="Strategy1",
                url="https://www.screener.in/screens/2902497/strategy1/",
                display_name="Strategy 1",
                short_name="S1"
            ),
            StrategyType.STRATEGY2.value: StrategyConfig(
                name="Strategy2",
                url="https://www.screener.in/screens/2902503/strategy2/",
                display_name="Strategy 2",
                short_name="S2"
            ),
            StrategyType.STRATEGY3.value: StrategyConfig(
                name="Strategy3",
                url="https://www.screener.in/screens/2902506/strategy3/",
                display_name="Strategy 3",
                short_name="S3"
            ),
            StrategyType.STRATEGY4.value: StrategyConfig(
                name="Strategy4",
                url="https://www.screener.in/screens/2902508/strategy4/",
                display_name="Strategy 4",
                short_name="S4"
            ),
            StrategyType.STRATEGY5.value: StrategyConfig(
                name="Strategy5",
                url="https://www.screener.in/screens/2902511/strategy5/",
                display_name="Strategy 5",
                short_name="S5"
            ),
            StrategyType.STRATEGY6A.value: StrategyConfig(
                name="Strategy6a",
                url="https://www.screener.in/screens/2902519/strategy6a/",
                display_name="Strategy 6a",
                short_name="S6a"
            ),
            StrategyType.STRATEGY6B.value: StrategyConfig(
                name="Strategy6b",
                url="https://www.screener.in/screens/2902525/strategy6b/",
                display_name="Strategy 6b",
                short_name="S6b"
            )
        }
    
    def get_strategy(self, name: str) -> Optional[StrategyConfig]:
        """Get strategy configuration by name"""
        return self.strategies.get(name)
    
    def get_all_strategies(self) -> Dict[str, StrategyConfig]:
        """Get all strategy configurations"""
        return self.strategies.copy()
    
    def get_short_name(self, strategy_name: str) -> str:
        """Get short name for a strategy"""
        strategy = self.get_strategy(strategy_name)
        return strategy.short_name if strategy else strategy_name


class WebScraper:
    """Robust web scraper with retry logic and error handling"""
    
    def __init__(self, max_retries: int = 3, delay: float = 0.5):
        self.max_retries = max_retries
        self.delay = delay
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.9',
            'Accept-Encoding': 'gzip, deflate, br',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1'
        })
    
    def _has_next_button(self, soup: BeautifulSoup) -> bool:
        """Check if pagination has a next button"""
        try:
            pagination = soup.find('div', class_='pagination')
            if not pagination:
                return False
            
            # Look for next button
            if isinstance(pagination, Tag):
                for link in pagination.find_all('a'):
                    if link and link.get_text(strip=True).lower().startswith('next'):
                        return True
            return False
        except Exception as e:
            logger.warning(f"Error checking pagination: {e}")
            return False
    
    def _extract_table_data(self, soup: BeautifulSoup) -> Optional[pd.DataFrame]:
        """Extract stock data from HTML table"""
        try:
            table = soup.find('table')
            if not table:
                return None
            
            # Extract headers
            headers = []
            header_row = table.find('thead')
            if header_row and isinstance(header_row, Tag):
                header_cells = header_row.find_all(['th', 'td'])
            else:
                first_row = table.find('tr')
                if first_row and isinstance(first_row, Tag):
                    header_cells = first_row.find_all(['th', 'td'])
                else:
                    return None
            
            for cell in header_cells:
                if isinstance(cell, Tag):
                    header_text = cell.get_text(strip=True)
                    if header_text:
                        headers.append(header_text)
            
            if not headers:
                return None
            
            # Extract data rows
            rows = []
            tbody = table.find('tbody')
            if tbody and isinstance(tbody, Tag):
                row_elements = tbody.find_all('tr')
            else:
                all_rows = table.find_all('tr')
                row_elements = all_rows[1:] if len(all_rows) > 1 else []
            
            for tr in row_elements:
                if isinstance(tr, Tag):
                    row_data = []
                    cells = tr.find_all(['td', 'th'])
                    
                    for cell in cells:
                        if isinstance(cell, Tag):
                            cell_text = cell.get_text(strip=True)
                            row_data.append(cell_text)
                    
                    # Validate row data - filter out header rows and invalid data
                    if (len(row_data) == len(headers) and 
                        row_data and 
                        row_data[0] and 
                        row_data[0] != 'Name' and
                        row_data[0] != 'S.No.' and
                        len(row_data) > 1 and
                        row_data[1] != '......' and
                        row_data[1] != 'CMPRs.' and
                        row_data[1] != 'CMP Rs.'):
                        rows.append(row_data)
            
            if not rows:
                return None
            
            # Create DataFrame
            df = pd.DataFrame(rows, columns=headers)
            
            # Clean up column names
            df.columns = [col.strip() for col in df.columns]
            
            # Remove S.No. column if present
            if 'S.No.' in df.columns:
                df = df.drop('S.No.', axis=1)
            
            # Keep only required columns
            required_columns = ['Name', 'CMPRs.']
            available_columns = [col for col in required_columns if col in df.columns]
            
            if available_columns:
                df = df[available_columns]
            
            # Clean data - remove invalid entries and duplicates
            df = df.dropna(subset=['Name'])
            df = df[df['Name'].str.strip() != '']
            df = df[df['Name'].str.strip() != 'Name']  # Remove any remaining header rows
            df = df[~df['Name'].str.strip().isin(['S.No.', 'Name'])]  # Remove header variants
            
            # Remove duplicates based on Name
            df = df.drop_duplicates(subset=['Name'], keep='first')
            
            return df.reset_index(drop=True)
            
        except Exception as e:
            logger.error(f"Error extracting table data: {e}")
            return None
    
    def scrape_strategy_data(self, url: str) -> pd.DataFrame:
        """Scrape stock data from a strategy URL with pagination support"""
        logger.info(f"Starting to scrape: {url}")
        
        all_data = []
        page = 1
        
        while True:
            # Build page URL
            page_url = f"{url}?page={page}" if '?' not in url else f"{url}&page={page}"
            
            # Attempt to fetch page with retries
            soup = None
            for attempt in range(self.max_retries):
                try:
                    response = self.session.get(page_url, timeout=15)
                    response.raise_for_status()
                    soup = BeautifulSoup(response.content, 'html.parser')
                    break
                except Exception as e:
                    logger.warning(f"Attempt {attempt + 1} failed for {page_url}: {e}")
                    if attempt < self.max_retries - 1:
                        time.sleep(self.delay * (2 ** attempt))  # Exponential backoff
            
            if not soup:
                logger.error(f"Failed to fetch {page_url} after {self.max_retries} attempts")
                break
            
            # Extract data from current page
            page_df = self._extract_table_data(soup)
            if page_df is None or page_df.empty:
                logger.info(f"No data found on page {page}")
                break
            
            all_data.append(page_df)
            logger.info(f"Scraped page {page}: {len(page_df)} records")
            
            # Check for next page
            if not self._has_next_button(soup):
                logger.info(f"No more pages found. Stopping at page {page}")
                break
            
            page += 1
            time.sleep(self.delay)  # Be respectful to the server
        
        # Combine all pages
        if all_data:
            final_df = pd.concat(all_data, ignore_index=True)
            logger.info(f"Successfully scraped {len(final_df)} total records from {url}")
            return final_df
        
        logger.warning(f"No data scraped from {url}")
        return pd.DataFrame()


class StockAnalyzer:
    """Handles stock analysis operations"""
    
    def __init__(self, strategy_manager: StrategyManager):
        self.strategy_manager = strategy_manager
        self.scraper = WebScraper()
        self._cache: Dict[str, pd.DataFrame] = {}
    
    def get_strategy_stocks(self, strategy_name: str, use_cache: bool = True) -> pd.DataFrame:
        """Get stocks for a specific strategy"""
        if use_cache and strategy_name in self._cache:
            logger.info(f"Using cached data for {strategy_name}")
            return self._cache[strategy_name]
        
        strategy = self.strategy_manager.get_strategy(strategy_name)
        if not strategy:
            logger.error(f"Unknown strategy: {strategy_name}")
            return pd.DataFrame()
        
        try:
            df = self.scraper.scrape_strategy_data(strategy.url)
            if not df.empty:
                self._cache[strategy_name] = df
            return df
        except Exception as e:
            logger.error(f"Error fetching {strategy_name}: {e}")
            return pd.DataFrame()
    
    def get_all_strategies_data(self) -> Dict[str, pd.DataFrame]:
        """Fetch data for all strategies"""
        logger.info("Fetching data for all strategies")
        
        all_data = {}
        for strategy_name in self.strategy_manager.get_all_strategies().keys():
            df = self.get_strategy_stocks(strategy_name)
            if not df.empty:
                all_data[strategy_name] = df
        
        logger.info(f"Successfully fetched data for {len(all_data)} strategies")
        return all_data
    
    def find_common_stocks_in_selected_strategies(self, selected_strategies: List[str]) -> List[StockData]:
        """Find stocks common to all selected strategies"""
        if not selected_strategies:
            return []
        
        if len(selected_strategies) == 1:
            # Single strategy - return all stocks
            return self._get_single_strategy_stocks(selected_strategies[0])
        
        # Multiple strategies - find intersection
        logger.info(f"Finding common stocks in strategies: {selected_strategies}")
        
        # Get data for selected strategies
        strategy_data = {}
        for strategy_name in selected_strategies:
            df = self.get_strategy_stocks(strategy_name)
            if not df.empty and 'Name' in df.columns:
                strategy_data[strategy_name] = df
        
        if len(strategy_data) < len(selected_strategies):
            logger.warning("Some strategies returned no data")
        
        if len(strategy_data) < 2:
            return []
        
        # Find intersection of stock names
        strategy_names = list(strategy_data.keys())
        common_stocks = set(strategy_data[strategy_names[0]]['Name'].str.strip())
        
        for strategy_name in strategy_names[1:]:
            strategy_stocks = set(strategy_data[strategy_name]['Name'].str.strip())
            common_stocks = common_stocks.intersection(strategy_stocks)
        
        # Build result
        result = []
        short_names = [self.strategy_manager.get_short_name(s) for s in strategy_names]
        
        for stock_name in common_stocks:
            # Get stock data from first available strategy
            stock_data = None
            for strategy_name in strategy_names:
                df = strategy_data[strategy_name]
                matching_rows = df[df['Name'].str.strip() == stock_name.strip()]
                if not matching_rows.empty:
                    stock_data = matching_rows.iloc[0]
                    break
            
            if stock_data is not None:
                result.append(StockData(
                    name=stock_data['Name'],
                    cmp=stock_data.get('CMPRs.', '-'),
                    strategies=short_names,
                    strategy_count=len(strategy_names)
                ))
        
        # Sort by name
        result.sort(key=lambda x: x.name)
        logger.info(f"Found {len(result)} common stocks")
        return result
    
    def _get_single_strategy_stocks(self, strategy_name: str) -> List[StockData]:
        """Get all stocks from a single strategy"""
        logger.info(f"Getting all stocks from {strategy_name}")
        
        df = self.get_strategy_stocks(strategy_name)
        if df.empty:
            return []
        
        result = []
        short_name = self.strategy_manager.get_short_name(strategy_name)
        
        for _, row in df.iterrows():
            result.append(StockData(
                name=row['Name'],
                cmp=row.get('CMPRs.', '-'),
                strategies=[short_name],
                strategy_count=1
            ))
        
        logger.info(f"Found {len(result)} stocks in {strategy_name}")
        return result
    
    def find_stocks_in_x_strategies(self, min_strategies: int = 2) -> List[StockData]:
        """Find stocks that appear in at least X strategies"""
        logger.info(f"Finding stocks that appear in at least {min_strategies} strategies")
        
        if min_strategies < 2:
            logger.error("min_strategies must be at least 2")
            return []
        
        # Get all strategy data
        all_data = self.get_all_strategies_data()
        
        if len(all_data) < min_strategies:
            logger.warning(f"Only {len(all_data)} strategies available, need at least {min_strategies}")
            return []
        
        # Build stock to strategies mapping
        stock_strategies: Dict[str, List[str]] = {}
        
        for strategy_name, df in all_data.items():
            if 'Name' in df.columns:
                for stock_name in df['Name'].str.strip():
                    if stock_name not in stock_strategies:
                        stock_strategies[stock_name] = []
                    stock_strategies[stock_name].append(strategy_name)
        
        # Find qualifying stocks
        result = []
        for stock_name, strategies in stock_strategies.items():
            if len(strategies) >= min_strategies:
                # Get stock data from first strategy
                stock_data = None
                for strategy_name in strategies:
                    df = all_data[strategy_name]
                    matching_rows = df[df['Name'].str.strip() == stock_name.strip()]
                    if not matching_rows.empty:
                        stock_data = matching_rows.iloc[0]
                        break
                
                if stock_data is not None:
                    short_names = [self.strategy_manager.get_short_name(s) for s in strategies]
                    result.append(StockData(
                        name=stock_data['Name'],
                        cmp=stock_data.get('CMPRs.', '-'),
                        strategies=short_names,
                        strategy_count=len(strategies)
                    ))
        
        # Sort by strategy count (descending) then by name
        result.sort(key=lambda x: (-x.strategy_count, x.name))
        logger.info(f"Found {len(result)} stocks in {min_strategies}+ strategies")
        return result


# Global instances
strategy_manager = StrategyManager()
analyzer = StockAnalyzer(strategy_manager)


# Public API Functions
def get_strategy1_stocks() -> pd.DataFrame:
    """Get stocks from Strategy 1"""
    return analyzer.get_strategy_stocks(StrategyType.STRATEGY1.value)


def get_strategy2_stocks() -> pd.DataFrame:
    """Get stocks from Strategy 2"""
    return analyzer.get_strategy_stocks(StrategyType.STRATEGY2.value)


def get_strategy3_stocks() -> pd.DataFrame:
    """Get stocks from Strategy 3"""
    return analyzer.get_strategy_stocks(StrategyType.STRATEGY3.value)


def get_strategy4_stocks() -> pd.DataFrame:
    """Get stocks from Strategy 4"""
    return analyzer.get_strategy_stocks(StrategyType.STRATEGY4.value)


def get_strategy5_stocks() -> pd.DataFrame:
    """Get stocks from Strategy 5"""
    return analyzer.get_strategy_stocks(StrategyType.STRATEGY5.value)


def get_strategy6a_stocks() -> pd.DataFrame:
    """Get stocks from Strategy 6a"""
    return analyzer.get_strategy_stocks(StrategyType.STRATEGY6A.value)


def get_strategy6b_stocks() -> pd.DataFrame:
    """Get stocks from Strategy 6b"""
    return analyzer.get_strategy_stocks(StrategyType.STRATEGY6B.value)


def get_all_strategies() -> Dict[str, pd.DataFrame]:
    """Get all strategy data (for backward compatibility)"""
    return analyzer.get_all_strategies_data()


def find_common_stocks_in_selected_strategies(selected_strategies: List[str]) -> pd.DataFrame:
    """Find stocks common to selected strategies (for backward compatibility)"""
    stocks = analyzer.find_common_stocks_in_selected_strategies(selected_strategies)
    if not stocks:
        return pd.DataFrame()
    
    data = [stock.to_dict() for stock in stocks]
    return pd.DataFrame(data)


def find_stocks_in_x_strategies(min_strategies: int = 2) -> pd.DataFrame:
    """Find stocks that appear in X+ strategies (for backward compatibility)"""
    stocks = analyzer.find_stocks_in_x_strategies(min_strategies)
    if not stocks:
        return pd.DataFrame()
    
    data = [stock.to_dict() for stock in stocks]
    return pd.DataFrame(data)


if __name__ == "__main__":
    # Test the system
    logger.info("Testing Finance Agent")
    
    # Test single strategy
    result = get_strategy2_stocks()
    print(f"Strategy 1 stocks: {len(result)}")
    
    # Test intersection
    # intersection_result = find_stocks_in_x_strategies(2)
    # print(f"Stocks in 2+ strategies: {len(intersection_result)}")
