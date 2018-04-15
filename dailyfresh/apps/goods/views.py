from django.core.cache import cache
from django.core.paginator import Paginator, EmptyPage
from django.core.urlresolvers import reverse
from django.shortcuts import render, redirect

# Create your views here.
from django.template import loader
from django.views.generic import View
from django_redis import get_redis_connection

from goods.models import GoodsCategory, IndexGoodsBanner, \
    IndexPromotionBanner, IndexCategoryGoodsBanner, GoodsSKU


class IndexView(View):
    def get(self, request):

        # 先从redis中获取缓存数据
        context = cache.get('index_page_static_cache')

        if context is None:
            print('缓存中没有数据')
            """如果缓存中没有数据就到数据库中查找"""
            # 显示首页
            # 商品分类的全部数据
            categorys = GoodsCategory.objects.all()
            # 幻灯片
            banners = IndexGoodsBanner.objects.all()
            # 活动
            promotion_banners = IndexPromotionBanner.objects.all()
            # # 首页所有的分类商品数据
            # goodsbanners = IndexCategoryGoodsBanner.objects.all()
            #

            for category in categorys:
                # 查询对应类别下的数据
                # display_type = 0 是标题类商品  1是图片类商品 按照index排序
                title_banners = IndexCategoryGoodsBanner.objects.filter(
                    category=category, display_type=0).order_by('index')
                # 把数据以属性的形式存到category对象中
                category.title_banners = title_banners

                image_banners = IndexCategoryGoodsBanner.objects.filter(
                    category=category, display_type=1).order_by('index')
                category.image_banners = image_banners

            context = {
                'categorys': categorys,
                'banners': banners,
                'promotion_banners': promotion_banners
            }

            # content 是数据渲染好的最终html代码 是根据render方法内部源码实现的
            # 文件流 耗时操作 celery 异步执行
            # content = loader.render_to_string('index.html', context)

            # print(content)
            # 把登录后用的相同数据 保存到缓存里 不用每次都去查找 settings里的CACHES指定了缓存默认存储路径
            cache.set('index_page_static_cache', context, 3600)
        else:
            print("使用的是缓存数据")

        cart_num = 0
        user = request.user

        # 用户已经登录
        if user.is_authenticated():
            # 获取redis链接实例
            redis_conn = get_redis_connection('default')

            # 获取购物车数据
            cart_dict = redis_conn.hgetall('cart_%s' % user.id)
            for cart in cart_dict.values():
                # 计算购物车的总数量
                cart_num += int(cart)
        # 将数据添加到context里
        context['cart_num'] = cart_num

        return render(request, 'index.html', context)


class DetailView(View):
    """商品详细信息页面"""

    def get(self, request, sku_id):
        # 尝试获取缓存数据
        context = cache.get("detail_%s" % sku_id)
        # 如果缓存没数据 就去数据库中查询数据
        if context is None:
            try:
                # 获取商品信息
                sku = GoodsSKU.objects.get(id=sku_id)
            except GoodsSKU.DoesNotExist:
                return redirect(reverse('goods:index'))

            # 获取类别
            categorys = GoodsCategory.objects.all()

            # 从订单中获取评论信息
            sku_orders = sku.ordergoods_set.all().order_by('-create_time')[:30]
            if sku_orders:
                for sku_order in sku_orders:
                    sku_order.ctime = sku_order.create_time.strftime('%Y-%m-%d %H:%M:%S')
                    sku_order.username = sku_order.order.user.username
            else:
                sku_order = []

            # 获取最新推荐
            new_skus = GoodsSKU.objects.filter(category=sku.category).order_by('-create_time')[:2]

            # 获取其他规格的商品
            other_skus = sku.goods.goodssku_set.exclude(id=sku_id)

            context = {
                'categorys': categorys,
                'sku': sku,
                'orders': sku_orders,
                'new_skus': new_skus,
                'other_skus': other_skus
            }
            # 设置缓存
            cache.set("detail_%s" % sku_id, context, 3600)

        cart_num = 0
        user = request.user

        # 用户已经登录
        if user.is_authenticated():
            # 获取redis链接实例
            redis_conn = get_redis_connection('default')

            # 获取购物车数据
            cart_dict = redis_conn.hgetall('cart_%s' % user.id)
            for cart in cart_dict.values():
                # 计算购物车的总数量
                cart_num += int(cart)
            # 移除已经存在的本商品浏览历史记录
            redis_conn.lrem('history_%s' % user.id, 0, sku_id)
            # 添加新的浏览记录
            redis_conn.lpush('history_%s' % user.id, sku_id)
            # 只保存最多5条记录
            redis_conn.ltrim('history_%s' % user.id, 0, 4)

        # 将数据添加到context里
        context['cart_num'] = cart_num

        return render(request, 'detail.html', context)


class ListView(View):
    def get(self, request, category_id, page):
        # 获取排序
        sort = request.GET.get('sort')
        # 当前类别
        try:
            category = GoodsCategory.objects.get(id=category_id)
        except GoodsCategory.DoesNotExist:
            return redirect(reverse('goods:index'))

        # 所有类别
        categorys = GoodsCategory.objects.all()

        # 新品推荐
        new_skus = GoodsSKU.objects.filter(category=category).order_by('-create_time')[:2]

        # 排序 默认defaul 价格price 人气hot
        if sort == 'price':
            # 所有商品
            skus = GoodsSKU.objects.filter(category=category).order_by('price')
        elif sort == 'hot':
            skus = GoodsSKU.objects.filter(category=category).order_by('-sales')
        else:
            # 排序
            sort = 'default'
            skus = GoodsSKU.objects.filter(category=category)

        # 分页
        paginator = Paginator(skus, 2)
        page = int(page)

        # 当向page()提供一个有效值，但是那个页面上没有任何对象时抛出EmptyPage
        try:
            skus_page = paginator.page(page)
        except EmptyPage:
            page = 1
            skus_page = paginator.page(page)

        # 如果总页数小于等于五 有多少页就返回多少页
        if paginator.num_pages <= 5:
            page_list = paginator.page_range
        # 当前页小于等于三 page_list=[1,2,3,4,5]
        elif page <= 3:
            page_list = range(1, 6)
        # 当前页处于最后三页的时候   page_list 为最后五页
        elif paginator.num_pages - page <= 2:
            page_list = range(paginator.num_pages - 4, paginator.num_pages + 1)
        # 其他情况
        else:
            page_list = range(page - 2, page + 3)


        context = {
            'sort': sort,
            'category': category,
            'categorys': categorys,
            'new_skus': new_skus,
            'skus_page': skus_page,
            'page_list': page_list,
        }
        cart_num = 0
        user = request.user

        # 用户已经登录
        if user.is_authenticated():
            # 获取redis链接实例
            redis_conn = get_redis_connection('default')

            # 获取购物车数据
            cart_dict = redis_conn.hgetall('cart_%s' % user.id)
            for cart in cart_dict.values():
                # 计算购物车的总数量
                cart_num += int(cart)

        context['cart_num'] = cart_num

        return render(request, 'list.html', context)
