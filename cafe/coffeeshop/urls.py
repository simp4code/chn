from django.urls import path
from . import views

urlpatterns = [
    path('', views.index, name='index'),
    path('c', views.add_to_cart, name='add_to_cart'),
    path('c/vc', views.view_cart, name='view_cart'),
    path('ck', views.checkout, name='checkout'),
    path('a', views.display_admin, name='admin'),
    path('a/q',views.queue_screen, name='queue'),
    path('get_orders/', views.get_orders, name='get_orders'),
    path('update_status/', views.update_status, name='update_status'),
    path('a/qrcs', views.qrs, name='qrs'),
    path('a/qrcs/v', views.verify, name='verify'),
    path('a/vo', views.verified_orders, name='verified_orders'),
    #path('/qr', views.download_qr_code, name='download_qr_code'),
    path('a/ap', views.add_product, name='add'),
    path('a/u/<int:pk>/', views.update_product, name='update'),
    path('a/d/<int:pk>/', views.delete_product, name='delete'),
    path('xc',views.clear_cart,name='clear_cart'),
    path('download-receipt/<int:order_id>/', views.download_receipt, name='download_receipt'),
]