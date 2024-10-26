import requests
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import time
from bs4 import BeautifulSoup
import json
import random
from waybackpy import WaybackMachineCDXServerAPI
import warnings
from tqdm import tqdm
import concurrent.futures
import re

class BirkenstockASPAnalyzer:
    def __init__(self):
        self.base_url = "https://www.birkenstock.com"
        self.user_agents = [
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/14.0 Safari/605.1.15',
        ]
        self.start_date = datetime(2020, 1, 1)
        self.categories = {
            'sandals': 'open',
            'clogs': 'closed-toe',
            'boots': 'closed-toe',
            'shoes': 'closed-toe'
        }

    def get_headers(self):
        return {
            'User-Agent': random.choice(self.user_agents),
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
        }

    def get_snapshots_for_url(self, url):
        """Get historical snapshots for a specific URL"""
        user_agent = random.choice(self.user_agents)
        cdx_api = WaybackMachineCDXServerAPI(url, user_agent)
        
        try:
            snapshots = list(cdx_api.snapshots(
                from_date=self.start_date,
                to_date=datetime.now(),
                match_type='exact'
            ))
            # Filter to one snapshot per month to avoid redundancy
            monthly_snapshots = {}
            for snapshot in snapshots:
                month_key = snapshot.timestamp.strftime('%Y-%m')
                if month_key not in monthly_snapshots:
                    monthly_snapshots[month_key] = snapshot
            
            return list(monthly_snapshots.values())
        except Exception as e:
            print(f"Error fetching snapshots for {url}: {e}")
            return []

    def extract_product_info(self, html_content, category, date, is_historical=True):
        """Extract product information from HTML content"""
        soup = BeautifulSoup(html_content, 'html.parser')
        products = []
        
        # Different possible product container classes
        product_containers = soup.find_all('div', {'class': [
            'product-tile', 'product-card', 'product-item',
            'product-grid-item', 'product-list-item'
        ]})
        
        for container in product_containers:
            try:
                # Extract product name
                name_elem = container.find(['h3', 'div', 'span'], {'class': [
                    'product-name', 'product-title', 'name'
                ]})
                if not name_elem:
                    continue
                name = name_elem.text.strip()
                
                # Extract SKU/Model number
                sku = self._extract_sku(container) or self._extract_sku_from_name(name)
                
                # Extract prices
                price_info = self._extract_price_info(container)
                if not price_info:
                    continue
                
                # Determine if product is new
                is_new = self._check_if_new(container, name)
                
                # Determine distribution channel
                channel = self._determine_channel(container)
                
                product = {
                    'name': name,
                    'sku': sku,
                    'category': category,
                    'style': self.categories[category],
                    'current_price': price_info['current'],
                    'original_price': price_info['original'],
                    'discount_amount': price_info['discount'],
                    'discount_percentage': price_info['discount_percent'],
                    'is_new_product': is_new,
                    'channel': channel,
                    'date': date,
                    'source': 'historical' if is_historical else 'current'
                }
                products.append(product)
                
            except Exception as e:
                continue
        
        return products

    def _extract_sku(self, container):
        """Extract SKU from product container"""
        sku_patterns = [
            r'SKU:\s*([A-Z0-9-]+)',
            r'Model:\s*([A-Z0-9-]+)',
            r'Item\s*#:\s*([A-Z0-9-]+)'
        ]
        
        for pattern in sku_patterns:
            if sku_match := re.search(pattern, str(container)):
                return sku_match.group(1)
        return None

    def _extract_sku_from_name(self, name):
        """Extract SKU from product name if possible"""
        sku_pattern = r'[A-Z0-9]{6,}'
        if sku_match := re.search(sku_pattern, name.replace(' ', '')):
            return sku_match.group(0)
        return None

    def _extract_price_info(self, container):
        """Extract detailed price information"""
        try:
            # Find current price
            price_elem = container.find(['span', 'div'], {'class': [
                'price', 'product-price', 'current-price'
            ]})
            if not price_elem:
                return None
            
            current_price = self._convert_price_to_float(price_elem.text)
            
            # Find original price if available
            original_price_elem = container.find(['span', 'div'], {'class': [
                'original-price', 'was-price', 'regular-price'
            ]})
            original_price = self._convert_price_to_float(original_price_elem.text) if original_price_elem else current_price
            
            # Calculate discount information
            discount = round(original_price - current_price, 2) if original_price > current_price else 0
            discount_percent = round((discount / original_price) * 100, 2) if discount > 0 else 0
            
            return {
                'current': current_price,
                'original': original_price,
                'discount': discount,
                'discount_percent': discount_percent
            }
        except:
            return None

    def _convert_price_to_float(self, price_text):
        """Convert price text to float"""
        if not price_text:
            return 0.0
        return float(re.sub(r'[^\d.]', '', price_text))

    def _check_if_new(self, container, name):
        """Determine if product is new"""
        new_indicators = ['new', 'new arrival', 'just in']
        text_content = str(container).lower()
        return any(indicator in text_content or indicator in name.lower() 
                  for indicator in new_indicators)

    def _determine_channel(self, container):
        """Determine distribution channel"""
        text_content = str(container).lower()
        if any(term in text_content for term in ['wholesale', 'retailer', 'dealer']):
            return 'wholesale'
        return 'dtc'  # Direct to Consumer

    def process_snapshot(self, snapshot, category):
        """Process individual snapshot"""
        try:
            response = requests.get(snapshot.archive_url, 
                                  headers=self.get_headers(), 
                                  timeout=15)
            date = snapshot.timestamp.strftime('%Y-%m-%d')
            return self.extract_product_info(response.content, category, date)
        except Exception as e:
            print(f"Error processing snapshot {snapshot.archive_url}: {e}")
            return []

    def collect_historical_data(self):
        """Collect historical data for all categories"""
        all_products = []
        
        for category in tqdm(self.categories.keys(), desc="Processing categories"):
            url = f"{self.base_url}/us/en-us/{category}"
            snapshots = self.get_snapshots_for_url(url)
            
            print(f"Found {len(snapshots)} snapshots for {category}")
            
            with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
                future_to_snapshot = {
                    executor.submit(self.process_snapshot, snapshot, category): snapshot 
                    for snapshot in snapshots
                }
                
                for future in tqdm(concurrent.futures.as_completed(future_to_snapshot), 
                                 total=len(snapshots),
                                 desc=f"Processing {category} snapshots"):
                    try:
                        products = future.result()
                        all_products.extend(products)
                    except Exception as e:
                        print(f"Error processing snapshot: {e}")
                    
            time.sleep(2)  # Be nice to Wayback Machine
            
        return pd.DataFrame(all_products)

    def analyze_asp_trends(self, df):
        """Analyze ASP trends and components"""
        df['date'] = pd.to_datetime(df['date'])
        df['year_month'] = df['date'].dt.to_period('M')
        
        analysis = {
            'overall_asp_trends': self._analyze_overall_asp(df),
            'product_mix_impact': self._analyze_product_mix(df),
            'channel_mix_impact': self._analyze_channel_mix(df),
            'style_mix_impact': self._analyze_style_mix(df),
            'pricing_actions': self._analyze_pricing_actions(df),
            'promotional_impact': self._analyze_promotional_impact(df)
        }
        
        return analysis

    def _analyze_overall_asp(self, df):
        """Analyze overall ASP trends"""
        monthly_asp = df.groupby('year_month').agg({
            'current_price': ['mean', 'median', 'count'],
            'original_price': 'mean'
        }).round(2)
        
        yoy_growth = monthly_asp.pct_change(12) * 100
        
        return {
            'monthly_asp': monthly_asp.to_dict(),
            'yoy_growth': yoy_growth.to_dict()
        }

    def _analyze_product_mix(self, df):
        """Analyze impact of product mix on ASP"""
        return {
            'category_mix': self._calculate_mix_impact(df, 'category'),
            'new_vs_existing': self._calculate_mix_impact(df, 'is_new_product')
        }

    def _analyze_channel_mix(self, df):
        """Analyze impact of channel mix on ASP"""
        return self._calculate_mix_impact(df, 'channel')

    def _analyze_style_mix(self, df):
        """Analyze impact of style mix on ASP"""
        return self._calculate_mix_impact(df, 'style')

    def _analyze_pricing_actions(self, df):
        """Analyze pricing actions and their impact"""
        # Track price changes for same SKUs over time
        sku_price_changes = df.pivot_table(
            index='sku',
            columns='year_month',
            values='current_price'
        ).pct_change(axis=1) * 100
        
        return {
            'avg_price_change': sku_price_changes.mean().to_dict(),
            'price_change_distribution': sku_price_changes.agg(['mean', 'median', 'std']).to_dict()
        }

    def _analyze_promotional_impact(self, df):
        """Analyze impact of promotions on ASP"""
        promo_impact = df.groupby('year_month').agg({
            'discount_percentage': ['mean', 'median'],
            'discount_amount': 'sum',
        }).round(2)
        
        return promo_impact.to_dict()

    def _calculate_mix_impact(self, df, dimension):
        """Calculate mix impact for a given dimension"""
        # Calculate ASP by dimension and time period
        asp_by_dim = df.groupby(['year_month', dimension])['current_price'].mean().unstack()
        
        # Calculate mix percentages
        mix_by_dim = df.groupby(['year_month', dimension]).size().unstack()
        mix_by_dim = mix_by_dim.div(mix_by_dim.sum(axis=1), axis=0)
        
        # Calculate mix impact
        base_period_asp = asp_by_dim.iloc[0]
        base_period_mix = mix_by_dim.iloc[0]
        
        mix_impact = ((mix_by_dim - base_period_mix) * base_period_asp).sum(axis=1)
        price_impact = ((asp_by_dim - base_period_asp) * mix_by_dim).sum(axis=1)
        
        return {
            'asp_by_dimension': asp_by_dim.to_dict(),
            'mix_percentages': mix_by_dim.to_dict(),
            'mix_impact': mix_impact.to_dict(),
            'price_impact': price_impact.to_dict()
        }

def run_analysis():
    """Run the complete analysis"""
    analyzer = BirkenstockASPAnalyzer()
    
    print("Collecting historical data...")
    df = analyzer.collect_historical_data()
    
    print("\nAnalyzing ASP trends...")
    analysis = analyzer.analyze_asp_trends(df)
    
    # Save results
    df.to_csv('birkenstock_historical_data.csv', index=False)
    with open('birkenstock_asp_analysis.json', 'w') as f:
        json.dump(analysis, f, indent=4, default=str)
    
    return df, analysis

# Run everything
if __name__ == "__main__":
    df, analysis = run_analysis()
