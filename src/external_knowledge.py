from dataclasses import dataclass
import requests

@dataclass
class ExternalSource:
    provider:str
    title:str
    url:str
    content:str


class WikipediaProvider:
    def __init__(self, language: str = 'en'):
        self.language = language

        self.api_url = f"https://{self.language}.wikipedia.org/w/api.php"

        self.session = requests.Session()

        self.session.headers.update({
            "User-Agent": "ActiveRecallRAG/0.1 (personal learning project)"
        })

    def search(self, query: str, limit:int = 3) -> list[ExternalSource]:
        titles = self._search_titles(query, limit)
    
        if not titles:
            return []

        return self._get_pages(titles)

    def _search_titles(self, query: str, limit:int = 3) -> list[str]:
        params = {
            "action": "query",
            "list": "search",
            "srsearch": query,
            "srlimit": limit,
            "format": "json",
            "formatversion": 2 
        }

        response = self.session.get(
            self.api_url,
            params=params,
            timeout=10
        )

        response.raise_for_status()

        data = response.json()

        results = data.get("query", {}).get("search", [])

        return [result["title"] for result in results]

    def _get_pages(self, titles: list[str]) -> list[ExternalSource]:
        params = {
            "action": "query",
            "prop": "extracts|info",
            "titles": "|".join(titles),
            "explaintext": True,
            "exintro": True,

            "inprop": "url",
            "format": "json",
            "formatversion": 2
        }

        response = self.session.get(
            self.api_url,
            params=params,
            timeout=10
        )

        response.raise_for_status()

        data = response.json() 

        pages = data.get("query", {}).get("pages", [])

        sources = []

        for page in pages:
            content = page.get("extract", "").strip()

            if not content:
                continue

            source = ExternalSource(
                provider="wikipedia",
                title=page.get("title", ""),
                url=page.get("fullurl", ""),
                content=content
            )

            sources.append(source)

        return sources

def should_use_external_knowledge(
    target_content:str,
    supporting_results: list[dict],
    difficulty:int,
    mode: str = "when_needed"
):
    if mode == "always":
        return True

    if mode == "never":
        return False

    if mode != "when_needed":
        raise ValueError(f"Invalid mode: {mode}. Must be 'always', 'never', or 'when_needed'.")

    content_length = len(target_content.strip())

    best_support_score = max((result["score"] for result in supporting_results), default=0.0)

    note_is_short = content_length < 600

    weak_related_context = best_support_score < 0.5

    advanced_question = difficulty >= 4 

    return note_is_short or weak_related_context or advanced_question