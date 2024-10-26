# Birkenstock ASP Analysis Tool

## Overview
This tool performs comprehensive Average Selling Price (ASP) analysis for Birkenstock products, tracking historical pricing data from 2020 onwards. It's designed to analyze pricing trends, product mix shifts, and promotional patterns across Birkenstock's product portfolio.

## Features
- Historical price tracking (2020-present)
- ASP decomposition analysis
- Product mix impact calculation
- Channel mix analysis (DTC vs. Wholesale)
- Style mix analysis (Open vs. Closed-toe)
- Promotional impact assessment
- SKU-level price change tracking

## Installation

1. Clone the repository:
```bash
git clone [repository-url]
cd birkenstock-analyzer
```

2. Install required packages:
```bash
pip install requests pandas beautifulsoup4 waybackpy tqdm
```

## Usage

### Basic Usage
```python
from birkenstock_analyzer import BirkenstockASPAnalyzer

# Initialize and run analysis
analyzer = BirkenstockASPAnalyzer()
df, analysis = run_analysis()
```

### Jupyter Notebook Usage
```python
# Run in Jupyter cell
from birkenstock_analyzer import BirkenstockASPAnalyzer
analyzer = BirkenstockASPAnalyzer()
df, analysis = run_analysis()

# View specific analysis components
print(analysis['overall_asp_trends'])
```

## Output Files
The tool generates two main output files:
1. `birkenstock_historical_data.csv`: Raw historical pricing data
2. `birkenstock_asp_analysis.json`: Detailed analysis results

## Analysis Components

### 1. Overall ASP Trends
- Monthly ASP tracking
- Year-over-Year growth rates
- Price distribution analysis

### 2. Product Mix Impact
- Category mix shifts
- New vs. existing product analysis
- Style mix changes

### 3. Channel Analysis
- DTC vs. Wholesale pricing
- Channel mix impact on ASP
- Channel-specific trends

### 4. Pricing Actions
- Base price changes
- SKU-level price tracking
- Price change distribution

### 5. Promotional Impact
- Discount depth analysis
- Promotional frequency
- Impact on effective ASP

## Data Structure

### Historical Data (CSV)
```
- name: Product name
- sku: Product SKU/Model number
- category: Product category
- style: Open/Closed-toe
- current_price: Current selling price
- original_price: Original price before discounts
- discount_amount: Absolute discount amount
- discount_percentage: Percentage discount
- is_new_product: New product flag
- channel: DTC/Wholesale
- date: Data collection date
- source: Data source (historical/current)
```

### Analysis Results (JSON)
```json
{
    "overall_asp_trends": {
        "monthly_asp": {...},
        "yoy_growth": {...}
    },
    "product_mix_impact": {
        "category_mix": {...},
        "new_vs_existing": {...}
    },
    "channel_mix_impact": {...},
    "style_mix_impact": {...},
    "pricing_actions": {...},
    "promotional_impact": {...}
}
```

## Best Practices

1. **Rate Limiting**: The tool includes built-in delays to respect website rate limits

2. **Data Freshness**: Run the analysis regularly to maintain up-to-date data

3. **Error Handling**: The tool includes robust error handling for network issues and parsing errors

4. **Data Storage**: Regular backups of historical data are recommended

## Limitations

1. Historical data availability depends on Wayback Machine snapshots
2. Some product details might be missing in historical snapshots
3. Channel information may be limited for older data
4. Price comparisons assume consistent SKU identification

## Contributing
Contributions are welcome! Please feel free to submit a Pull Request.

## License
MIT License

## Support
For issues and feature requests, please create an issue in the repository.

---

**Note**: This tool is for analytical purposes only and should be used in accordance with website terms of service and robots.txt directives.
