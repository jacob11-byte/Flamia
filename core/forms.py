from django import forms
from django.forms import inlineformset_factory
from .models import Customer, Order, OrderItem, Payment, Product, Route, Vehicle, Visit

class StyledForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values(): field.widget.attrs.setdefault("class", "input")

class CustomerForm(StyledForm):
    class Meta: model = Customer; fields = ["name", "phone", "address", "reference", "zone", "latitude", "longitude", "frequency", "active"]
class ProductForm(StyledForm):
    class Meta: model = Product; fields = ["name", "presentation", "kind", "price", "active"]
class VehicleForm(StyledForm):
    class Meta: model = Vehicle; fields = ["plate", "description", "capacity", "active"]
class OrderForm(StyledForm):
    class Meta:
        model = Order; fields = ["customer", "scheduled_date", "notes"]
        widgets = {"scheduled_date": forms.DateInput(attrs={"type":"date"})}
OrderItemFormSet = inlineformset_factory(Order, OrderItem, fields=["product", "quantity", "unit_price"], extra=1, can_delete=True, widgets={"product":forms.Select(attrs={"class":"input"}),"quantity":forms.NumberInput(attrs={"class":"input"}),"unit_price":forms.NumberInput(attrs={"class":"input","step":"0.01"})})
class RouteForm(StyledForm):
    class Meta:
        model = Route; fields = ["date", "name", "driver", "vehicle", "status", "notes"]
        widgets = {"date": forms.DateInput(attrs={"type":"date"})}
VisitFormSet = inlineformset_factory(Route, Visit, fields=["order", "sequence"], extra=1, can_delete=True, widgets={"order":forms.Select(attrs={"class":"input"}),"sequence":forms.NumberInput(attrs={"class":"input"})})
class PaymentForm(StyledForm):
    class Meta: model = Payment; fields = ["order", "amount", "method", "notes"]
