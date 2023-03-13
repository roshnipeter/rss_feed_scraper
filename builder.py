import json
import feedparser
import hashlib
import re

from pip import main


def rss_feeder(feed_url) -> tuple:
    """
    Parses an RSS Feed and returns it's data as a list opf dictionaries, along with the hash-key of feed URL
    Args:
        feed_url: The URL which needs to be parsed.

    Returns:
        A tuple containing:
            - The hash-key of URL
            - A list of dictionariies that represent the parsed RSS feed. The elements of the dict are:
                - "title" - Title of the entry
                - "summary" - Summary of the entry
                - "link" - The link associatied with the entry
                - "published" - The published date of the entry.
            These are a sample subset of the data taken from RSS parser.
    Example usage:

    hash_key, feed_data = rss_feeder("https://www.example.com/rss.xml")
    """
    feed = feedparser.parse(feed_url)
    feed_data = [{ 
                    "title": entry.title,
                    "summary": entry.summary,
                    "link": entry.link,
                    "published": entry.published,
                } for entry in feed.entries]
    hash_key = generate_hash(feed_url)
    return hash_key, feed_data


def generate_hash(feed_url):
    """
    Returns a hashed value of the URL passed
    Args:
        feed_url: URL that needs to be hashed.

    Returns:
        A string representing the hashed url
    Example usage:

    hash_key = generate_hash("https://www.example.com/rss.xml")
    """

    return hashlib.md5(json.dumps(re.sub('[^A-Za-z0-9]+', '', feed_url)).encode('UTF-8')).hexdigest()

