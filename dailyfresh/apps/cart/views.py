from django.http import JsonResponse
from django.shortcuts import render

# Create your views here.
from django.views.generic import View
from django_redis import get_redis_connection

from goods.models import GoodsSKU


class AddCartView(View):
    """添加购物车"""

    def post(self, request):
        # 用户信息user
        user = request.user

        # 验证客户是否有登陆
        if not user.is_authenticated():
            return JsonResponse({'code': 5, 'msg': '用户未登录'})

        # 应该接受的商品信息 skuid 数量count
        sku_id = request.POST.get('sku_id')
        count = request.POST.get('count')

        # 判断数据是否为空
        if not all([sku_id, count]):
            return JsonResponse({'code': 1, 'msg': '参数不全'})

        # 查询数据库中是否有该商品
        try:
            sku = GoodsSKU.objects.get(id=sku_id)
        except GoodsSKU.DoesNotExist:
            return JsonResponse({'code': 2, 'msg': '商品不存在'})

        try:
            count = int(count)
        except Exception:
            return JsonResponse({'code': 3, 'msg': '商品数量不正确'})

        # 判断数量是否大于库存
        if count > sku.stock:
            return JsonResponse({'code': 4, 'msg': '库存不足'})

        # 保存数据到redis
        # 获取redis链接对象
        redis_conn = get_redis_connection('default')
        # 判断redis之前是否已经存在该商品 若有就累加
        origin_count = redis_conn.hget('cart_%s' % user.id, sku_id)
        if origin_count:
            # redis 存的是str 需要强转
            count += int(origin_count)

        # 保存商品的redis
        redis_conn.hset('cart_%s' % user.id, sku_id, count)

        return JsonResponse({'code': 0, 'msg': '添加购物车成功'})
