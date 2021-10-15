from flask import make_response, Flask
import requests
import re
from feedgen.feed import FeedGenerator
from dataclasses import dataclass
from abc import ABC, abstractclassmethod


@dataclass
class Article:
    """Represents a single article, containing a title and a contents string."""

    title: str
    content: str


class News(ABC):
    """Represents a source of news, and sanitizes the data"""

    def __init__(self, source: str):
        raw_news = self.fetch_news(source)
        sanitised_news = self.get_sanitised_news(raw_news)
        self.news = [
            Article(title, content) for title, content in sanitised_news.items()
        ]

    def fetch_news(self, source: str) -> str:
        return requests.get(source).text

    @abstractclassmethod
    def get_titles() -> list[str]:
        pass

    @abstractclassmethod
    def get_contents() -> list[str]:
        pass

    def get_sanitised_news(self, raw_news: str) -> dict:
        return dict(zip(self.get_titles(raw_news), self.get_titles(raw_news)))


class FT(News):
    """Represents a source of news from the Financial Times"""

    def __init__(self, source: str):
        super().__init__(source)

    def get_titles(self, raw_news: str):
        return re.findall(
            # start of title is matched but not included
            r"(?:<title><!\[CDATA\[)"
            # content is captured
            r"(.*?)"
            # end of title is matched but not included
            r"(?:\]\]><\/title>)",
            raw_news,
        )

    def get_contents(self, raw_news: str):
        contents_segmented = re.findall(
            # finds the start of the content tag
            r"(?:<description><!\[CDATA\[)"
            # removes any embedded images
            r"(?:<img.*?>)*"
            # removes any links before the content or in case content is empty
            r"(?:<a href=.*?<\/a>)*"
            # content is captured
            r"(.*?)"
            # removes  links after the content
            r"(?:<br \/><a href=.*?)*"
            # finds the end of the content section
            r"(?:\]\]><\/description>)",
            raw_news,
        )
        return ["".join(content) for content in contents_segmented]


app = Flask(__name__)


@app.route("/rss")
def rss():
    fg = FeedGenerator()
    fg.title("Ibrahim's FT Feed")
    fg.description("A DAKboard friendly FT news feed")
    fg.link(href="https://awesome.com")

    for article in FT(
        "https://www.ft.com/myft/following/269dc2ef-c8a1-4264-9b86-8f591050edff.rss"
    ).news:
        fe = fg.add_entry()
        fe.title(article.title)
        fe.content(article.content, type="CDATA")

    response = make_response(fg.rss_str())
    response.headers.set("Content-Type", "application/rss+xml")
    return response


if __name__ == "__main__":
    from waitress import serve

    serve(app, host="0.0.0.0", port=4580)
