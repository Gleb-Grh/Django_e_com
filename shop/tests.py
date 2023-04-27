from decimal import Decimal
from django.contrib.auth.models import User
from django.test import TestCase
from shop.models import Product, Payment, Order, OrderItem
import zoneinfo
from django.utils import timezone


class TestDataBase(TestCase):
    fixtures = [
        "shop/fixtures/data.json" 
    ]

    def setUp(self):
        self.user = User.objects.get(username="Admin")
        self.p = Product.objects.all().first()

    def test_user_exists(self):
        users = User.objects.all()
        users_number = users.count()
        user = users.first() #Первый пользователь
        self.assertEqual(users_number, 1) #Кол-во пользователей
        self.assertEqual(user.username, "Admin") # сравнение имени первого пользователя 
        self.assertTrue(user.is_superuser) 

    def test_user_check_password(self):
        self.assertTrue(self.user.check_password('841200'))

    def test_all_data(self):
        self.assertGreater(Product.objects.all().count(), 0)
        # self.assertGreater(Order.objects.all().count(), 0) 
        # self.assertGreater(OrderItem.objects.all().count(), 0)
        # self.assertGreater(Payment.objects.all().count(), 0) 
    
    def find_card_number(self):
        cart_number = Order.objects.filter(user=self.user,
                                           status=Order.STATUS_CART).count()
        return cart_number
    
    def test_function_get_cart(self):
        pass
        #1 No cart
        self.assertEqual(self.find_card_number(), 0) #
        
        #2 Create cart
        Order.get_cart(self.user)
        self.assertEqual(self.find_card_number(), 1)
        
        #3 Get started cart
        Order.get_cart(self.user)
        self.assertEqual(self.find_card_number(), 1)
        

    def test_cart_order_7_days(self):

        cart = Order.get_cart(self.user)
        cart.creation_time = timezone.datetime(2000, 1, 1, tzinfo=zoneinfo.ZoneInfo('UTC'))
        cart.save()
        cart = Order.get_cart(self.user)
        self.assertEqual((timezone.now() - cart.creation_time).days, 0)

    def test_recalculate_order_amount_after_changing_orderitem(self):
        """ Проверка корзины
        1. получить началбную сумму заказа
        2. после добавления товара
        3. после удаления товара """
        #1
        cart = Order.get_cart(self.user)
        self.assertEqual(cart.amount, Decimal(0))
        #2
        i = OrderItem.objects.create(order=cart, product=self.p, price=2, quantity=2)
        i = OrderItem.objects.create(order=cart, product=self.p, price=2, quantity=3)
        cart = Order.get_cart(self.user)
        self.assertEqual(cart.amount, Decimal(10))
        #3
        i.delete()
        cart = Order.get_cart(self.user)
        self.assertEqual(cart.amount, Decimal(4))

    def test_cart_status_changing_after_applying_make_order(self):
        '''Проверка изменения статуса корзины после Order.make_order() (добавить этот метод)'''
        # 1. Пытаемся изменить статус для пустой корзины (не должен меняться)
        cart = Order.get_cart(self.user)
        cart.make_order()
        self.assertEqual(cart.status, Order.STATUS_CART)
        # 2. пытаемся сменить статус для не пустой корзины'''
        OrderItem.objects.create(order=cart, product=self.p, price=2, quantity=2)
        cart.make_order()
        self.assertEqual(cart.status, Order.STATUS_WAITING_FOR_PAYMENT)
        
    def test_method_get_amount_of_unpaid_orders(self):
        '''Проверить @staticmethod get_amount_of_unpaid_orders() для некоторых случаев
        1. До создания корзины
        2. после создания корзины
        3. после создания заказа в корзине
        4. после оплаты заказа
        5. после удаления всех заказов
        '''
        # 1.
        amount = Order.get_amount_of_unpaid_orders(self.user)
        self.assertEqual(amount, Decimal(0))

        # 2.
        cart = Order.get_cart(self.user)
        OrderItem.objects.create(order=cart, product=self.p, price=2, quantity=2)
        amount = Order.get_amount_of_unpaid_orders(self.user)
        self.assertEqual(amount, Decimal(0))

        # 3.
        cart.make_order()
        amount = Order.get_amount_of_unpaid_orders(self.user)
        self.assertEqual(amount, Decimal(4))

        # 4.
        cart.status = Order.STATUS_PAID
        cart.save()
        amount = Order.get_amount_of_unpaid_orders(self.user)
        self.assertEqual(amount, Decimal(0))

        # 5.
        Order.objects.all().delete
        amount = Order.get_amount_of_unpaid_orders(self.user)
        self.assertEqual(amount, Decimal(0))

    def test_method_get_balance(self):
        '''Проверить @staticmethod get_balance для некоторых случаев:
        1. До добавления платежа
        2. После добавдения платежа
        3. После добавдения нескольких платежей
        4. Без платежей
        '''

        # 1.
        amount = Payment.get_balance(self.user)
        self.assertEqual(amount, Decimal(0))

        # 2.
        Payment.objects.create(user=self.user, amount = 100)
        amount = Payment.get_balance(self.user)
        self.assertEqual(amount, Decimal(100))

        # 3.
        Payment.objects.create(user=self.user, amount = -50)
        amount = Payment.get_balance(self.user)
        self.assertEqual(amount, Decimal(50))

        # 4.
        Payment.objects.all().delete()
        amount = Payment.get_balance(self.user)
        self.assertEqual(amount, Decimal(0))


    def test_auto_payment_after_apply_make_order_true(self):
        '''Проверка авто платежа после подтверждения make_order()
        1. Есть необходимая сумма
        2. Нет необходимой суммы'''

        # 1.
        Order.objects.all().delete()
        cart = Order.get_cart(self.user)
        OrderItem.objects.create(order=cart, product=self.p, price=2, quantity=2)
        self.assertEqual(Payment.get_balance(self.user), Decimal(0))
        cart.make_order()
        self.assertEqual(Payment.get_balance(self.user), Decimal(0))

    def test_auto_payment_after_apply_make_order_false(self):
        # 2.
        Order.objects.all().delete()
        cart = Order.get_cart(self.user)
        OrderItem.objects.create(order=cart, product=self.p, price=2, quantity=5000000)
        cart.make_order()
        self.assertEqual(Payment.get_balance(self.user), Decimal(0))

    def test_auto_payment_after_add_required_payment(self):
        '''В этом тесте неоплаченный заказ на 13556 и баланс 13000
        После подтверждения платежа = 556
        - заказ меняет статус 
        - и баланс становится = 0'''         

        Payment.objects.create(user=self.user, amount=556)
        self.assertEqual(Payment.get_balance(self.user), Decimal(556))
        amount = Order.get_amount_of_unpaid_orders(self.user)
        self.assertEqual(amount, Decimal(0))

    def test_auto_payment_for_earlier_order(self):
        ''''В этом тесте неоплаченный заказ = 13556 и баланс = 13000
        После создем новый заказ = 1000, подтверждение платежа = 1000:
        - только ранний заказ может поменять статус
        -  баланс должен составить 13000 + 1000 - 13556 '''

        cart = Order.get_cart(self.user)
        OrderItem.objects.create(order=cart, product=self.p, price=2, quantity=500)
        Payment.objects.create(user=self.user, amount=1000)
        self.assertEqual(Payment.get_balance(self.user), Decimal(1000))
        amount = Order.get_amount_of_unpaid_orders(self.user)
        self.assertEqual(amount, Decimal(0))

    def test_auto_payment_for_all_orders(self):
        '''Неоплаченный заказ = 13556 и баланс = 13000
        После создания нового заказа = 1000, принять платёж = 10000
        - все заказы должны быть оплачены'''

        cart = Order.get_cart(self.user)
        OrderItem.objects.create(order=cart, product=self.p, price=2, quantity=500)
        Payment.objects.create(user=self.user, amount=10000)
        self.assertEqual(Payment.get_balance(self.user), Decimal(10000))
        amount = Order.get_amount_of_unpaid_orders(self.user)
        self.assertEqual(amount, Decimal(0))