from django.core.management.base import BaseCommand
from askAI.askAI.ai_ask import ask_ai, get_reference_articles
from webspider.models import Article

class Command(BaseCommand):
    help = 'Ask AI for information'
    
    def add_arguments(self, parser):
        parser.add_argument('question', type=str, help='The question to ask AI')

    def handle(self, *args, **options):
        question = options['question']
        articles = get_reference_articles(question)
        content = [article.content for article in articles]
        for chunk in ask_ai(question, content):
            print(chunk, end='')
        print("\n[参考文献]")
        for article in articles:
            print(f"- {article.id} {article.title}({article.article_url})")
