from django.db import models
from db.base_model import BaseModel


# Create your models here.


class OrderInfo(BaseModel):
    '''订单模型类'''
    PAY_METHODS = {
        '1': '货到付款',
        '2': '微信支付',
        '3': '支付宝',
        '4': '银联支付',
    }

    PAY_METHOD_CHOICES = (
        (1, '货到付款'),
        (2, '微信支付'),
        (3, '支付宝'),
        (4, '银联支付'),
    )
    ORDER_STATUS = {
        1: '待支付',
        2: '代发货',
        3: '待收货',
        4: '待评价',
        5: '已完成',
    }
    ORDER_STATUS_CHOICES = (
        (1, '待支付'),
        (2, '代发货'),
        (3, '待收货'),
        (4, '待评价'),
        (5, '已完成'),
    )
    order_id = models.CharField(max_length=128, primary_key=True, verbose_name='订单id')
    user = models.ForeignKey('user.User', verbose_name='用户', on_delete=models.CASCADE)
    addr = models.ForeignKey('user.Address', verbose_name='地址', on_delete=models.CASCADE)
    pay_method = models.SmallIntegerField(default=3, choices=PAY_METHOD_CHOICES, verbose_name='支付方式')
    total_count = models.IntegerField(default=1, verbose_name='商品数量')
    total_price = models.DecimalField(max_digits=10, decimal_places=2, verbose_name='商品总价')
    transit_price = models.DecimalField(max_digits=10, decimal_places=2, verbose_name='订单运费')
    order_status = models.SmallIntegerField(default=1, choices=ORDER_STATUS_CHOICES, verbose_name='商品库存')
    trade_no = models.CharField(max_length=128, default='', verbose_name='支付id')

    class Meta:
        db_table = 'df_order_info'


class OrderGoods(BaseModel):
    '''订单商品模型类'''
    order = models.ForeignKey('OrderInfo', verbose_name='订单', on_delete=models.CASCADE)
    sku = models.ForeignKey('goods.GoodsSKU', verbose_name='商品SKU', on_delete=models.CASCADE)
    count = models.IntegerField(default=1, verbose_name='商品数量')
    price = models.DecimalField(max_digits=10, decimal_places=2, verbose_name='商品单价')
    comment = models.CharField(max_length=256, default='', verbose_name='评论')

    class Meta:
        db_table = 'df_order_goods'
