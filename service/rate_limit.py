from config import ORG_LIMIT_KEY, ORG_COUNT_KEY, STAFF_LIMIT_KEY, STAFF_COUNT_KEY
from repository.redis_repository import RedisRepository


class RateLimitService:

    def __init__(self, redis_repository: RedisRepository):
        self.redis_repository = redis_repository

    def validate_org_limit_exceed(self, org_id):
        org_limit_value = self.redis_repository.get_hash_key(ORG_LIMIT_KEY, org_id)
        org_total_request = self.redis_repository.get_hash_key(ORG_COUNT_KEY, org_id)
        if org_total_request is None:
            org_total_request = 0
        else:
            org_total_request = int(org_total_request)

        if org_limit_value is None:
            org_limit_value = 0
        else:
            org_limit_value = int(org_limit_value)

        if org_total_request >= org_limit_value:
            return True

        return False

    def validate_staff_limit(self, staff_id):
        staff_limit_value = self.redis_repository.get_hash_key(STAFF_LIMIT_KEY, staff_id)
        staff_total_request = self.redis_repository.get_hash_key(STAFF_COUNT_KEY, staff_id)
        if staff_total_request is None:
            staff_total_request = 0
        else:
            staff_total_request = int(staff_total_request)

        if staff_limit_value is None:
            staff_limit_value = 0
        else:
            staff_limit_value = int(staff_limit_value)

        if staff_total_request >= staff_limit_value:
            return True

        return False

    def count_organization_request(self, org_id, number_of_requests):
        self.redis_repository.hash_increase_value(ORG_COUNT_KEY, org_id, number_of_requests)

    def count_staff_request(self, staff_id, number_of_requests):
        self.redis_repository.hash_increase_value(STAFF_COUNT_KEY, staff_id, number_of_requests)
