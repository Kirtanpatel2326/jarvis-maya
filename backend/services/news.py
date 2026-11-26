import xml.etree.ElementTree as ET
import httpx

RSS_URL = "https://news.google.com/rss?hl=en-US&gl=US&ceid=US:en"

async def get_latest_news(count: int = 5) -> list:
    """
    Fetches latest headlines from Google News RSS.
    """
    try:
        async with httpx.AsyncClient() as client:
            res = await client.get(RSS_URL, timeout=5.0)
            if res.status_code == 200:
                root = ET.fromstring(res.text)
                items = root.findall(".//item")
                
                news_list = []
                for item in items[:count]:
                    title = item.find("title").text
                    # Clean up source from title (e.g. "Headline - CNN" -> "Headline")
                    if " - " in title:
                        title = title.rsplit(" - ", 1)[0]
                    news_list.append(title)
                return news_list
    except Exception as e:
        print(f"News fetch error: {e}")
    
    # Fallback default items if offline
    return [
        "Global economic summits align on AI safety protocols.",
        "Space exploration services launch new reusable deep-space cargo pod.",
        "Renewable energy grids hit record generation capacity in Asia.",
        "New research breakthroughs in solid-state battery technology.",
        "Stark Industries announces next-gen hardware interfaces."
    ]
