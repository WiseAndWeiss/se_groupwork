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
        
        # 先直接查询数据库获取实际计数
        users = User.objects.all()
        for user in users:
            # 直接查询数据库计数
            actual_subscription_count = Subscription.objects.filter(user=user).count()
            actual_collection_count = Collection.objects.filter(user=user).count()
            actual_favorite_count = Favorite.objects.filter(user=user).count()
            actual_history_count = History.objects.filter(user=user).count()
            
            # 更新不匹配的计数
            if user.subscription_count != actual_subscription_count:
                user.subscription_count = actual_subscription_count
                self.stdout.write(f'  用户 {user.username} 订阅计数: {actual_subscription_count}')
            
            if user.collection_count != actual_collection_count:
                user.collection_count = actual_collection_count
                self.stdout.write(f'  用户 {user.username} 收藏夹计数: {actual_collection_count}')
            
            if user.favorite_count != actual_favorite_count:
                user.favorite_count = actual_favorite_count
                self.stdout.write(f'  用户 {user.username} 收藏计数: {actual_favorite_count}')
            
            if user.history_count != actual_history_count:
                user.history_count = actual_history_count
                self.stdout.write(f'  用户 {user.username} 历史记录计数: {actual_history_count}')
            
            # 保存所有更改
            user.save()
    
    def fix_subscription_counts(self):
        """修复公众号的订阅计数"""
        self.stdout.write('修复公众号订阅计数...')
        
        public_accounts = PublicAccount.objects.all()
        for account in public_accounts:
            actual_count = Subscription.objects.filter(public_account=account).count()
            if account.subscription_count != actual_count:
                account.subscription_count = actual_count
                account.save(update_fields=['subscription_count'])
                self.stdout.write(f'  公众号 {account.name} 订阅计数: {actual_count}')
    
    def fix_collection_counts(self):
        """修复收藏夹的收藏计数"""
        self.stdout.write('修复收藏夹收藏计数...')
        
        collections = Collection.objects.all()
        for collection in collections:
            actual_count = Favorite.objects.filter(collection=collection).count()
            if collection.favorite_count != actual_count:
                collection.favorite_count = actual_count
                collection.save(update_fields=['favorite_count'])
                self.stdout.write(f'  收藏夹 {collection.name} 收藏计数: {actual_count}')
    
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