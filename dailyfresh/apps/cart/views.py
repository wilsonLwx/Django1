import json

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

        # 获取redis链接对象
        redis_conn = get_redis_connection('default')

        # cart_dict = {}
        if user.is_authenticated():
            # 保存数据到redis

            # 判断redis之前是否已经存在该商品 若有就累加
            origin_count = redis_conn.hget('cart_%s' % user.id, sku_id)
            if origin_count:
                # redis 存的是str 需要强转
                count += int(origin_count)

            # 保存商品的redis
            redis_conn.hset('cart_%s' % user.id, sku_id, count)
        else:
            # 用户未登录 数据存到cookie中
            # 获取商品之前的数量
            cart_json = request.COOKIES.get('cart')
            if cart_json:
                # 将json字符串转换成字典
                cart_dict = json.loads(cart_json)
            else:
                cart_dict = {}

            if sku_id in cart_dict:
                # 获取商品之前的数量
                origin_count = cart_dict.get(sku_id)
                count += origin_count
            cart_dict['sku_id'] = count

        # 查询购物车商品的所有数量
        cart_num = 0

        # 如果有登陆 从redis查询数据
        if user.is_authenticated():
            cart_dict = redis_conn.hgetall('cart_%s' % user.id)


        # 获取总的数量
        for val in cart_dict.values():
            cart_num += int(val)

        response = JsonResponse({'code': 0, 'msg': '添加购物车成功', 'cart_num': cart_num})
        if not user.is_authenticated():
            cart_json = json.dumps(cart_dict)
            response.set_cookie('cart', cart_json)

        return response
