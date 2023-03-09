import datetime
from pip import main
import json
import feedparser
import hashlib


def rss_feeder(feed_url):
    #feed to db
    feed = feedparser.parse(feed_url)
    feed_data = [{ 
                    "title": entry.title,
                    "summary": entry.summary,
                    "link": entry.link,
                    "published": entry.published,
                } for entry in feed.entries ]
    # print(feed)
    hash_key = generate_hash(feed_data)
    print(hash_key)
    return hash_key,feed

def generate_hash(feed):
    return hashlib.md5(json.dumps(feed).encode('UTF-8')).hexdigest()

