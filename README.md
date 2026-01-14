# MSN Channel Post Scraper 📰

A powerful Python tool to scrape and download posts from any MSN channel with likes, comments, and engagement metrics. Extract articles and slideshows data incrementally with real-time saving capabilities.

[![Python 3.7+](https://img.shields.io/badge/python-3.7+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)

## 🌟 Features

- **Auto Provider Detection**: Automatically extracts provider ID from MSN channel URLs
- **Incremental Saving**: Save posts progressively as they're scraped (never lose progress!)
- **Flexible Scraping**: Choose specific number of posts or fetch all available posts
- **Rich Data Extraction**: Captures likes, dislikes, comments, titles, URLs, abstracts, and timestamps
- **Dual Export Format**: Saves data in both CSV and JSON formats
- **Provider Filtering**: Filter posts to only include those from the specific channel
- **Smart Caching**: Caches first page to avoid redundant API calls
- **Rate Limiting**: Built-in delays to respect MSN servers
- **Real-time Progress**: Live updates showing scraping progress
- **Dynamic Filenames**: Automatically names files based on provider name

## 📋 Table of Contents

- [Installation](#installation)
- [Quick Start](#quick-start)
- [Usage](#usage)
- [Features Explained](#features-explained)
- [Data Fields](#data-fields)
- [Examples](#examples)
- [Requirements](#requirements)
- [Contributing](#contributing)
- [License](#license)

## 🚀 Installation

### Prerequisites

- Python 3.7 or higher
- pip (Python package installer)

### Setup

1. **Clone the repository**
```bash
git clone https://github.com/yourusername/msn-scraper.git
cd msn-scraper
```

2. **Install required packages**
```bash
pip install requests
```

That's it! No additional dependencies required.

## 🎯 Quick Start

1. **Run the scraper**
```bash
python msn.py
```

2. **Enter MSN channel URL when prompted**
```
Example: https://www.msn.com/en-us/channel/source/FinanceBuzz%20Money/sr-vid-nx9xwm4ac8jkgyp2qymus852ntch6haq5b8msw39hdgsf4anjjxa
```

3. **Choose how many posts to scrape**
- Enter a number (e.g., `50`, `100`, `200`)
- Or enter `all` to fetch all available posts

4. **Wait for completion**
- Posts are saved incrementally as they're fetched
- Files are automatically named based on the channel (e.g., `FinanceBuzz_Money_posts.csv`)

## 📖 Usage

### Interactive Mode (Recommended)

Simply run the script and follow the prompts:

```bash
python msn.py
```

### Finding MSN Channel URLs

1. Go to [MSN.com](https://www.msn.com)
2. Navigate to any channel/source page
3. Copy the URL from your browser
4. The URL should look like: `https://www.msn.com/en-us/channel/source/{ProviderName}/sr-{provider-id}`

### Example Channels

- **FinanceBuzz Money**: `https://www.msn.com/en-us/channel/source/FinanceBuzz%20Money/sr-vid-nx9xwm4ac8jkgyp2qymus852ntch6haq5b8msw39hdgsf4anjjxa`
- **Any other MSN channel**: Just copy the URL from the channel page

## 🔍 Features Explained

### Auto Provider Detection
The scraper automatically extracts the provider ID from any MSN channel URL. No need to manually find provider IDs!

### Incremental Saving
Unlike traditional scrapers that save everything at the end, this tool saves posts **after each page** is fetched. Benefits:
- ✅ Never lose progress if the script is interrupted
- ✅ See results immediately
- ✅ Safe for long-running scrapes

### Flexible Post Limits
- Set a specific limit: `50`, `100`, `500`
- Fetch everything: `all`
- The scraper respects your choice and stops accordingly

### Provider Filtering
By default, only posts from the specific channel are included. This filters out:
- Suggested posts from other sources
- Topic feed recommendations
- Only gives you authentic channel content

## 📊 Data Fields

Each scraped post includes:

| Field | Description |
|-------|-------------|
| `id` | Unique post identifier |
| `title` | Post headline/title |
| `type` | Content type (article/slideshow) |
| `url` | Direct link to the post |
| `likes` | Number of upvotes |
| `dislikes` | Number of downvotes |
| `total_reactions` | Total engagement count |
| `total_comments` | Number of comments |
| `published_date` | Publication timestamp |
| `provider` | Provider/source name |
| `provider_id` | Provider unique identifier |
| `abstract` | Post summary/description |

## 💡 Examples

### Example 1: Scrape 100 Posts

```bash
python msn.py
# Enter URL: https://www.msn.com/en-us/channel/source/...
# Number of posts: 100
```

**Output:**
- `ProviderName_posts.csv` - 100 posts in CSV format
- `ProviderName_posts.json` - 100 posts in JSON format

### Example 2: Scrape All Available Posts

```bash
python msn.py
# Enter URL: https://www.msn.com/en-us/channel/source/...
# Number of posts: all
```

**Output:**
- All available posts from the channel
- Automatically stops when no more posts are available

### Example 3: Using as a Python Module

```python
from msn import MSNDataFetcher

# Initialize with provider ID
fetcher = MSNDataFetcher(provider_id="vid-...")

# Fetch posts
posts = fetcher.fetch_posts(
    max_posts=50,
    save_incrementally=True,
    csv_filename="my_posts.csv",
    json_filename="my_posts.json"
)

# Access post data
for post in posts:
    print(f"{post['title']}: {post['likes']} likes")
```

## 🛠️ Requirements

- **Python**: 3.7+
- **Dependencies**:
  - `requests` - For HTTP requests
  
All other dependencies are part of Python standard library:
- `json` - JSON parsing
- `csv` - CSV file handling
- `time` - Rate limiting
- `re` - Regular expressions
- `urllib.parse` - URL parsing
- `typing` - Type hints

Install dependencies:
```bash
pip install requests
```

## 📁 Project Structure

```
msn_scraper/
├── msn.py                    # Main scraper script
├── README.md                 # This file
├── ProviderName_posts.csv    # Output CSV (generated)
└── ProviderName_posts.json   # Output JSON (generated)
```

## 🎨 Use Cases

- **Content Analysis**: Analyze trending topics and engagement patterns
- **Research**: Gather data for academic or market research
- **Archival**: Backup posts from your favorite channels
- **Data Science**: Build datasets for NLP or machine learning projects
- **Competitive Analysis**: Monitor competitor content performance
- **SEO Research**: Study headline patterns and engagement
- **Social Media Analytics**: Track viral content and trends

## ⚙️ Advanced Configuration

### Modify Rate Limiting

In `msn.py`, adjust the delay between requests:

```python
posts = fetcher.fetch_posts(
    delay=2.0  # 2 seconds between requests (default: 1.0)
)
```

### Disable Provider Filtering

To include all posts (including suggestions):

```python
posts = fetcher.fetch_posts(
    provider_filter=False  # Include all posts
)
```

### Custom Filenames

```python
posts = fetcher.fetch_posts(
    csv_filename="custom_name.csv",
    json_filename="custom_name.json"
)
```

## 🐛 Troubleshooting

### "Could not extract provider ID"
- Make sure the URL contains `/sr-vid-...`
- Check that you copied the complete URL
- Try copying the URL again from the channel page

### "No posts found"
- Some channels may have no posts or private content
- Try a different channel URL
- Check your internet connection

### Script stops unexpectedly
- Data is saved incrementally, so check the CSV file for partial results
- Increase delay between requests if you're being rate-limited
- Check your internet connection

## 🤝 Contributing

Contributions are welcome! Here's how you can help:

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

### Ideas for Contributions

- [ ] Add support for other MSN content types
- [ ] Implement proxy support
- [ ] Add GUI interface
- [ ] Create data visualization features
- [ ] Add export to other formats (Excel, SQLite, etc.)
- [ ] Implement multi-threading for faster scraping
- [ ] Add sentiment analysis features

## 📝 License

This project is licensed under the MIT License - see below for details:

```
MIT License

Copyright (c) 2026 MSN Scraper

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
```

## ⚠️ Disclaimer

This tool is for educational and research purposes only. Please:
- Respect MSN's Terms of Service
- Use reasonable rate limiting
- Don't overload their servers
- Use scraped data responsibly
- Check robots.txt and terms before scraping
- Don't use for commercial purposes without permission

## 🌐 Keywords

`msn scraper` `web scraping` `data extraction` `python scraper` `msn news` `content scraper` `article scraper` `news scraper` `social media scraper` `engagement metrics` `data mining` `web crawler` `msn api` `msn data` `incremental scraping` `csv export` `json export` `content analysis` `news aggregator` `python automation`

## 📞 Support

- **Issues**: [GitHub Issues](https://github.com/yourusername/msn-scraper/issues)
- **Discussions**: [GitHub Discussions](https://github.com/yourusername/msn-scraper/discussions)

## 🎓 Learn More

- [MSN Official Website](https://www.msn.com)
- [Python Requests Documentation](https://docs.python-requests.org/)
- [Web Scraping Best Practices](https://www.scrapingbee.com/blog/web-scraping-best-practices/)

---

**Made with ❤️ for the data community**

If this project helped you, please give it a ⭐ on GitHub!
