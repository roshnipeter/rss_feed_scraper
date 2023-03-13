import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)) + "/../")
import builder

class TestBuilder:
    
    @classmethod
    def setup_class(cls):
        pass

    @classmethod
    def teardown_class(cls):
        pass
        
    def test_rss_feeder(cls):
        hash_key, feeds = builder.rss_feeder('http://www.nu.nl/rss/Algemeen')
        assert isinstance(hash_key, str)
        assert isinstance(feeds, list)

        assert all(isinstance(entry, dict) for entry in feeds)
        assert all("title" in entry for entry in feeds)
        assert all("summary" in entry for entry in feeds)
        assert all("link" in entry for entry in feeds)
        assert all("published" in entry for entry in feeds)
    
    def test_generate_hash(cls):
        hash_key = builder.generate_hash('http://www.nu.nl/rss/Algemeen')
        assert hash_key == '489dd89f4b0474b26f5247c2fa5257f7'


