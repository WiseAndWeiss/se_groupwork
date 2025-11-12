from django.apps import AppConfig


class ArticleselectorConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "article_selector"

    def ready(self):
        import article_selector.signals
