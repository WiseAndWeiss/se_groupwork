from django.core.management.base import BaseCommand
from webspider.models import Article
from se_groupwork.global_tools import global_sqlvec_tool_load

class Command(BaseCommand):
    help = 'load once and do as command'
    
    def handle(self, *args, **kwargs):
        sqlvecTool = global_sqlvec_tool_load()
        while True:
            t = input("Enter command: ")
            t = t.split()
            cmd = t[0]
            if len(t) > 1: argv = t[1:]
            if cmd == "exit":
                break
            elif cmd == "all_articles":
                res = sqlvecTool.get_all_articles_ids_in_index()
                print(f"{len(res)} articles in sqlvec index totally")
                print(res)
            elif cmd == "update_article":
                target_id = argv[0]
                sqlvecTool.update_article(target_id)
            elif cmd == "update_articles":
                target_ids = argv
                sqlvecTool.update_articles(target_ids)
            elif cmd == "update_all":
                sqlvecTool.update_all_articles()
            elif cmd == 'clear':
                sqlvecTool.clear_index()
            elif cmd == 'rebuild':
                sqlvecTool.rebuild_index()
            elif cmd == 'search':
                query = argv[0]
                res = sqlvecTool.search(query)
                for id, score in res:
                    article = Article.objects.get(id=id)
                    print(f"- {id}({score}) {article.title}")
            else:
                print("Unknown command")
            print("-----------------------------------------------\n")
        return