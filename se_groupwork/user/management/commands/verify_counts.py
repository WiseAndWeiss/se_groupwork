# management/commands/verify_counts.py
from django.core.management.base import BaseCommand
from django.db.models import Count
from user.models import User, PublicAccount, Collection

class Command(BaseCommand):
    help = '验证所有统计字段的准确性'
    
    def handle(self, *args, **options):
        self.stdout.write('开始验证计数准确性...')
        
        errors = []
        
        # 验证用户计数
        users = User.objects.annotate(
            actual_subscription_count=Count('subscription'),
            actual_collection_count=Count('collection'),
            actual_favorite_count=Count('favorite'),
            actual_history_count=Count('history'),
        )
        
        for user in users:
            if user.subscription_count != user.actual_subscription_count:
                errors.append(f'用户 {user.username} 订阅计数不准确: {user.subscription_count} vs {user.actual_subscription_count}')
            if user.collection_count != user.actual_collection_count:
                errors.append(f'用户 {user.username} 收藏夹计数不准确: {user.collection_count} vs {user.actual_collection_count}')
            if user.favorite_count != user.actual_favorite_count:
                errors.append(f'用户 {user.username} 收藏计数不准确: {user.favorite_count} vs {user.actual_favorite_count}')
            if user.history_count != user.actual_history_count:
                errors.append(f'用户 {user.username} 历史记录计数不准确: {user.history_count} vs {user.actual_history_count}')
        
        # 验证公众号计数
        public_accounts = PublicAccount.objects.annotate(
            actual_subscription_count=Count('subscription')
        )
        for account in public_accounts:
            if account.subscription_count != account.actual_subscription_count:
                errors.append(f'公众号 {account.name} 订阅计数不准确: {account.subscription_count} vs {account.actual_subscription_count}')
        
        # 验证收藏夹计数
        collections = Collection.objects.annotate(
            actual_favorite_count=Count('favorite')
        )
        for collection in collections:
            if collection.favorite_count != collection.actual_favorite_count:
                errors.append(f'收藏夹 {collection.name} 收藏计数不准确: {collection.favorite_count} vs {collection.actual_favorite_count}')
        
        if errors:
            self.stdout.write(self.style.ERROR('❌ 发现计数不准确:'))
            for error in errors:
                self.stdout.write(self.style.ERROR(f'  - {error}'))
        else:
            self.stdout.write(self.style.SUCCESS('✅ 所有计数准确无误!'))