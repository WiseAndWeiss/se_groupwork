from django.core.management.base import BaseCommand
from webspider.models import Article
from se_groupwork.global_tools import global_faiss_tool_load

class Command(BaseCommand):
    help = 'load once and do as command'
    
    def handle(self, *args, **kwargs):
        faissTool = global_faiss_tool_load()
        while True:
            t = input("Enter command: ")
            t = t.split()
            cmd = t[0]
            if len(t) > 1: argv = t[1:]
            if cmd == "exit":
                break
            elif cmd == "all_articles":
                res = faissTool.get_all_articles_ids_in_index()
                print(f"{len(res)} articles in faiss index totally")
                print(res)
            elif cmd == "update_article":
                target_id = argv[0]
                faissTool.update_article(target_id)
            elif cmd == "update_articles":
                target_ids = argv
                faissTool.update_articles(target_ids)
            elif cmd == "update_all":
                faissTool.update_all_articles()
            elif cmd == 'clear':
                faissTool.clear_index()
            elif cmd == 'rebuild':
                faissTool.rebuild_index()
            elif cmd == 'search':
                query = argv[0]
                res = faissTool.search(query)
                for id, score in res:
                    article = Article.objects.get(id=id)
                    print(f"- {id}({score}) {article.title}")
            else:
                print("Unknown command")
            print("-----------------------------------------------\n")
        return