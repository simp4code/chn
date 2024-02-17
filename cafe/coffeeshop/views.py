from django.http import HttpResponse, HttpResponseRedirect
from django.template.response import TemplateResponse
from django.template import loader
from .models import Product,Cart,QRCodeData, Orders
from .forms import FileForm, VerificationForm
from django.shortcuts import render, redirect
from django.shortcuts import get_object_or_404
from django.contrib import messages
import logging
import os
from django.core.serializers import serialize
from django.http import JsonResponse
from io import BytesIO
import json
import qrcode
import random
import base64
from django.shortcuts import render
from django.db.utils import IntegrityError
from django.db import transaction
import json
from django.http import JsonResponse
import datetime
from django.shortcuts import get_object_or_404
from django.http import HttpResponse
from io import BytesIO
from PIL import Image, ImageDraw, ImageFont
from django.template.loader import render_to_string

def generate_receipt_image(order):
    try:
        # Render receipt HTML template with order details
        receipt_html = render_to_string('receipt.html', {'order': order})

        # Create a blank image
        width, height = 600, 800
        image = Image.new('RGB', (width, height), color='white')
        draw = ImageDraw.Draw(image)

        # Load a font
        font = ImageFont.truetype("arial.ttf", 20)

        # Draw the receipt HTML text on the image
        draw.text((50, 50), receipt_html, fill='black', font=font)

        return image
    except Exception as e:
        # Log or handle the exception appropriately
        raise RuntimeError(f"Error generating receipt image: {e}")

def download_receipt(request, order_id):
    try:
        # Retrieve order details
        order = get_object_or_404(Orders, id=order_id)

        # Generate receipt image
        receipt_image = generate_receipt_image(order)

        # Convert image to bytes
        image_bytes = BytesIO()
        receipt_image.save(image_bytes, format='PNG')
        image_bytes.seek(0)

        # Return the receipt as a downloadable file
        response = HttpResponse(image_bytes, content_type='image/png')
        response['Content-Disposition'] = f'attachment; filename="receipt_{order_id}.png"'
        return response
    except Exception as e:
        # Log or handle the exception appropriately
        return HttpResponse(f"Error downloading receipt: {e}", status=500)


def update_status(request):
    if request.method == 'POST':
        order_id = request.POST.get('order_id')
        if order_id:
            try:
                order = Orders.objects.get(pk=order_id)
                order.status = 'serving'  
                order.save()
                messages.success(request, f"Order {order_id} status updated to serving.")
            except Orders.DoesNotExist:
                messages.error(request, f"Order with ID {order_id} does not exist.")
        else:
            messages.error(request, "Order ID not provided.")
        return redirect('verified_orders') 
    else:
        messages.error(request, "Invalid request method.")
        return redirect('verified_orders') 


def get_orders(request):
    preparing_orders = Orders.objects.filter(status='preparing').values('order_number')
    serving_orders = Orders.objects.filter(status='serving').values('order_number')
    data = {
        'preparing_orders': list(preparing_orders),
        'serving_orders': list(serving_orders)
    }
    return JsonResponse(data)

def queue_screen(request):
    preparing_orders = Orders.objects.filter(status='preparing')
    serving_orders = Orders.objects.filter(status='serving')
    context = {
        'preparing_orders': preparing_orders,
        'serving_orders': serving_orders
    }
    return render(request, 'queue.html', context)

def extract_latest_created_at(order):
    # Initialize the latest date as a fallback
    latest_date = datetime.datetime.min
    
    # Iterate over each item in the cart_items list
    for item in order.cart_items:
        # Assuming each item is a dictionary and has a 'created_at' key
        if 'created_at' in item:
            item_created_at = item['created_at']
            # Compare with the current latest date
            if item_created_at > latest_date:
                latest_date = item_created_at
    
    return latest_date

def verified_orders(request):
    orders = Orders.objects.all().order_by('id')  # Order queryset by ID
    context = {
        'orders': orders,
    }
    return render(request, 'orders.html', context)
    
def verify(request):
    if request.method == 'POST':
        form = VerificationForm(request.POST)
        if form.is_valid():
            verification_code = form.cleaned_data['verification_code']
            try:
                qr_code_data = QRCodeData.objects.get(verification_code=verification_code)
                if not qr_code_data.verified:
                    with transaction.atomic():
                        qr_code_data.verified = True
                        qr_code_data.save()
                        # Create an order if verified and move data to Orders model
                        order = Orders.objects.create(
                            cart_items=qr_code_data.cart_items,
                            total_price=qr_code_data.total_price,
                            verification_code=qr_code_data.verification_code
                        )
                        print('Order saved')
                        order.save()
                    messages.success(request, 'QR code verified successfully and order created.')
                    return redirect('verified_orders')
                else:
                    messages.error(request, 'QR code is already verified.')
            except QRCodeData.DoesNotExist:
                messages.error(request, 'Invalid verification code.')
            except IntegrityError as e:
                messages.error(request, f'Error saving order: {e}')
    else:
        form = VerificationForm()
    qr = QRCodeData.objects.all()
    context={
                'qr_code_data':qr,
                'form':form
            }
    return render(request, 'qrcodes.html', context)

def qrs(request):
    qr = QRCodeData.objects.all()
    context={
        'qr_code_data':qr,
    }
    return render(request, 'qrcodes.html',context)

def checkout(request):
    cart_items = Cart.objects.all()
    total_price = sum(item.total_price() for item in cart_items)

    # Generate random 9-letter code
    code = ''.join(random.choices('ABCDEFGHIJKLMNOPQRSTUVWXYZ', k=3)) + \
           ' ' + ''.join(random.choices('0123456789', k=3)) + \
           ' ' + ''.join(random.choices('ABCDEFGHIJKLMNOPQRSTUVWXYZ', k=3))

    # Serialize cart items
    cart_items_json = serialize('json', cart_items)

    # Combine cart items JSON and total price into a dictionary
    data = {
        'cart_items': cart_items_json,
        'total_price': total_price,
        'verification_code': code
    }

    qr_code_data = QRCodeData.objects.create(
    cart_items=data['cart_items'],
    total_price=data['total_price'],
    verification_code=data['verification_code'],
    verified=False 
    )

    # Generate QR code
    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_L,
        box_size=10,
        border=4,
    )
    qr.add_data(str(data))
    qr.make(fit=True)
    img = qr.make_image(fill_color="black", back_color="white")

    # Save QR code to BytesIO
    buffer = BytesIO()
    img.save(buffer, format="PNG")
    img_str = base64.b64encode(buffer.getvalue()).decode('utf-8')

    # Pass data to template
    context = {
        'qr_code': img_str,
        'verification_code': code,
    }

    # Render the template with data
    return render(request, 'qrcode.html', context)





def index(request):
    coffees = Product.objects.all()
    return render(request, 'index.html', {'coffees': coffees})



def display_admin(request):
  pdf_list = Product.objects.all().values() 
  file_count = len(pdf_list)
  template = loader.get_template('admin.html')
  context = {
        'products': pdf_list,
        'file_count':file_count,
  }
  return HttpResponse(template.render(context, request))

logger = logging.getLogger(__name__)




def add_to_cart(request):
    if request.method == 'POST':
        try:
            product_id = request.POST.get('id')
            quantity = int(request.POST.get('quantity', 1))
            coffee = Product.objects.get(pk=product_id)

            # Check if the item is already in the cart
            cart_item, created = Cart.objects.get_or_create(product=coffee)

            # If the item already exists, update the quantity
            if not created:
                cart_item.quantity += quantity
                cart_item.save()
            else:
                cart_item.quantity = quantity
                cart_item.save()

            messages.success(request, 'Item added to cart successfully.')
        except Product.DoesNotExist:
            messages.error(request, 'Product does not exist')
        except Exception as e:
            messages.error(request, f'Error adding item to cart: {e}')

    return redirect('index')

def view_cart(request):
    cart_items = Cart.objects.all()
    total_price = sum(item.total_price() for item in cart_items)
    return render(request, 'cart.html', {'cart_items': cart_items, 'total_price': total_price})
   
def add_product(request):
    if request.method == 'POST':
        product_image = request.FILES.get('img')
        product_name = request.POST.get('n')
        product_price = request.POST.get('p')
        product_quantity = request.POST.get('q')

        Product.objects.create(
            img=product_image,
            name=product_name,
            price=product_price,
            quantity=product_quantity
        )
        return redirect('admin') 

    return render(request, 'add_product.html')

def update_product(request, pk):
    obj = get_object_or_404(Product, pk=pk)

    if request.method == 'POST':
        obj.img = request.FILES.get('img')
        obj.name = request.POST.get('n')
        obj.price = request.POST.get('p')
        obj.quantity = request.FILES.get('q')

        obj.save()
        return redirect('admin') 

    return render(request, 'update_product.html', {'obj': obj})

def delete_product(request, pk):
    obj = get_object_or_404(Product, pk=pk)

    if request.method == 'POST':
        obj.delete()
        return redirect('admin')

    return render(request, 'delete_product.html', {'obj': obj})

def clear_cart(request):
    # Clear the cart
    Cart.objects.all().delete()

    # Render the splash screen template
    return redirect('index')