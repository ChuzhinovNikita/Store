from django.urls import path
from . import views

urlpatterns = [
    path('home/', views.home, name='home'),
    path('product/<int:pk>', views.product, name='product'),
    path('guest_reqister/<int:pk>', views.guest_reqister, name='guest_reqister'),
    path('cart/', views.cart, name='cart'),
    path('create_order/', views.create_order, name='create_order'),
    path('saved_page/', views.saved_page, name='saved_page'),
    path('orders/', views.orders, name='orders'),
    path('order_cancel/<int:pk>', views.order_cancel, name='order_cancel'),
]
