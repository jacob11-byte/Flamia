import json, uuid
from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse
from .models import Customer, Order, OrderItem, Payment, Product, Profile, Route, Visit

class FlamiaTests(TestCase):
    def setUp(self):
        self.driver=User.objects.create_user("driver",password="test12345");self.driver.profile.role=Profile.Role.DRIVER;self.driver.profile.save()
        self.manager=User.objects.create_user("manager",password="test12345");self.manager.profile.role=Profile.Role.SUPERVISOR;self.manager.profile.save()
        self.customer=Customer.objects.create(name="Cliente",address="Guatemala")
        self.product=Product.objects.create(name="Agua",presentation="5 gal",kind="WATER",price=20)
        self.order=Order.objects.create(customer=self.customer);OrderItem.objects.create(order=self.order,product=self.product,quantity=2,unit_price=20)
        self.route=Route.objects.create(name="Ruta",driver=self.driver);self.visit=Visit.objects.create(route=self.route,order=self.order,sequence=1)
    def test_totals_and_partial_payment(self):
        Payment.objects.create(order=self.order,amount=15,collected_by=self.driver)
        self.assertEqual(self.order.total,40);self.assertEqual(self.order.paid,15);self.assertEqual(self.order.balance,25)
    def test_driver_cannot_create_customer(self):
        self.client.login(username="driver",password="test12345")
        self.assertRedirects(self.client.get(reverse("customer_create")),reverse("dashboard"))
    def test_offline_sync_is_idempotent(self):
        self.client.login(username="driver",password="test12345"); oid=str(uuid.uuid4()); body={"operations":[{"id":oid,"type":"payment","data":{"order_id":self.order.id,"amount":"10","method":"CASH"}}]}
        for _ in range(2): self.assertEqual(self.client.post(reverse("api_sync"),data=json.dumps(body),content_type="application/json").status_code,200)
        self.assertEqual(Payment.objects.count(),1)
    def test_visit_sync_updates_trace(self):
        self.client.login(username="driver",password="test12345");body={"operations":[{"id":str(uuid.uuid4()),"type":"visit","data":{"visit_id":self.visit.id,"status":"DELIVERED","observation":"Entregado"}}]}
        self.client.post(reverse("api_sync"),data=json.dumps(body),content_type="application/json");self.visit.refresh_from_db();self.order.refresh_from_db();self.assertEqual(self.visit.status,"DELIVERED");self.assertEqual(self.order.status,"DELIVERED")

# Create your tests here.
