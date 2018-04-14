from django.core.cache import cache
from django.shortcuts import render

# Create your views here.
from django.template import loader
from django.views.generic import View

from goods.models import GoodsCategory, IndexGoodsBanner, \
    IndexPromotionBanner, IndexCategoryGoodsBanner


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

        return render(request, 'index.html', context)
