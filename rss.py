from flask import make_response, Flask
import requests
import re
from feedgen.feed import FeedGenerator
from dataclasses import dataclass


@dataclass
class Article:
    title: str
    content: str


def get_news():
    source = requests.get(
        "https://www.ft.com/myft/following/269dc2ef-c8a1-4264-9b86-8f591050edff.rss"
    ).text
    titles = re.findall(
        # start of title is matched but not included
        r"(?:<title><!\[CDATA\[)"
        # content is captured
        r"(.*?)"
        # end of title is matched but not included
        r"(?:\]\]><\/title>)",
        source,
    )
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
        source,
    )

    contents = ["".join(content) for content in contents_segmented]

    return [Article(titles[i], contents[i]) for i in range(len(titles))]


app = Flask(__name__)


@app.route("/rss")
def rss():
    fg = FeedGenerator()
    fg.title("Ibrahim's FT Feed")
    fg.description("A DAKboard friendly FT news feed")
    fg.link(href="https://awesome.com")

    for article in get_news():
        fe = fg.add_entry()
        fe.title(article.title)
        fe.content(article.content, type="CDATA")
    print(fg.rss_str())
    response = make_response(fg.rss_str())
    response.headers.set("Content-Type", "application/rss+xml")
    return response


if __name__ == "__main__":
    from waitress import serve

    serve(app, host="0.0.0.0", port=4580)


# get_news()
