import redis


class RedisRepository:
    def __init__(self, host, port, db, password):
        self.client = redis.Redis(host=host, port=port, db=db, password=password)

    def get_hash_key(self, hash_key, key):
        is_exist = self.client.hexists(hash_key, key)
        if not is_exist:
            return None

        value = self.client.hget(hash_key, key)
        if value is None:
            return None

        return value.decode('utf-8')

    def get_key(self, key):
        is_exist = self.client.exists(key)
        if not is_exist:
            return None

        value = self.client.get(key)
        return value.decode('utf-8')

    def set_hash_key(self, hash_key, key, value):
        self.client.hset(hash_key, key, value)

    def set_key(self, key, value):
        self.client.set(key, value)

    def hash_increase_value(self, hash_key, key, value):
        self.client.hincrby(hash_key, key, value)
