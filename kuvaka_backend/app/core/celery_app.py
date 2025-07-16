from celery import Celery

celery_app = Celery(
    "kuvaka_backend",
    broker="redis://localhost:6379/0",
    backend="redis://localhost:6379/0"
)

celery_app.conf.task_routes = {  # Optional: route tasks by name
    "app.services.gemini.process_gemini_message": {"queue": "gemini"},
}
