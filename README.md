# VC Thesis Scraper

A comprehensive web scraper for collecting investment theses and insights from leading venture capital firms in India. This tool extracts detailed investment content, portfolio information, and strategic insights from major VC websites.

## Features

- **Multi-VC Support**: Scrapes from major Indian VC firms including:
    - Accel India
    - Kalaari Capital
    - Peak XV Partners (formerly Sequoia Capital India)
    - Blume Ventures
- **Intelligent Content Extraction**: Captures investment theses, portfolio announcements, and strategic insights
- **Configurable Scraping**: YAML-based configuration for easy customization
- **Content Deduplication**: Removes duplicate entries and cleans extracted data
- **Respectful Scraping**: Follows robots.txt guidelines and implements rate limiting
- **Structured Output**: Exports data to CSV format with organized columns (VC Name, Title, URL, Content)
- **Date Tracking**: Captures publication dates and timestamps
- **Comprehensive Coverage**: Extracts both recent and historical investment content

## Data Sources

The scraper collects various types of content:
- **Investment Announcements**: Seed, Series A/B/C funding rounds
- **Portfolio Updates**: Company progress and milestone updates
- **Market Insights**: Industry analysis and trend observations
- **Technology Focus Areas**: AI/ML, fintech, healthcare, SaaS, and emerging sectors
- **Geographic Coverage**: India-focused investments and global expansion insights

## Sample Extracted Content

The scraper captures detailed information including:
- AI and technology investments (Cursor, Synthesia, Tessl)
- Healthcare and biotech ventures (PhaseV, WellTheory, RapidClaims)
- Fintech and payments (Pismo, Swan, Rainforest)
- Developer tools and infrastructure (Linear, Appsmith, Akto)
- Consumer and retail (MyGlamm, Samosa Party, Deconstruct)
- Enterprise software (Cyera, Sprinto, Lightdash)

## Installation

1. Clone the repository:
```bash
git clone https://github.com/yourusername/vc-thesis-scraper.git
cd vc-thesis-scraper
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Configure your scraping parameters:
```bash
cp config.yaml.example config.yaml
# Edit config.yaml with your settings
```

## Configuration

### YAML Configuration Structure

```yaml
vc_firms:
    - name: "Accel India"
        base_url: "https://www.accel.com"
        scraping_rules:
            - path: "/news"
            - path: "/noteworthies"
        rate_limit: 2  # seconds between requests
        
    - name: "Kalaari Capital"
        base_url: "https://kalaari.com"
        scraping_rules:
            - path: "/news"
            - path: "/portfolio"
        rate_limit: 2

output:
    format: "csv"
    filename: "vc_theses.csv"
    include_content: true
    deduplicate: true

scraping:
    respect_robots: true
    user_agent: "VC-Thesis-Scraper/1.0"
    timeout: 30
    max_retries: 3
```

## Usage

### Basic Scraping

```bash
# Scrape all configured VCs
python scraper.py

# Scrape specific VC
python scraper.py --vc "Accel India"

# Output to specific file
python scraper.py --output custom_output.csv
```

### Advanced Options

```bash
# Enable verbose logging
python scraper.py --verbose

# Set custom date range
python scraper.py --start-date 2024-01-01 --end-date 2024-12-31

# Skip content deduplication
python scraper.py --no-dedupe

# Dry run (test without writing)
python scraper.py --dry-run
```

## Output Format

The scraper generates CSV files with the following structure:

| Column | Description | Example |
|--------|-------------|---------|
| VC Name | Name of the venture capital firm | "Accel India" |
| Title | Title of the article/announcement | "Our Investment in Cursor" |
| URL | Source URL of the content | "https://www.accel.com/noteworthies/..." |
| Content | Full extracted text content | "We're pleased to announce our investment..." |
| Date | Publication date (when available) | "2025-06-06" |

### Sample Output Files

- `vc_theses.csv`: Main output with all scraped content
- `all_vc_theses.csv`: Consolidated view across all VCs
- `output/`: Directory containing organized results

## Investment Themes Covered

The scraper captures investments across major themes:

### Technology & Infrastructure
- AI/ML platforms and tools
- Developer infrastructure
- Cloud and SaaS solutions
- Cybersecurity and data protection

### Vertical Markets
- **Healthcare**: Digital health, biotech, medical devices
- **Fintech**: Payments, lending, insurance
- **Education**: EdTech, skill development
- **Gaming**: Social gaming, esports platforms
- **Commerce**: E-commerce, retail tech

### Geographic Focus
- India-first companies
- Global expansion stories
- Cross-border opportunities
- Emerging market insights

## Content Quality Features

- **Clean Extraction**: Removes navigation, ads, and boilerplate content
- **Full Article Text**: Captures complete investment thesis and analysis
- **Metadata Preservation**: Maintains publication dates and source attribution
- **Deduplication Logic**: Identifies and removes duplicate content across sources
- **Content Validation**: Ensures extracted text meets quality thresholds

## Rate Limiting & Ethics

- Respects robots.txt files
- Implements configurable delays between requests
- Uses rotating user agents
- Handles rate limiting gracefully
- Provides options for politeness policies

## Troubleshooting

### Common Issues

**Connection Errors**:
```bash
# Increase timeout
python scraper.py --timeout 60
```

**Rate Limiting**:
```bash
# Increase delay between requests
python scraper.py --delay 5
```

**Content Not Found**:
```bash
# Update selectors in config.yaml
# Check website structure changes
```

### Debugging

```bash
# Enable debug mode
python scraper.py --debug

# Test specific URL
python scraper.py --test-url "https://example.com/article"

# Validate configuration
python scraper.py --validate-config
```

## Data Analysis

The extracted data enables various analyses:
- Investment trend analysis over time
- Sector focus comparison across VCs
- Geographic investment patterns
- Technology theme evolution
- Portfolio company growth trajectories

## Compliance & Legal

- Respects website terms of service
- Implements ethical scraping practices
- Provides attribution for all content
- Supports opt-out mechanisms
- Maintains data usage guidelines

## Contributing

1. Fork the repository
2. Create a feature branch
3. Add new VC firm configurations
4. Test thoroughly
5. Submit a pull request

## Support & Maintenance

- Regular updates for website structure changes
- Configuration templates for new VCs
- Community-driven improvements
- Issue tracking and resolution

## License

This project is licensed under the MIT License - see the LICENSE file for details.