import os
import json
import httpx
from loguru import logger
from agent.memory.manager import memory_manager

NEWS_SYSTEM_PROMPT = """Kamu adalah perangkum berita AI.
Topik: {topic}
Sumber: {sources}
Jumlah: {count}

Berita terkini:
{news_data}

Tugasmu:
1. Pilih {count} berita paling relevan tentang "{topic}"
2. Beri ringkasan 2-3 kalimat per berita
3. Urutkan dari yang paling penting
4. Gunakan bahasa Indonesia

Format:
📰 *Ringkasan Berita: {topic}*
Berita #1:
• **[judul]**
  [ringkasan 2-3 kalimat]
  🔗 [URL]
  🕐 [waktu]
---
[Kesimpulan singkat]
"""

DEFAULT_FEEDS = {
    "teknologi": "https://feed.info.com/berita/teknologi/rss",
    "bisnis": "https://feed.info.com/berita/bisnis/rss",
    "olahraga": "https://feed.info.com/berita/olahraga/rss",
    "internasional": "https://feed.info.com/berita/internasional/rss",
    "sains": "https://rss.nytimes.com/services/xml/rss/nyt/Science.xml",
    "ai": "https://rss.nytimes.com/services/xml/rss/nyt/Technology.xml",
    "kompas_tekno": "https://tekno.kompas.com/rss",
    "detik_inet": "https://inet.detik.com/indeks/feed",
}

QUERY_BASED_FALLBACK = """Kamu adalah perangkum berita AI.
Topik: {topic}

Hasil pencarian:
{search_results}

Tugasmu:
1. Pilih 3-5 berita paling relevan
2. Ringkas masing-masing 2-3 kalimat
3. Gunakan bahasa Indonesia

Format:
📰 *Berita: {topic}*
• **[judul]** — ringkasan
  🔗 URL
"""


class NewsDigest:
    def __init__(self):
        self.nim_api_key = os.environ.get("NVIDIA_NIM_API_KEY", "")
        self.nim_base = os.environ.get("NVIDIA_NIM_BASE_URL", "https://integrate.api.nvidia.com/v1")

    async def digest(self, topic: str = "", count: int = 5) -> str:
        from agent.scraper import read_rss, _search_engines

        feeds = []
        if topic:
            topic_lower = topic.lower()
            for key, url in DEFAULT_FEEDS.items():
                if topic_lower in key or topic_lower in url.lower():
                    feeds.append((key, url))
            if not feeds:
                for key, url in DEFAULT_FEEDS.items():
                    feeds.append((key, url))
        else:
            feeds = list(DEFAULT_FEEDS.items())

        all_news = []
        feed_label = " + ".join(k for k, _ in feeds[:3])

        for key, url in feeds[:3]:
            try:
                result = await read_rss(url, limit=5)
                if result and "❌" not in result[:5]:
                    all_news.append(f"-- {key} --\n{result}")
            except Exception:
                pass

        if all_news:
            combined = "\n\n".join(all_news)

            if self.nim_api_key:
                prompt = NEWS_SYSTEM_PROMPT.format(
                    topic=topic or "terkini",
                    sources=feed_label,
                    count=min(count, 8),
                    news_data=combined[:5000],
                )
                try:
                    async with httpx.AsyncClient(timeout=120) as client:
                        resp = await client.post(
                            f"{self.nim_base}/chat/completions",
                            headers={"Authorization": f"Bearer {self.nim_api_key}", "Content-Type": "application/json"},
                            json={
                                "model": os.environ.get("NVIDIA_NIM_MODEL", "meta/llama-3.1-70b-instruct"),
                                "messages": [{"role": "user", "content": prompt}],
                                "max_tokens": 1536,
                                "temperature": 0.2,
                            },
                        )
                        resp.raise_for_status()
                        report = resp.json()["choices"][0]["message"]["content"].strip()
                        try:
                            memory_manager.remember(
                                f"News digest: {topic or 'terkini'} ({feed_label})",
                                source="news_digest",
                                topic="news",
                                tags=["news", topic or "terkini"],
                            )
                        except Exception:
                            pass
                        return report
                except Exception as e:
                    logger.error(f"NewsDigest NIM error: {e}")

            return f"📰 *Berita {topic or 'terkini'}*\n\n{combined[:3000]}"

        try:
            results = await _search_engines(f"berita {topic} 2026", max_results=8)
            if results:
                lines = [f"🔍 Hasil pencarian berita: {topic}"]
                for r in results:
                    lines.append(f"- {r.get('title','')}")
                    lines.append(f"  🔗 {r.get('url','')}")
                    if r.get("snippet"):
                        lines.append(f"  {r['snippet'][:200]}")
                search_text = "\n".join(lines)

                if self.nim_api_key:
                    prompt = QUERY_BASED_FALLBACK.format(topic=topic, search_results=search_text)
                    try:
                        async with httpx.AsyncClient(timeout=120) as client:
                            resp = await client.post(
                                f"{self.nim_base}/chat/completions",
                                headers={"Authorization": f"Bearer {self.nim_api_key}", "Content-Type": "application/json"},
                                json={
                                    "model": os.environ.get("NVIDIA_NIM_MODEL", "meta/llama-3.1-70b-instruct"),
                                    "messages": [{"role": "user", "content": prompt}],
                                    "max_tokens": 1024,
                                    "temperature": 0.3,
                                },
                            )
                            resp.raise_for_status()
                            return resp.json()["choices"][0]["message"]["content"].strip()
                    except Exception as e:
                        logger.error(f"NewsDigest fallback NIM: {e}")

                return f"📰 *Berita: {topic}*\n\n{search_text[:2500]}"
        except Exception as e:
            logger.error(f"NewsDigest search error: {e}")

        return f"❌ Tidak ada berita ditemukan untuk '{topic}'."


news_digest = NewsDigest()
