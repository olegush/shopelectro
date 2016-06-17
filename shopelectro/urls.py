"""
shopelectro.ru urlconf.

NOTE: it's better to group related sets of urls into
distinct lists and then include them all at once.
"""

from django.contrib import admin
from django.conf.urls import url, include
from . import views


category_urls = [
    url(r'^(?P<category_slug>[\w-]+)/$',
        views.category_page, name='category'),
    url(r'^(?P<category_slug>[\w-]+)/(?P<sorting>[0-9]*)/$',
        views.category_page, name='category'),
    url(r'^(?P<category_slug>[\w-]+)/load-more/(?P<offset>[0-9]+)/(?P<sorting>[0-9]*)/$',
        views.load_more, name='load_more'),
]

shop_urls = [
    url(r'^cart-add/$', views.add_to_cart),
    url(r'^cart-change/$', views.change_count_in_cart),
    url(r'^cart-flush/$', views.cart_flush),
    url(r'^cart-remove/$', views.cart_remove),
    url(r'^one-click-buy/$', views.one_click_buy),
    url(r'^success-order/$', views.success_order, name='order_success'),
    url(r'^order-call/$', views.order_call),
    url(r'^order/$', views.order_page, name='order_page'),
]

urlpatterns = [
    url(r'^$', views.index, name='index'),
    url(r'^admin/', admin.site.urls),
    url(r'^admin-autocomplete/', views.admin_autocomplete),
    url(r'^set-view-type/$', views.set_view_type, name='set_view_type'),
    url(r'^catalog/categories/', include(category_urls)),
    url(r'^catalog/products/(?P<product_id>[0-9]+)/$', views.product_page, name='product'),
    url(r'^catalog/', include('catalog.urls')),
    url(r'^blog/posts/(?P<type_>[\w-]+)/$', views.blog_post, name='posts'),
    url(r'^blog/', include('blog.urls')),
    url(r'^shop/', include(shop_urls))
]
