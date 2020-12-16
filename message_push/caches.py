import redis
from utils import config


class CacheConfig:
    server: str = config['redis']['server']
    port: int = config['redis']['port']
    password: str = config['redis']['password']


class RedisCache:
    """
    redis 缓存
    """
    def __init__(self, db: int = 1, ssl: bool = True):
        self.redis = redis.StrictRedis(
            host=CacheConfig.server,
            password=CacheConfig.password,
            port=CacheConfig.port,
            db=db,
            ssl=ssl
        )

    def read(self, key: str):
        return self.redis.get(key)


# 通过微信 unionid获取对应公众号的openid
class WxOpenIDCache(RedisCache):
    """
    从redis中获取对应公众号的openid
    """
    def __init__(self, db: int = 1, ssl: bool = True):
        super(WxOpenIDCache, self).__init__(db=db, ssl=ssl)


if __name__ == '__main__':
    wx_cache = WxOpenIDCache()
    print(wx_cache.read('oGTnct0FO7uoNsqhEBrwDsj66GAA'))
