from django.urls import re_path
from order.views import OrderPlaceView, OrderCommitView, OrderPayView, CheckPayView, CommentView

urlpatterns = [
    re_path(r'^place$', OrderPlaceView.as_view(), name='place'),  # 提交订单页面显示
    re_path(r'^commit$', OrderCommitView.as_view(), name='commit'),  # 提交订单
    re_path(r'^pay$', OrderPayView.as_view(), name='pay'),  # 订单支付
    re_path(r'^check$', CheckPayView.as_view(), name='check'),  # 查询支付交易结果
    re_path(r'^comment/(?P<order_id>.+)$', CommentView.as_view(), name='comment'),  # 订单评论
]
