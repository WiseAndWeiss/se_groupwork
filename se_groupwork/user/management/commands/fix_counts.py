# management/commands/fix_counts.py
from django.core.management.base import BaseCommand
from django.db.models import Count
from user.models import User, Subscription, Collection, Favorite, History, PublicAccount

class Command(BaseCommand):
    help = '修复所有统计字段的计数'
    
    def add_arguments(self, parser):
        parser.add_argument(
            '--model',
            type=str,
            help='指定要修复的模型 (user, subscription, collection, favorite, history)',
        )
    
    def handle(self, *args, **options):
        model_name = options.get('model')
        
        if not model_name or model_name == 'user':
            self.fix_user_counts()
        if not model_name or model_name == 'subscription':
            self.fix_subscription_counts()
        if not model_name or model_name == 'collection':
            self.fix_collection_counts()
        if not model_name or model_name == 'favorite':
            self.fix_favorite_counts()
        if not model_name or model_name == 'history':
            self.fix_history_counts()
        
        self.stdout.write(
            self.style.SUCCESS('✅ 所有计数修复完成!')
        )
    
    def fix_user_counts(self):
        """修复用户的各项计数"""
        self.stdout.write('修复用户计数...')
        
        # 修复用户的订阅计数
        users_with_subscriptions = User.objects.annotate(
            actual_subscription_count=Count('subscription', distinct=True)
        )
        for user in users_with_subscriptions:
            if user.subscription_count != user.actual_subscription_count:
                user.subscription_count = user.actual_subscription_count
                user.save(update_fields=['subscription_count'])
                self.stdout.write(
                    f'  用户 {user.username} 订阅计数: {user.actual_subscription_count}'
                )
        
        # 修复用户的收藏夹计数
        users_with_collections = User.objects.annotate(
            actual_collection_count=Count('collection', distinct=True)
        )
        for user in users_with_collections:
            if user.collection_count != user.actual_collection_count:
                user.collection_count = user.actual_collection_count
                user.save(update_fields=['collection_count'])
                self.stdout.write(
                    f'  用户 {user.username} 收藏夹计数: {user.actual_collection_count}'
                )
        
        # 修复用户的收藏计数
        users_with_favorites = User.objects.annotate(
            actual_favorite_count=Count('favorite', distinct=True)
        )
        for user in users_with_favorites:
            if user.favorite_count != user.actual_favorite_count:
                user.favorite_count = user.actual_favorite_count
                user.save(update_fields=['favorite_count'])
                self.stdout.write(
                    f'  用户 {user.username} 收藏计数: {user.actual_favorite_count}'
                )
        
        # 修复用户的历史记录计数
        users_with_history = User.objects.annotate(
            actual_history_count=Count('history', distinct=True)
        )
        for user in users_with_history:
            if user.history_count != user.actual_history_count:
                user.history_count = user.actual_history_count
                user.save(update_fields=['history_count'])
                self.stdout.write(
                    f'  用户 {user.username} 历史记录计数: {user.actual_history_count}'
                )
    
    def fix_subscription_counts(self):
        """修复公众号的订阅计数"""
        self.stdout.write('修复公众号订阅计数...')
        
        public_accounts = PublicAccount.objects.annotate(
            actual_subscription_count=Count('subscription', distinct=True)
        )
        for account in public_accounts:
            if account.subscription_count != account.actual_subscription_count:
                account.subscription_count = account.actual_subscription_count
                account.save(update_fields=['subscription_count'])
                self.stdout.write(
                    f'  公众号 {account.name} 订阅计数: {account.actual_subscription_count}'
                )
    
    def fix_collection_counts(self):
        """修复收藏夹的收藏计数"""
        self.stdout.write('修复收藏夹收藏计数...')
        
        collections = Collection.objects.annotate(
            actual_favorite_count=Count('favorite', distinct=True)
        )
        for collection in collections:
            if collection.favorite_count != collection.actual_favorite_count:
                collection.favorite_count = collection.actual_favorite_count
                collection.save(update_fields=['favorite_count'])
                self.stdout.write(
                    f'  收藏夹 {collection.name} 收藏计数: {collection.actual_favorite_count}'
                )
    
    def fix_favorite_counts(self):
        """修复收藏相关的计数（备用方法）"""
        self.stdout.write('检查收藏计数一致性...')
        # 这部分逻辑已经在 fix_user_counts 和 fix_collection_counts 中处理
        pass
    
    def fix_history_counts(self):
        """修复历史记录计数（备用方法）"""
        self.stdout.write('检查历史记录计数一致性...')
        # 这部分逻辑已经在 fix_user_counts 中处理
        pass