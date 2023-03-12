from pip import main
import json
import feedparser
import hashlib
import re


def rss_feeder(feed_url):
    #feed to db
    feed = feedparser.parse(feed_url)
    feed_data = [{ 
                    "title": entry.title,
                    "summary": entry.summary,
                    "link": entry.link,
                    "published": entry.published,
                } for entry in feed.entries ]
    hash_key = generate_hash(feed_url)
    return hash_key,feed_data

def generate_hash(feed_url):
    return hashlib.md5(json.dumps(re.sub('[^A-Za-z0-9]+', '', feed_url)).encode('UTF-8')).hexdigest()

