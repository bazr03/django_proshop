from django.urls import path
from ..views import order_views as views

urlpatterns = [
    path('', views.getOrders, name='orders'),
    path('add/', views.addOrderItems, name='orders-add'),
    path('myorders/', views.getUserOrders, name='user-orders'),
    path('totalPrice/', views.getTotalPrice, name='orders-totalPrice'),
    path('<str:pk>/deliver/', views.updateOrderToDelivered, name='order-deliver'),
    path('<str:pk>/pay', views.updateOrderToPaid, name='pay-order'),
    path('<str:pk>/', views.getOrderById, name='user-order'),
]