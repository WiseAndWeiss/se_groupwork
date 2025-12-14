from django.apps import AppConfig


class AskaiConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "askAI"

    def ready(self):
        import askAI.signals