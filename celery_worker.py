from app.core.celery_app import celery_app

if __name__ == "__main__":
    celery_app.worker_main()
