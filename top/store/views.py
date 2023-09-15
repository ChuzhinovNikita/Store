from django.shortcuts import render, redirect
from .models import *
from django.db.models import Q, Count
from .forms import OrderForm, RateForm
from django.contrib.auth.decorators import login_required
from staff.models import CancelRequest


def home(request):
    products = Product.objects.all()
    category = request.GET.get('category')
    brand = request.GET.get('brand')
    slides = SliderImage.objects.all()
    search = request.GET.get('search')
    action = request.GET.get('action')

    products = products.filter(category=category) if category else products
    products = products.filter(brand=brand) if brand else products
    products = products.filter(Q(name__icontains=search) | Q(description__icontains=search)) if search else products

    if action == 'saved':
        saved(request)
        return redirect('store:home')

    amount = show_amount(request)

    return render(request, 'home.html', {'products': products, 'slides': slides, 'amount': amount})


def product(request, pk):
    product_data = Product.objects.get(pk=pk)
    action = request.GET.get('action')
    comments = Review.objects.get(pk=pk)
    filter_by = request.GET.get('value')

    # Отзывы =======================

    form = RateForm(request.POST or None)

    if form.is_valid():
        instance = form.save(commit=False)
        instance.customer = request.user
        instance.product = product_data
        instance.save()
        return redirect('store:product', pk=product_data.pk)

    # =============================================================

    if action:
        saved(request, pk)
        return redirect('store:product', pk=pk)

    amount = show_amount(request)

    return render(request, 'product.html',
                  {'product': product_data, 'form': form, 'amount': amount, 'comments': comments})


def guest_reqister(request, pk):
    token = request.COOKIES['csrftoken']
    guest = Guest.objects.filter(token=token)
    page_home = request.GET.get('page_home')

    if not guest:
        Guest.objects.create(token=token)
        guest = Guest.objects.filter(token=token)

    cart_item = CartItem.objects.filter(product=pk, guest=guest[0] if request.user.is_anonymous else None,
                                        customer=request.user if request.user.is_authenticated else None)
    if not cart_item:
        CartItem.objects.create(
            guest=guest[0] if request.user.is_anonymous else None,
            product=Product.objects.get(pk=pk),
            quantity=1,
            customer=request.user if request.user.is_authenticated else None
        )
    else:
        cart_item[0].quantity += 1
        cart_item[0].save()

    if page_home:
        return redirect('store:home')
    else:
        return redirect('store:product', pk=pk)


def cart(request):
    token = request.COOKIES['csrftoken']
    guest = Guest.objects.filter(token=token)
    action = request.GET.get('action')

    cart_item_pk = request.GET.get('pk')

    if action == 'increment' or action == 'decrement':
        edit_cart(action, cart_item_pk)
        return redirect('store:cart')
    elif action == 'saved':
        saved(request)
        return redirect('store:cart')

    if request.GET.get('chosen_all'):
        items = CartItem.objects.filter(customer=request.user)
        for item in items:
            item.chosen = True
        item.save()
        return redirect('store:cart')

    if request.GET.get('chosen'):
        item = CartItem.objects.get(pk=cart_item_pk)
        item.chosen = True
        item.save()
        return redirect('store:cart')

    if request.GET.get('not_chosen'):
        item = CartItem.objects.get(pk=cart_item_pk)
        item.chosen = False
        item.save()
        return redirect('store:cart')

    if request.GET.get('confirm'):
        CartItem.objects.get(pk=cart_item_pk).delete()
        return redirect('store:cart')

    if request.user.is_authenticated:
        cart_items = CartItem.objects.filter(customer=request.user)

    else:
        cart_items = CartItem.objects.filter(guest=guest[0]) if guest else []

    if action == 'delete':
        pk = request.COOKIES.get('pk')
        CartItem.objects.get(pk=pk).delete()
        return redirect('store:cart')

    if action == 'chosen_all':
        cart_items.update(chosen=True)
    elif action == 'remove_all':
        cart_items.update(chosen=False)
    elif action == 'delete_all':
        cart_items.delete()

    total_quantity = sum([i.quantity for i in cart_items])
    total_sum = sum([i.total_price() for i in cart_items])

    chosen_items = cart_items.filter(chosen=True)

    return render(request, 'cart.html',
                  {'cart_items': cart_items, 'amount': total_quantity,
                   'total_sum': total_sum, 'chosen_items': chosen_items})


def edit_cart(action, pk):
    cart_item = CartItem.objects.get(pk=pk)
    if action == 'increment':
        cart_item.quantity += 1
        cart_item.save()

    if action == 'decrement' and cart_item.quantity > 1:
        cart_item.quantity -= 1
        cart_item.save()


@login_required(login_url='/users/log_in/')
def create_order(request):
    cart_items = CartItem.objects.filter(customer=request.user, chosen=True)

    if sum(item.quantity for item in cart_items) == 0:
        cart_items = CartItem.objects.filter(customer=request.user)

    if not cart_items:
        return render(request, 'error.html', {})

    total_price = sum(item.total_price() for item in cart_items)
    amount = sum(item.quantity for item in cart_items)
    form = OrderForm(request.POST or None)

    if form.is_valid():
        order = Order.objects.create(
            address=request.POST.get('address'),
            phone=request.POST.get('phone'),
            total_price=total_price,
            customer=request.user,
            comment=request.POST.get('comment')
        )
        for item in cart_items:
            OrderProduct.objects.create(
                order=order,
                product=item.product,
                amount=item.quantity,
                total=item.total_price()
            )

        cart_items.delete()
        return redirect('store:home')

    return render(request, 'order_create.html',
                  {'cart_items': cart_items, 'total_price': total_price, 'amount': amount, 'form': form})


def saved(request, pk=None):
    product_pk = request.GET.get('product') if not pk else pk
    product_data = Product.objects.get(pk=product_pk)

    if request.user not in product_data.saved.all():
        product_data.saved.add(request.user)
    elif request.user in product_data.saved.all():
        product_data.saved.remove(request.user)


def saved_page(request):
    product_saved = Product.objects.filter(saved=request.user)
    action = request.GET.get('action')

    if action:
        saved(request)
        return redirect('store:saved_page')

    amount = show_amount(request)

    return render(request, 'saved_page.html', {'saved': product_saved, 'amount': amount})


def orders(request):
    orders_list = Order.objects.filter(customer=request.user)
    requests = [item.order.pk for item in CancelRequest.objects.all()]

    amount = show_amount(request)

    return render(request, 'orders.html', {'orders': orders_list, 'amount': amount, 'requests': requests})


def show_amount(request):
    token = request.COOKIES.get('csrftoken')
    guest = Guest.objects.filter(token=token).last()

    cart_items = CartItem.objects.filter(customer=request.user if request.user.is_authenticated else None,
                                         guest=guest if request.user.is_anonymous else None)

    return sum([i.quantity for i in cart_items])


def order_cancel(request, pk):
    order_data = Order.objects.get(pk=pk)
    CancelRequest.objects.create(order=order_data)
    return render(request, 'order_cancel.html', {'order': order_data})



