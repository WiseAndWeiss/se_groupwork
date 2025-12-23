from django.core.management.base import BaseCommand
from user.models import User, PublicAccount, Collection, Subscription, Favorite, History

class Command(BaseCommand):
    help = '验证所有统计字段的准确性'
    
    def handle(self, *args, **options):
        self.stdout.write('开始验证计数准确性...')
        
        errors = []
        
        # 验证用户计数 - 使用直接查询方法
        users = User.objects.all()
        for user in users:
            actual_subscription_count = Subscription.objects.filter(user=user).count()
            actual_collection_count = Collection.objects.filter(user=user).count()
            actual_favorite_count = Favorite.objects.filter(user=user).count()
            actual_history_count = History.objects.filter(user=user).count()
            
            if user.subscription_count != actual_subscription_count:
                errors.append(f'用户 {user.username} 订阅计数不准确: {user.subscription_count} vs {actual_subscription_count}')
            if user.collection_count != actual_collection_count:
                errors.append(f'用户 {user.username} 收藏夹计数不准确: {user.collection_count} vs {actual_collection_count}')
            if user.favorite_count != actual_favorite_count:
                errors.append(f'用户 {user.username} 收藏计数不准确: {user.favorite_count} vs {actual_favorite_count}')
            if user.history_count != actual_history_count:
                errors.append(f'用户 {user.username} 历史记录计数不准确: {user.history_count} vs {actual_history_count}')
        
        # 验证公众号计数
        public_accounts = PublicAccount.objects.all()
        for account in public_accounts:
            actual_count = Subscription.objects.filter(public_account=account).count()
            if account.subscription_count != actual_count:
                errors.append(f'公众号 {account.name} 订阅计数不准确: {account.subscription_count} vs {actual_count}')
        
        # 验证收藏夹计数
        collections = Collection.objects.all()
        for collection in collections:
            actual_count = Favorite.objects.filter(collection=collection).count()
            if collection.favorite_count != actual_count:
                errors.append(f'收藏夹 {collection.name} 收藏计数不准确: {collection.favorite_count} vs {actual_count}')
        
        if errors:
            self.stdout.write(self.style.ERROR('❌ 发现计数不准确:'))
            for error in errors:
                self.stdout.write(self.style.ERROR(f'  - {error}'))
        else:
            self.stdout.write(self.style.SUCCESS('✅ 所有计数准确无误!'))