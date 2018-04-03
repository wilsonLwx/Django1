# 验证是否登录的工具类
from django.contrib.auth.decorators import login_required
from django.utils.decorators import classonlymethod


class LoginRequired(object):
    @classonlymethod
    def as_view(cls, **initkwargs):
        # 调用父类的as_view()方法
        view = super().as_view(**initkwargs)
        return login_required(view)
