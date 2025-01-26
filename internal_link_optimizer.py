import aiohttp
import asyncio
from bs4 import BeautifulSoup
import numpy as np
import pandas as pd
import re
from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity
from tqdm.asyncio import tqdm_asyncio
from typing import List, Dict, Tuple

class AsyncScraper:
    def __init__(self, concurrency=50):
        self.concurrency = concurrency
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
        }
    
    async def _fetch(self, session, url):
        try:
            async with session.get(url, timeout=10, headers=self.headers) as response:
                return await response.text()
        except Exception as e:
            print(f"Error fetching {url}: {str(e)}")
            return None
    
    async def scrape_urls(self, base_url: str, paths: List[str]) -> Dict[str, str]:
        connector = aiohttp.TCPConnector(limit=self.concurrency)
        async with aiohttp.ClientSession(connector=connector) as session:
            tasks = [self._fetch(session, f"{base_url.rstrip('/')}{path}") for path in paths]
            results = await tqdm_asyncio.gather(*tasks, desc="Scraping URLs")
            return {path: self._clean_html(html) for path, html in zip(paths, results) if html}
    
    def _clean_html(self, html: str) -> str:
        soup = BeautifulSoup(html, 'html.parser')
        for element in soup(['nav', 'footer', 'header', 'script', 'style', 'aside']):
            element.decompose()
        main_content = soup.find(['article', 'main']) or soup
        return ' '.join(main_content.stripped_strings)

class ContextGenerator:
    def __init__(self, openai_api_key: str):
        self.openai_api_key = openai_api_key
    
    def find_best_context(self, source_text: str, target_keywords: List[str]) -> str:
        sentences = re.split(r'(?<!\w\.\w.)(?<![A-Z][a-z]\.)(?<=\.|\?)\s', source_text)
        keyword_scores = [
            sum(sentence.lower().count(kw.lower()) for kw in target_keywords)
            for sentence in sentences
        ]
        if max(keyword_scores) > 0:
            return sentences[np.argmax(keyword_scores)]
        return None
    
    async def generate_snippet(self, source_topic: str, anchor_text: str) -> str:
        try:
            response = openai.ChatCompletion.create(
                model="gpt-3.5-turbo",
                messages=[{
                    "role": "user",
                    "content": f"Write a 1-sentence content snippet about '{source_topic}' that naturally includes this anchor text: '{anchor_text}'. Use a professional tone."
                }]
            )
            return response.choices[0].message['content'].strip('"')
        except Exception as e:
            print(f"OpenAI Error: {str(e)}")
            return f"Learn more about {anchor_text}."

# [Keep previous InternalLinkOptimizer class from prototype and add...]

    async def analyze_with_context(self, df: pd.DataFrame, max_links=3) -> pd.DataFrame:
        # Previous analysis logic plus...
        context_gen = ContextGenerator(self.openai_api_key)
        
        for result in tqdm(results, desc="Generating context"):
            source_text = df[df['URL'] == result['Source URL']]['Body Content'].values[0]
            target_keywords = df[df['URL'] == result['Destination URL']]['Keywords'].values[0]
            
            # Find existing context
            existing_context = context_gen.find_best_context(
                source_text, 
                eval(target_keywords) if isinstance(target_keywords, str) else target_keywords
            )
            
            if existing_context:
                result['Context'] = f"ADD TO EXISTING CONTENT: '{existing_context}'"
            else:
                result['Context'] = await context_gen.generate_snippet(
                    source_text[:100], 
                    result['Anchor Text']
                )
        
        return pd.DataFrame(results)
