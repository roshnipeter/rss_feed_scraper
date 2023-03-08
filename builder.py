import datetime
from pip import main
import json
import feedparser
import es_service
import hashlib


def rss_feeder(feed_url):
    #feed to db
    feed = feedparser.parse(feed_url)
    hash_key = generate_hash(feed)
    return hash_key,feed

def generate_hash(feed):
    return hashlib.md5(json.dumps(sorted(feed)).encode('UTF-8')).hexdigest()

def write_to_es(feed, url, userId):
    es_record = {
        '@timestamp': datetime.now(),
        'feedData' : json.dumps(feed),
        'url' : url,
        'userId': userId,
        'marked' : False,

    }
    es_service.add_data("rss_feeds",es_record)

def read_data(userId):
    userId = userId
    marked = False
    result, count = es_service.get_audit_log(userId, marked)

def main():
    url = "http://www.nu.nl/rss/Algemeen"
    feed = rss_feeder(url)
    write_to_es(feed, url, userId='100A1')

if __name__ == '__main__':
    main()

