from datetime import datetime
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework.permissions import  IsAuthenticated, IsAdminUser
from ..serializer import   OrderSerializer
from ..models import Product, Order, OrderItem, ShippingAddress
from django.shortcuts import get_object_or_404
import decimal

# from datetime import  timezone

from rest_framework import  status

def calcSubtotal(items):
    # products = [Product.objects.get(_id=item['product'].get('_id')) for item in items]
    subtotal = 0
    for item in items:
        product = Product.objects.get(_id=item['product'].get('_id'))
        qty= item['qty']
        subtotal += product.price*qty

    return subtotal
    
def calcTaxPrice(subtotal):
    taxPrice = decimal.Decimal('0.082') * subtotal
    return round(taxPrice,2)

def calcShippingPrice(subtotal):
    if subtotal > 100:
        return 0
    else:
        return 10

def calcTotalPrice(subtotal,taxPrice, shippingPrice):
    total = subtotal + taxPrice + shippingPrice
    return round(total,2)



@api_view(['POST'])
@permission_classes([IsAuthenticated])
def addOrderItems(request):
    user = request.user
    data = request.data


    orderItems = data['orderItems']

    if orderItems and len(orderItems) == 0:
        return Response({'message':'No Items in the Order!'}, status=status.HTTP_400_BAD_REQUEST)
    
    # Create order
    subTotal = calcSubtotal(orderItems)
    taxPrice = calcTaxPrice(subTotal)
    shippingPrice= calcShippingPrice(subTotal)
    totalPrice= calcTotalPrice(subTotal,taxPrice, shippingPrice)

    order = Order.objects.create(
        user=user,
        paymentMethod=data['paymentMethod'],
        subTotal=subTotal,
        taxPrice=taxPrice,
        shippingPrice=shippingPrice,
        totalPrice=totalPrice,
    )
    # Create Shipping address
    shipping = ShippingAddress.objects.create(
        order=order,
        adress=data['shippingAddress'].get('address'),
        city=data['shippingAddress'].get('city'),
        postalCode=data['shippingAddress'].get('postalCode'),
        country=data['shippingAddress'].get('country'),
        shippingPrice=shippingPrice
    )
    # Create order items and set order to orderItem relationship
    for item in orderItems:
        pk = item['product'].get('_id')
        # product = Product.objects.get(_id=item['product'].get('_id'))
        product = get_object_or_404(Product,pk=int(pk))

        newItem = OrderItem.objects.create(
            product=product,
            order=order,
            name=product.name,
            qty=item['qty'],
            price=product.price,
            image=product.mainImageUrl,
        )
        # update stock
        product.countInStock -= newItem.qty
        product.save(update_fields=['countInStock'])

    serializer = OrderSerializer(order, many=False)
    return Response(serializer.data)

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def getOrderById(request, pk):
    user = request.user
    order = get_object_or_404(Order,pk=int(pk))

    if user.is_staff or (order.user == user): 
        serializer = OrderSerializer(order, many=False)
        return Response(serializer.data)
    else:
        return Response({'message':'Not authorized'}, status=status.HTTP_401_UNAUTHORIZED)


@api_view(['PUT'])
@permission_classes([IsAuthenticated])
def getTotalPrice(request):
    orderItems = request.data

    if orderItems and len(orderItems) == 0:
        return Response({'message':'No Order Items'}, status=status.HTTP_400_BAD_REQUEST)

    subTotal = calcSubtotal(orderItems)
    taxPrice = calcTaxPrice(subTotal)
    shippingPrice= calcShippingPrice(subTotal)
    totalPrice= calcTotalPrice(subTotal,taxPrice, shippingPrice)

    return Response({'subTotal': subTotal, 'taxPrice':taxPrice, 'shippingPrice':shippingPrice, 'totalPrice':totalPrice}, status=status.HTTP_200_OK)

@api_view(['PUT'])
@permission_classes([IsAuthenticated])
def updateOrderToPaid(request, pk):
    order = get_object_or_404(Order,pk=int(pk))
    order.isPaid = True
    order.paidAt = datetime.now()
    order.save(update_fields=['isPaid','paidAt'])

    return Response({
        'message':'Order was paid',
        'paidAt':datetime.now()
    }, status=status.HTTP_202_ACCEPTED)

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def getUserOrders(request):
    user = request.user
    orders = user.order_set.all()
    serializer = OrderSerializer(orders, many=True)

    return Response(serializer.data)

@api_view(['GET'])
@permission_classes([IsAdminUser])
def getOrders(request):
    orders = Order.objects.all()
    serializer = OrderSerializer(orders, many=True)

    return Response(serializer.data)


@api_view(['PUT'])
@permission_classes([IsAdminUser])
def updateOrderToDelivered(request, pk):
    order = get_object_or_404(Order,pk=int(pk))

    order.isDelivered = True
    order.deleveredAt = datetime.now()
    order.save(update_fields=['isDelivered','deleveredAt'])

    return Response({
        'message': 'Order delivered',
        'deliveredAt': order.deleveredAt
    }, status=status.HTTP_202_ACCEPTED)