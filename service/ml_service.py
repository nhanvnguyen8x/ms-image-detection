from random import randint
from time import sleep


class MlService:

    def placeholder_function(self, params = None):
        sleep(randint(1, 10))
        return {
            'result': '0.89579',
            'result_path': "",
            'job_status': 'COMPLETED'
        }
