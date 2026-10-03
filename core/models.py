import uuid
from django.contrib.auth.models import User
from django.core.validators import MinValueValidator
from django.db import models
from django.utils import timezone


class Profile(models.Model):
    class Role(models.TextChoices):
        ADMIN = "ADMIN", "Administrador"
        SUPERVISOR = "SUPERVISOR", "Supervisor / propietario"
        DRIVER = "DRIVER", "Repartidor"
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name="profile")
    role = models.CharField(max_length=15, choices=Role.choices, default=Role.DRIVER)
    phone = models.CharField(max_length=25, blank=True)
    def __str__(self): return f"{self.user.get_full_name() or self.user.username} — {self.get_role_display()}"


class Customer(models.Model):
    name = models.CharField(max_length=150)
    phone = models.CharField(max_length=25, blank=True)
    address = models.TextField()
    reference = models.CharField(max_length=255, blank=True)
    zone = models.CharField(max_length=80, blank=True)
    latitude = models.DecimalField(max_digits=10, decimal_places=7, null=True, blank=True)
    longitude = models.DecimalField(max_digits=10, decimal_places=7, null=True, blank=True)
    frequency = models.CharField(max_length=80, blank=True, help_text="Ej. lunes y jueves")
    active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    def __str__(self): return self.name


class Product(models.Model):
    class Kind(models.TextChoices):
        WATER = "WATER", "Agua purificada"
        GAS = "GAS", "Gas"
    name = models.CharField(max_length=120)
    presentation = models.CharField(max_length=100)
    kind = models.CharField(max_length=10, choices=Kind.choices)
    price = models.DecimalField(max_digits=10, decimal_places=2, validators=[MinValueValidator(0)])
    active = models.BooleanField(default=True)
    def __str__(self): return f"{self.name} — {self.presentation}"


class Vehicle(models.Model):
    plate = models.CharField(max_length=20, unique=True)
    description = models.CharField(max_length=120)
    capacity = models.PositiveIntegerField(default=1)
    active = models.BooleanField(default=True)
    def __str__(self): return f"{self.plate} — {self.description}"


class Order(models.Model):
    class Status(models.TextChoices):
        PENDING = "PENDING", "Pendiente"
        ASSIGNED = "ASSIGNED", "Asignado"
        DELIVERED = "DELIVERED", "Entregado"
        FAILED = "FAILED", "No entregado"
        CANCELLED = "CANCELLED", "Cancelado"
    customer = models.ForeignKey(Customer, on_delete=models.PROTECT, related_name="orders")
    scheduled_date = models.DateField(default=timezone.localdate)
    status = models.CharField(max_length=12, choices=Status.choices, default=Status.PENDING)
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    @property
    def total(self): return sum((i.subtotal for i in self.items.all()), 0)
    @property
    def paid(self): return sum((p.amount for p in self.payments.all()), 0)
    @property
    def balance(self): return self.total - self.paid
    def __str__(self): return f"Pedido #{self.pk} — {self.customer}"


class OrderItem(models.Model):
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name="items")
    product = models.ForeignKey(Product, on_delete=models.PROTECT)
    quantity = models.PositiveIntegerField(default=1)
    unit_price = models.DecimalField(max_digits=10, decimal_places=2, validators=[MinValueValidator(0)])
    @property
    def subtotal(self): return self.quantity * self.unit_price


class Route(models.Model):
    class Status(models.TextChoices):
        PLANNED = "PLANNED", "Planificada"
        ACTIVE = "ACTIVE", "En recorrido"
        DONE = "DONE", "Finalizada"
    date = models.DateField(default=timezone.localdate)
    name = models.CharField(max_length=120)
    driver = models.ForeignKey(User, on_delete=models.PROTECT, related_name="routes")
    vehicle = models.ForeignKey(Vehicle, on_delete=models.PROTECT, null=True, blank=True)
    status = models.CharField(max_length=10, choices=Status.choices, default=Status.PLANNED)
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    def __str__(self): return f"{self.name} — {self.date}"


class Visit(models.Model):
    class Status(models.TextChoices):
        PENDING = "PENDING", "Pendiente"
        DELIVERED = "DELIVERED", "Entregado"
        FAILED = "FAILED", "No entregado"
    route = models.ForeignKey(Route, on_delete=models.CASCADE, related_name="visits")
    order = models.ForeignKey(Order, on_delete=models.PROTECT, related_name="visits")
    sequence = models.PositiveIntegerField(default=1)
    status = models.CharField(max_length=12, choices=Status.choices, default=Status.PENDING)
    observation = models.TextField(blank=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    updated_by = models.ForeignKey(User, on_delete=models.PROTECT, null=True, blank=True)
    updated_at = models.DateTimeField(auto_now=True)
    class Meta:
        ordering = ["sequence"]
        constraints = [models.UniqueConstraint(fields=["route", "sequence"], name="unique_route_sequence")]
    def __str__(self): return f"{self.route} / {self.sequence}. {self.order.customer}"


class Payment(models.Model):
    class Method(models.TextChoices):
        CASH = "CASH", "Efectivo"
        TRANSFER = "TRANSFER", "Transferencia"
        OTHER = "OTHER", "Otro"
    operation_id = models.UUIDField(default=uuid.uuid4, unique=True, editable=False)
    order = models.ForeignKey(Order, on_delete=models.PROTECT, related_name="payments")
    amount = models.DecimalField(max_digits=10, decimal_places=2, validators=[MinValueValidator(0.01)])
    method = models.CharField(max_length=12, choices=Method.choices, default=Method.CASH)
    collected_by = models.ForeignKey(User, on_delete=models.PROTECT)
    received_at = models.DateTimeField(default=timezone.now)
    notes = models.CharField(max_length=255, blank=True)
    synced_at = models.DateTimeField(auto_now_add=True)
    def __str__(self): return f"Q{self.amount} — {self.order}"


class AuditEvent(models.Model):
    entity = models.CharField(max_length=40)
    entity_id = models.PositiveIntegerField()
    action = models.CharField(max_length=80)
    actor = models.ForeignKey(User, on_delete=models.PROTECT)
    details = models.JSONField(default=dict, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    class Meta: ordering = ["-created_at"]

# Create your models here.
