import unittest
import requests
from redis import Redis


class TestFetch(unittest.TestCase):
    def setUp(self):
        self.redis = Redis('localhost')
        self.key = 'yoyo'

    def test_redis_unicode(self):
        s = u'\u003cfoo/\u003e'
        self.redis.set(self.key, s)
        result = self.redis.get(self.key)
        self.assertEqual(s, result)

    def test_requests_unicode(self):
        url = 'http://search.cmgdigital.com/v2/guid/?g=https://identifiers.cmgdigital.com/medley/prod/medley_lists.fastautolist/2725/&format=json&detail=full'
        text = requests.get(url).text
        self.redis.set(self.key, text)
        result = self.redis.get(self.key).decode('utf-8')
        # import pdb; pdb.set_trace()
        self.assertEqual(text, result)



if __name__ == '__main__':
    unittest.main()
