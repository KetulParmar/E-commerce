from django_countries.fields import CountryField
from django.db import models
from django.contrib.auth.models import User
from django.urls import reverse


class Customer(models.Model):
    user = models.OneToOneField(User, null=False, blank=False, on_delete=models.CASCADE)

    #extra fields
    phone_field = models.CharField(max_length=12, blank=False)

    def __str__(self):
        return self.user.username


class Category(models.Model):
    category_name = models.CharField(max_length=200)

    def __str__(self):
        return self.category_name


class Product(models.Model):
    name = models.CharField(max_length=100)
    category_name = models.ForeignKey('category', on_delete=models.CASCADE)
    desc = models.TextField()
    price = models.FloatField(default=0.0)
    product_available_count = models.IntegerField(default=0)
    img = models.ImageField(upload_to='images/')

    def get_add_to_cart_url(self):
        return reverse("core:add-to-cart", kwargs={
            "pk": self.pk
        })

    def __str__(self):
        return self.name


class OrderItem(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    ordered = models.BooleanField(default=False)
    quantity = models.PositiveIntegerField(default=1)
    product = models.ForeignKey(Product, on_delete=models.CASCADE)

    def __str__(self):
        return f"{self.quantity} of {self.product.name}"

    def get_total_item_price(self):
        return self.quantity * self.product.price

    def get_final_price(self):
        return self.get_total_item_price()


class Order(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    items = models.ManyToManyField(OrderItem)
    start_date = models.DateTimeField(auto_now_add=True)
    ordered_date = models.DateTimeField()
    ordered = models.BooleanField(default=False)
    order_id = models.CharField(max_length=100, unique=True, blank=True, null=True)
    datetime_ofpayment = models.DateTimeField(auto_now_add=True)
    order_delivered = models.BooleanField(default=False)
    order_received = models.BooleanField(default=False)
    payment_method = models.CharField(default=False,max_length=50,
                                      choices=[('COD', 'Cash on Delivery'), ('Online', 'Online Payment')])

    razorpay_order_id = models.CharField(max_length=500, null=True, blank=True)
    razorpay_payment_id = models.CharField(max_length=500, null=True, blank=True)
    razorpay_signature = models.CharField(max_length=500, null=True, blank=True)

    def save(self, *args, **kwargs):
        # Check if the order_id is already set
        if not self.order_id:
            # Save the object first to generate a primary key
            super().save(*args, **kwargs)
            # Generate the order_id using the datetime_ofpayment and the primary key
            self.order_id = self.datetime_ofpayment.strftime('PAY2ME%Y%m%dOOR') + str(self.pk)
            # Save the object again to store the order_id
            kwargs['force_insert'] = False  # Avoids force_insert error
        super().save(*args, **kwargs)

    def __str__(self):
        return self.user.username

    def get_total_price(self):
        return sum(order_item.get_final_price() for order_item in self.items.all())

    def get_total_count(self):
        return self.items.count()


class CheckoutAddress(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    street_address = models.CharField(max_length=100)
    apartment_address = models.CharField(max_length=100)
    country = CountryField(multiple=False)
    zip_code = models.CharField(max_length=100)

    def __str__(self):
        return self.user.username
