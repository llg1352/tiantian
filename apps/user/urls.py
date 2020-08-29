from django.urls import re_path
# from user import views
from user.views import RegisterView, ActiveView, LoginView, UserInfoView, UserOrderView, AddressView, LogoutView
from django.contrib.auth.decorators import login_required
urlpatterns = [
    # re_path(r'^register$', views.register, name='register'), #注册页面
    # re_path(r'^register_handle$', views.register_handle, name='register_handle')  # 注册处理
    re_path(r'^register$', RegisterView.as_view(), name='register'),  # 注册页面
    re_path(r'^active/(?P<token>.*)$', ActiveView.as_view(), name='active'),  # 激活页面
    re_path(r'^login$', LoginView.as_view(), name='login'),  # 登录页面
    re_path(r'^logout$', LogoutView.as_view(), name='logout'),  # 注销登录
    re_path(r'^$', UserInfoView.as_view(), name='user'),  # 用户中心-信息页
    re_path(r'^order/(?P<page>\d+)$', UserOrderView.as_view(), name='order'),  # 用户中心-订单页
    re_path(r'^address$', AddressView.as_view(), name='address'),  # 用户中心-详情页
]
