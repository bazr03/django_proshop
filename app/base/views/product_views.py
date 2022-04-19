
from datetime import datetime
from pickletools import optimize
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated, IsAdminUser
from rest_framework.response import Response
from django.shortcuts import get_object_or_404
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
import cloudinary.uploader
from rest_framework import status
from io import BytesIO
from ..models import Product, Image, Review
from ..serializer import ProductSerializer, ReviewSerializer
from ..utils.image_resize import image_resize, is_valid_image


MAX_IMAGE_SIZE = 1024*1024*4 # 4MB

@api_view(['GET'])
def getProducts(request):
    query = request.query_params.get('keyword')
    if query == None:
        query = ''

    products = Product.objects.filter(name__icontains=query).order_by('_id')

    page = request.query_params.get('page')
    pageSize = request.query_params.get('pageSize')
    
    if page == None:
        page = 1

    if pageSize == None or int(pageSize) > 10:
        pageSize = 4

    page = int(page)
    pageSize = int(pageSize)
    paginator = Paginator(products, pageSize)

    try:
        products = paginator.page(page)
    except PageNotAnInteger:
        products = paginator.page(1)
    except EmptyPage:
        products = paginator.page(paginator.num_pages)

    
    # products = Product.objects.all()
    serializer = ProductSerializer(products, many=True)
    # print(serializer.data)
    return Response({'products':serializer.data, 'page':page, 'pages':paginator.num_pages, 'pageSize':pageSize})


@api_view(['GET'])
def getTopProducts(request):
    products = Product.objects.filter(rating__gte=4).order_by('-rating')[0:5]
    serializer = ProductSerializer(products, many=True)
    return Response(serializer.data)

@api_view(['GET'])
def getProduct(request, pk):
    product = get_object_or_404(Product,pk=int(pk))
    serializer = ProductSerializer(product, many=False)
    return Response(serializer.data)

@api_view(['POST'])
@permission_classes([IsAdminUser])
def createProduct(request):
    user = request.user
    data = request.data

    product = Product.objects.create(
        user=user,
        name=data['name'],
        price=data['price'],
        brand=data['brand'],
        countInStock=data['countInStock'],
        category=data['category'],
        description=data['description']
    )

    serializer = ProductSerializer(product, many=False)
    return Response(serializer.data)


@api_view(['PUT'])
@permission_classes([IsAdminUser])
def updateProduct(request, pk):
    data = request.data
    product = get_object_or_404(Product,pk=int(pk))

    product.name = data['name']
    product.price = data['price']
    product.brand = data['brand']
    product.countInStock = data['countInStock']
    product.category = data['category']
    product.description = data['description']

    product.save()
    serializer = ProductSerializer(product, many=False)
    return Response(serializer.data)


@api_view(['DELETE'])
@permission_classes([IsAdminUser])
def deleteProduct(request, pk):
    product = get_object_or_404(Product,pk=int(pk))
    product.delete()
    return Response('Product deleted')


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def uploadImage(request):
    data = request.data

    product_id = data['product_id']
    # product = Product.objects.get(_id=product_id)
    product = get_object_or_404(Product,pk=int(product_id))
    files = request.FILES.getlist('images')

    if not files:
        return Response({
            'status': 'error',
            'message':'No images sended!'
        }, status=status.HTTP_400_BAD_REQUEST)

    for file in files:
        is_image_valid = is_valid_image(file)
        if not is_image_valid:
            return Response({
                'message':'Not a valid image'
                }, status=status.HTTP_400_BAD_REQUEST)

    imageUrls = []
    for file in files:
        # incoming transformations
        resized_img = image_resize(file)
        image_io = BytesIO()
        resized_img.save(image_io, format='JPEG', optimize=True, quality=70)

        #upload_data = cloudinary.uploader.upload(file, height=900,crop="limit")

        upload_data = cloudinary.uploader.upload(image_io.getvalue())

        image = Image.objects.create(
            product_id=product._id,
            url=upload_data['secure_url'],
            publicId=upload_data['public_id']
        )

        image.save()

        if not product.mainImageUrl:
            product.mainImageUrl = image.url
            image.isMain = True
            image.save(update_fields=['isMain'])
            product.save(update_fields=['mainImageUrl'])

        imageUrls.append({'url':image.url, 'public_id':image.publicId, '_id':image._id, 'isMain':image.isMain})

    return Response({
        'message':'image upload success!',
        'images':imageUrls,
        'mainImageUrl': product.mainImageUrl
    }, status=status.HTTP_201_CREATED)



@api_view(['PUT'])
@permission_classes([IsAuthenticated])
def deleteImage(request):
    data = request.data
    images_to_delete = data['imagesToDelete']

    for image in images_to_delete:
        img = get_object_or_404(Image,pk=int(image['_id']))
        print('img to delete: ', img)
        if not img.isMain:
            # Image.objects.filter(_id=image['_id']).delete()
            img.delete()
            cloudinary.uploader.destroy(image['publicId'],invalidate=True)

    return Response({
        'message': 'images deleted successfully!'
    }, status=status.HTTP_204_NO_CONTENT)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def setMainImage(request):
    data = request.data

    image_id = data['image_id']
    product_id = data['product_id']

    images = Image.objects.filter(product___id=product_id)
    product = Product.objects.filter(_id=product_id)

    if not images:
        return Response({
            'message':'Product images not found!'
        }, status=status.HTTP_404_NOT_FOUND)

    for img in images:
        if img._id == image_id:
            img.isMain = True
            product.update(mainImageUrl=img.url)
        else:
            img.isMain = False
        img.save(update_fields=['isMain'])

    return Response({
        'message': 'image setup as main'
    }, status=status.HTTP_202_ACCEPTED)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def createProductReview(request, pk):

    user = request.user
    data = request.data

    product = get_object_or_404(Product, pk=pk)

    # 1 Review already exists
    #reviewAlreadyExists = Review.objects.filter(product__user=user)
    alreadyExists = product.review_set.filter(user=user).exists()

    if alreadyExists:
        return Response({
            'message':'Product already reviewed by user'
        }, status=status.HTTP_400_BAD_REQUEST)

    # 2 No rating or 0
    rating = int(data.get('rating'))

    if not rating or (rating <= 0 or rating > 5 ):
        return Response({
            'message': 'Valid rating range is between 0 and 5!'
        }, status=status.HTTP_400_BAD_REQUEST)

    # 3 Create review
    review = Review.objects.create(
        user=user,
        product=product,
        name=user.first_name,
        rating=rating,
        comment=data['comment'],
        createdAt=datetime.now()
    )

    reviews = product.review_set.all()
    updatedNumReviews = len(reviews)
    product.numReviews = updatedNumReviews

    total = 0
    for rev in reviews:
        total += rev.rating

    product.rating = total / updatedNumReviews
    product.save(update_fields=['numReviews','rating'])

    serializer = ReviewSerializer(review, many=False)

    return Response({
        'message':'Review Added',
        'product_num_reviews':updatedNumReviews,
        'product_rating':product.rating,
        'review':serializer.data
    }, status=status.HTTP_201_CREATED)


@api_view(['GET'])
def getProductReviews(request, pk):
    product = get_object_or_404(Product, pk=pk)

    reviews = product.review_set.all()

    serializer = ReviewSerializer(reviews, many=True)

    return Response(serializer.data, status=status.HTTP_200_OK)