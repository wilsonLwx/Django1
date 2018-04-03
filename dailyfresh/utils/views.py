from django.contrib.auth.decorators import login_required
from django.utils.decorators import classonlymethod


# 验证是否登录的工具类,谁需要谁继承
class LoginRequiredMixin(object):
    @classonlymethod
    def as_view(cls, **initkwargs):
        # 调用父类的as_view()方法
        view = super().as_view(**initkwargs)
        return login_required(view)
