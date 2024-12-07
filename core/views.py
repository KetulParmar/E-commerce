from django.contrib.auth.decorators import login_required
from django.http import HttpResponse, JsonResponse
from django.shortcuts import render, redirect, get_object_or_404
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST

from .forms import ProductForm
from .models import Product, Order, OrderItem
from django.utils import timezone
from django.contrib import messages
from .forms import CheckoutForm
from .models import CheckoutAddress
import razorpay
from django.conf import settings
import json
from django.urls import reverse

razorpay_client = razorpay.Client(auth=(settings.RAZORPAY_ID, settings.RAZORPAY_SECRET))


def index(request):
    products = Product.objects.all()
    return render(request, 'core/index.html', {'products': products})


def orderlist(request):
    if Order.objects.filter(user=request.user, ordered=False).exists():
        order = Order.objects.get(user=request.user, ordered=False)
        order_items = order.items.all()  # assuming Order model has a related name 'items' for OrderItem
        print(f"Total Order Price: {order.get_total_price()}")  # Debugging print
        return render(request, 'core/orderlist.html', {'order': order, 'order_items': order_items})
    return render(request, 'core/orderlist.html', {'order_items': [], 'message': "Your cart is empty"})


def add_product(request):
    if request.method == 'POST':
        form = ProductForm(request.POST, request.FILES)
        if form.is_valid():
            form.save()
            messages.success(request, "Product added successfully")
            return redirect('/')
        else:
            messages.info(request, "Product is not added!! Try again.")
    else:
        form = ProductForm()
    return render(request, 'core/add_product.html', {'form': form})


def product_desc(request, pk):
    product = get_object_or_404(Product, pk=pk)
    return render(request, 'core/product_desc.html', {'product': product})


def add_to_cart(request, pk):
    product = get_object_or_404(Product, pk=pk)
    order_item, created = OrderItem.objects.get_or_create(
        product=product,
        user=request.user,
        ordered=False,
    )
    order_qs = Order.objects.filter(user=request.user, ordered=False)
    if order_qs.exists():
        order = order_qs[0]
        if order.items.filter(product__pk=pk).exists():
            order_item.quantity += 1
            order_item.save()
            messages.info(request, "Added quantity of the item")
            return redirect("core:product_desc", pk=pk)
        else:
            order.items.add(order_item)
            messages.info(request, "Item added to cart")
            return redirect("core:product_desc", pk=pk)
    else:
        ordered_date = timezone.now()
        order = Order.objects.create(user=request.user, ordered_date=ordered_date)
        order.items.add(order_item)
        order.save()  # Ensure order_id is set
        messages.info(request, "Item added to cart")
    return redirect('core:product_desc', pk=pk)


def add_item(request, pk):
    product = Product.objects.get(pk=pk)

    order_item, create = OrderItem.objects.get_or_create(
        product=product,
        user=request.user,
        ordered=False,
    )

    order_qs = Order.objects.filter(user=request.user, ordered=False)
    if order_qs.exists():
        order = order_qs[0]
        if order.items.filter(product__pk=pk).exists():
            if order_item.quantity < product.product_available_count:
                order_item.quantity += 1
                order_item.save()
                messages.info(request, "Added quantity item")
                return redirect("core:orderlist")
            else:
                messages.info(request, "Sorry! product is out of stock")
                return redirect("core:orderlist")
        else:
            order.items.add(order_item)
            messages.info(request, "Item added to cart")
            return redirect("core:product_desc", pk=pk)
    else:
        ordered_date = timezone.now()
        order = Order.objects.create(user=request.user, ordered_date=ordered_date)
        order.items.add(order_item)
        order.save()  # Ensure order_id is set
        messages.info(request, "Item added to cart")
    return redirect('core:product_desc', pk=pk)


def remove_item(request, pk):
    item = get_object_or_404(Product, pk=pk)
    order_qs = Order.objects.filter(
        user=request.user,
        ordered=False,
    )
    if order_qs.exists():
        order = order_qs[0]
        if order.items.filter(product__pk=pk).exists():
            order_item = OrderItem.objects.filter(
                product=item,
                user=request.user,
                ordered=False,
            )[0]
            if order_item.quantity > 1:
                order_item.quantity -= 1
                order_item.save()
            else:
                order_item.delete()
            messages.info(request, "Item quantity was updated")
            return redirect("core:orderlist")
        else:
            messages.info(request, "this item is not in your cart")
            return redirect("core:orderlist")
    else:
        messages.info(request, "You Do not have any order")
        return redirect("core:orderlist")


def checkout_page(request):
    if CheckoutAddress.objects.filter(user=request.user).exists():
        return render(request, 'core/checkout_address.html', {'payment_allow': 'allow'})

    if request.method == 'POST':
        print("saving must start")
        form = CheckoutForm(request.POST)
        if form.is_valid():
            street_address = form.cleaned_data.get('street_address')
            apartment_address = form.cleaned_data.get('apartment_address')
            country = form.cleaned_data.get('country')
            zip_code = form.cleaned_data.get('zip')

            checkout_address = CheckoutAddress(
                user=request.user,
                street_address=street_address,
                apartment_address=apartment_address,
                country=country,
                zip_code=zip_code,
            )
            checkout_address.save()
            print("It should render the summary page")
            return render(request, 'core/checkout_address.html', {'payment_allow': 'allow'})


    else:
        form = CheckoutForm()
        return render(request, 'core/checkout_address.html', {'form': form})


def payment(request):
    try:
        order = Order.objects.get(user=request.user, ordered=False)
        address = CheckoutAddress.objects.get(user=request.user)
        order_amount = order.get_total_price()
        order_currency = "INR"
        order_receipt = order.order_id
        notes = {
            "street_address": address.street_address,
            "apartment_address": address.apartment_address,
            "country": address.country.name,
            "zip": address.zip_code,
        }
        razorpay_order = razorpay_client.order.create(
            dict(
                amount=order_amount * 100,
                currency=order_currency,
                receipt=order_receipt,
                notes=notes,
                payment_capture="0",
            )
        )
        print(razorpay_order["id"])
        order.razorpay_order_id = razorpay_order["id"]
        order.save()
        print("It should render the summary page")
        return render(
            request,
            "core/paymentsummaryrazorpay.html",
            {
                "order": order,
                "order_id": razorpay_order["id"],
                "orderID": order.order_id,
                "final_price": order_amount,
                "razorpay_merchant_id": settings.RAZORPAY_ID,
            },
        )
    except Order.DoesNotExist:
        print("Order Not Found")
        return HttpResponse("404 Error")
    except Exception as e:
        print(f"Error in payment creation: {e}")
        return HttpResponse("Error Occurred")


@csrf_exempt
def handlerequest(request):
    if request.method == "POST":
        try:
            # Parse the JSON response
            data = json.loads(request.body.decode('utf-8'))
            payment_id = data.get("razorpay_payment_id")
            order_id = data.get("razorpay_order_id")
            signature = data.get("razorpay_signature")

            print(payment_id, order_id, signature)

            params_dict = {
                "razorpay_order_id": order_id,
                "razorpay_payment_id": payment_id,
                "razorpay_signature": signature,
            }

            try:
                order_db = Order.objects.get(razorpay_order_id=order_id)
                print("Order Found")
            except Order.DoesNotExist:
                print("Order Not Found")
                return JsonResponse({"success": False, "error": "Order Not Found"}, status=404)

            order_db.razorpay_payment_id = payment_id
            order_db.razorpay_signature = signature
            order_db.save()

            print("Verifying signature...")
            result = razorpay_client.utility.verify_payment_signature(params_dict)

            if result is None:
                print("Signature verified.")
                amount = order_db.get_total_price()
                amount = amount * 100  # amount in paise

                payment_status = razorpay_client.payment.capture(payment_id, amount)

                if payment_status['status'] == 'captured':
                    print("Payment captured successfully.")
                    order_db.ordered = True
                    order_db.save()
                    checkout_address = CheckoutAddress.objects.get(user=request.user)
                    request.session[
                        'order_complete'] = "Your Order is Successfully Placed, You will receive your order soon!"
                    return render(request, "core/invoice.html", {
                        'order': order_db,
                        "payment_status": payment_status,
                        "checkout_address": checkout_address
                    })
                else:
                    print("Payment capture failed.")
                    order_db.ordered = False
                    order_db.save()
                    request.session['order_failed'] = "Unfortunately your order could not be placed, try again!"
                    return redirect(reverse('paymentfailed'))
            else:
                print("Signature verification failed.")
                order_db.ordered = False
                order_db.save()
                return redirect(reverse('paymentfailed'))
        except Exception as e:
            print(f"Error in handle request: {e}")
            return JsonResponse({"success": False, "error": str(e)}, status=500)
    else:
        return HttpResponse("Invalid request method", status=400)


@login_required
def invoice(request):
    try:
        order = Order.objects.get(user=request.user, ordered=True)
        checkout_address = CheckoutAddress.objects.get(user=request.user)

        context = {
            'order': order,
            'checkout_address': checkout_address,
        }

        return render(request, 'core/invoice.html', context)

    except Order.DoesNotExist:
        messages.error(request, "No completed order found for the current user.")
        return redirect('core:index')

    except CheckoutAddress.DoesNotExist:
        messages.error(request, "No checkout address found for the current user.")
        return redirect('core:index')

    except Exception as e:
        messages.error(request, f"An error occurred: {str(e)}")
        return redirect('core:index')


def payment_failed(request):
    return render(request, 'core/paymentfailed.html')


from django.db.models import Sum, F


def generate_report(request):
    # Total number of orders
    total_orders = Order.objects.filter(ordered=True).count()

    # Total revenue
    total_revenue = 0
    for order_item in OrderItem.objects.filter(order__ordered=True):
        total_revenue += order_item.get_total_item_price()

    # Total items sold
    total_items_sold = 0
    for order_item in OrderItem.objects.filter(order__ordered=True):
        total_items_sold += order_item.quantity
    print("total_revenue:", total_revenue)
    context = {
        'total_orders': total_orders,
        'total_revenue': total_revenue,
        'total_items_sold': total_items_sold,
    }

    return render(request, 'core/generate_report.html', context)


from django.db import transaction

from django.contrib.auth.decorators import login_required

@login_required
@require_POST
@transaction.atomic
def cash_on_delivery(request):
    try:
        order_qs = Order.objects.filter(user=request.user, ordered=False)
        if not order_qs.exists():
            messages.error(request, "No active order found.")
            return redirect('core:index')

        order = order_qs[0]
        order.ordered = True
        order.payment_method = 'COD'
        order.ordered_date = timezone.now()
        order.save()

        # Redirect to the invoice page after successfully placing the order
        return redirect('core:invoice')
    except Exception as e:
        print(f"Error creating COD order: {e}")
        messages.error(request, 'An error occurred while placing your order. Please try again later.')
        return redirect('core:index')


def daily_orders_report(request):
    today = timezone.now().date()
    today_orders = Order.objects.filter(ordered=True, ordered_date__date=today)

    context = {
        'today': today,
        'today_orders': today_orders,
    }
    return render(request, 'core/daily_orders_report.html', context)
