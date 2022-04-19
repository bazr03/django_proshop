from django.urls import path
from base.views import product_views as views



urlpatterns = [
    path('', views.getProducts, name='products'),
    path('create/', views.createProduct, name='product-create'),
    path('upload/', views.uploadImage, name='image-upload'),
    path('top/', views.getTopProducts, name='top-products'),
    path('image/delete/', views.deleteImage, name='delete-image'),
    path('image/setMain/', views.setMainImage, name='set-main-image'),
    path('<str:pk>/reviews/create/', views.createProductReview, name='create-review'),
    path('<str:pk>/reviews/', views.getProductReviews, name='product-reviews'),
    path('<str:pk>/', views.getProduct, name='product'),
    path('update/<str:pk>/', views.updateProduct, name='product-update'),
    path('delete/<str:pk>/', views.deleteProduct, name='product-delete'),
]