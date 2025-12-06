from django.apps import AppConfig


class WebspiderConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'webspider'
    def ready(self):
        # 导入信号处理程序
        import webspider.signals
