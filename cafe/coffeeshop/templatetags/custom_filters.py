from django import template
import json
from coffeeshop.models import Product

register = template.Library()

@register.filter
def decode_cart_items(cart_items_json):
    cart_items = json.loads(cart_items_json)
    decoded_items = []
    for item in cart_items:
        product_id = item['fields']['product']
        product = Product.objects.get(id=product_id)
        decoded_item = f"{product.name} (Quantity: {item['fields']['quantity']})"
        decoded_items.append(decoded_item)
    return decoded_items
