VC_CONFIGS = {
    "accel_india": {
        "name": "Accel India",
        "base_url": "https://www.accel.com",
        "search_patterns": [
            "/news",
            "/noteworthies/",
            "/insights/",
            "/portfolio-news/"
        ],
        "content_selectors": {
            "title": "h1, .post-title, .article-title",
            "content": ".post-content, .article-content, .content",
            "date": ".date, .published-date, time"
        }
    },
    "peak_xv": {
        "name": "Peak XV Partners",
        "base_url": "https://peakxv.com",
        "search_patterns": [
            "/newsroom",
            "/insights/",
            "/portfolio/"
        ],
        "content_selectors": {
            "title": "h1, .post-title, .article-title",
            "content": ".post-content, .article-content, .content",
            "date": ".date, .published-date, time"
        }
    },
    "kalaari_capital": {
        "name": "Kalaari Capital",
        "base_url": "https://kalaari.com",
        "search_patterns": [
            "/news/",
            "/insights/",
            "/portfolio/"
        ],
        "content_selectors": {
            "title": "h1, .post-title, .article-title",
            "content": ".post-content, .article-content, .content",
            "date": ".date, .published-date, time"
        }
    },
    "matrix_partners_india": {
        "name": "Matrix Partners India (Z47)",
        "base_url": "https://matrixpartners.in",
        "search_patterns": [
            "/insights/",
            "/news/",
            "/portfolio/"
        ],
        "content_selectors": {
            "title": "h1, .post-title, .article-title",
            "content": ".post-content, .article-content, .content",
            "date": ".date, .published-date, time"
        }
    },
    "nexus_venture_partners": {
        "name": "Nexus Venture Partners",
        "base_url": "https://www.nexusvp.com",
        "search_patterns": [
            "/insights",
            "/news/",
            "/portfolio/"
        ],
        "content_selectors": {
            "title": "h1, .post-title, .article-title",
            "content": ".post-content, .article-content, .content",
            "date": ".date, .published-date, time"
        }
    },
    "blume_ventures": {
        "name": "Blume Ventures",
        "base_url": "https://blume.vc",
        "search_patterns": [
            "/blog",
            "/news/",
            "/portfolio/"
        ],
        "content_selectors": {
            "title": "h1, .post-title, .article-title",
            "content": ".post-content, .article-content, .content",
            "date": ".date, .published-date, time"
        }
    },
    "chiratae_ventures": {
        "name": "Chiratae Ventures",
        "base_url": "https://www.chiratae.com",
        "search_patterns": [
            "/newsroom",
            "/insights/",
            "/portfolio/"
        ],
        "content_selectors": {
            "title": "h1, .post-title, .article-title",
            "content": ".post-content, .article-content, .content",
            "date": ".date, .published-date, time"
        }
    },
    "ah_ventures": {
        "name": "ah! Ventures",
        "base_url": "https://ahventures.in",
        "search_patterns": [
            "/blog/",
            "/news/",
            "/portfolio/"
        ],
        "content_selectors": {
            "title": "h1, .post-title, .article-title",
            "content": ".post-content, .article-content, .content",
            "date": ".date, .published-date, time"
        }
    }
}


# User agents to rotate through
USER_AGENTS = [
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
    'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
    'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:89.0) Gecko/20100101 Firefox/89.0',
    'Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:89.0) Gecko/20100101 Firefox/89.0'
]


def load_vc_configs():
    """Load VC configurations and return as a list of dictionaries"""
    vc_list = []
    for vc_key, vc_config in VC_CONFIGS.items():
        # Add the key to the config for easier reference
        config_with_key = vc_config.copy()
        config_with_key['key'] = vc_key
        vc_list.append(config_with_key)
    return vc_list
