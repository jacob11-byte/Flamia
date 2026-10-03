from django.contrib import admin
from .models import AuditEvent, Customer, Order, OrderItem, Payment, Product, Profile, Route, Vehicle, Visit

class OrderItemInline(admin.TabularInline): model = OrderItem; extra = 1
class VisitInline(admin.TabularInline): model = Visit; extra = 1
@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ("id", "customer", "scheduled_date", "status", "total", "paid", "balance")
    list_filter = ("status", "scheduled_date")
    inlines = [OrderItemInline]
@admin.register(Route)
class RouteAdmin(admin.ModelAdmin):
    list_display = ("name", "date", "driver", "vehicle", "status")
    list_filter = ("status", "date")
    inlines = [VisitInline]
for model in (Profile, Customer, Product, Vehicle, Payment, AuditEvent): admin.site.register(model)
admin.site.site_header = "Flamia — Administración"

# Register your models here.
