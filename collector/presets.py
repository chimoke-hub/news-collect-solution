"""ニュース収集テーマのプリセット。

非エンジニアでもワンクリックで収集ツールを作れるよう、
人気テーマのキーワード・言語・おすすめRSSをあらかじめ用意する。
"""

PRESETS = [
    {
        "id": "web3",
        "emoji": "₿",
        "name": "Web3・暗号資産",
        "tagline": "ブロックチェーン / DeFi / NFT の最新動向",
        "keywords": "Web3 OR blockchain OR cryptocurrency OR Bitcoin OR Ethereum OR DeFi OR NFT",
        "language": "both",
        "rss_feeds": "https://www.coindesk.com/arc/outboundfeeds/rss/\nhttps://cointelegraph.com/rss",
    },
    {
        "id": "ai",
        "emoji": "🤖",
        "name": "AI・生成AI",
        "tagline": "LLM / 機械学習 / 生成AI の研究と製品",
        "keywords": "AI OR \"artificial intelligence\" OR LLM OR \"machine learning\" OR OpenAI OR Anthropic",
        "language": "both",
        "rss_feeds": "https://www.technologyreview.com/feed/",
    },
    {
        "id": "startup",
        "emoji": "🚀",
        "name": "スタートアップ・資金調達",
        "tagline": "ベンチャー / 資金調達 / IPO の話題",
        "keywords": "startup OR \"venture capital\" OR funding OR \"series A\" OR IPO",
        "language": "both",
        "rss_feeds": "https://techcrunch.com/feed/",
    },
    {
        "id": "sports",
        "emoji": "⚽",
        "name": "サッカー・スポーツ",
        "tagline": "海外サッカー / 国内スポーツのニュース",
        "keywords": "Premier League OR Champions League OR サッカー OR Jリーグ",
        "language": "both",
        "rss_feeds": "https://www.soccer-king.jp/feed",
    },
    {
        "id": "climate",
        "emoji": "🌱",
        "name": "気候・サステナビリティ",
        "tagline": "脱炭素 / 再エネ / ESG の動向",
        "keywords": "climate OR \"renewable energy\" OR sustainability OR ESG OR 脱炭素",
        "language": "both",
        "rss_feeds": "",
    },
    {
        "id": "gadget",
        "emoji": "📱",
        "name": "ガジェット・テック製品",
        "tagline": "スマホ / 新製品 / コンシューマーテック",
        "keywords": "iPhone OR Android OR gadget OR Apple OR Google Pixel OR ガジェット",
        "language": "both",
        "rss_feeds": "https://www.theverge.com/rss/index.xml",
    },
]
