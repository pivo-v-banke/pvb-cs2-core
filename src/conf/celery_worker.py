import sys

IN_CELERY_WORKER_PROCESS = sys.argv and 'celery' in sys.argv[0] and 'worker' in sys.argv
