from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required

from user.models import Subscription
from webspider.models import PublicAccount


# Create your views here.

@login_required
def subscribe(request, fakeid):
    account = get_object_or_404(PublicAccount, pk=fakeid)
    # 创建或更新订阅记录
    sub, created = Subscription.objects.get_or_create(
        user=request.user,
        public_account=account,
        defaults={'is_active': True}
    )
    if not created and not sub.is_active:
        sub.is_active = True  # 重新激活已取消的订阅
        sub.save()
    return redirect('account_list')


@login_required
def unsubscribe(request, fakeid):
    account = get_object_or_404(PublicAccount, pk=fakeid)
    Subscription.objects.filter(
        user=request.user,
        public_account=account
    ).update(is_active=False)  # 软删除：仅标记为取消
    return redirect('account_list')