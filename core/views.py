import json, uuid
from decimal import Decimal, InvalidOperation
from django.conf import settings
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db import transaction
from django.db.models import Count, Q, Sum
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST
from .forms import CustomerForm, OrderForm, OrderItemFormSet, PaymentForm, ProductForm, RouteForm, VehicleForm, VisitFormSet
from .models import AuditEvent, Customer, Order, Payment, Product, Route, Vehicle, Visit

def role(user):
    return getattr(getattr(user, "profile", None), "role", "ADMIN" if user.is_superuser else "DRIVER")
def manager_required(view):
    @login_required
    def wrapped(request, *args, **kwargs):
        if role(request.user) == "DRIVER":
            messages.error(request, "Esta acción requiere rol de administrador o supervisor."); return redirect("dashboard")
        return view(request, *args, **kwargs)
    return wrapped
def audit(user, entity, object_id, action, details=None): AuditEvent.objects.create(actor=user, entity=entity, entity_id=object_id, action=action, details=details or {})

@login_required
def dashboard(request):
    today = timezone.localdate(); routes = Route.objects.filter(date=today)
    if role(request.user) == "DRIVER": routes = routes.filter(driver=request.user)
    return render(request, "core/dashboard.html", {"routes":routes.prefetch_related("visits"), "customers":Customer.objects.filter(active=True).count(), "pending":Order.objects.filter(status__in=["PENDING","ASSIGNED"]).count(), "receivable":sum((o.balance for o in Order.objects.all()), Decimal("0")), "today_collected":Payment.objects.filter(received_at__date=today).aggregate(v=Sum("amount"))["v"] or 0})

@login_required
def customer_list(request): return render(request, "core/object_list.html", {"title":"Clientes", "objects":Customer.objects.all(), "create_url":"customer_create", "type":"customer"})
@login_required
def customer_detail(request, pk):
    obj=get_object_or_404(Customer,pk=pk); return render(request,"core/customer_detail.html",{"object":obj,"orders":obj.orders.prefetch_related("items","payments")})
@manager_required
def customer_edit(request, pk=None): return model_edit(request, CustomerForm, Customer, pk, "Clientes", "customer_list")
@login_required
def product_list(request): return render(request,"core/object_list.html",{"title":"Productos","objects":Product.objects.all(),"create_url":"product_create","type":"product"})
@manager_required
def product_edit(request,pk=None): return model_edit(request,ProductForm,Product,pk,"Productos","product_list")
@login_required
def vehicle_list(request): return render(request,"core/object_list.html",{"title":"Vehículos","objects":Vehicle.objects.all(),"create_url":"vehicle_create","type":"vehicle"})
@manager_required
def vehicle_edit(request,pk=None): return model_edit(request,VehicleForm,Vehicle,pk,"Vehículos","vehicle_list")

def model_edit(request, form_cls, model, pk, title, redirect_name):
    obj=get_object_or_404(model,pk=pk) if pk else None; form=form_cls(request.POST or None,instance=obj)
    if form.is_valid():
        obj=form.save(); audit(request.user,model.__name__,obj.pk,"actualizado" if pk else "creado"); messages.success(request,"Información guardada."); return redirect(redirect_name)
    return render(request,"core/form.html",{"form":form,"title":title,"object":obj,"is_customer":model is Customer,"google_maps_api_key":settings.GOOGLE_MAPS_API_KEY})

@login_required
def order_list(request): return render(request,"core/order_list.html",{"orders":Order.objects.select_related("customer").prefetch_related("items","payments")})
@login_required
def order_detail(request,pk): return render(request,"core/order_detail.html",{"object":get_object_or_404(Order.objects.prefetch_related("items__product","payments"),pk=pk)})
@manager_required
def order_edit(request,pk=None):
    obj=get_object_or_404(Order,pk=pk) if pk else Order(); form=OrderForm(request.POST or None,instance=obj); formset=OrderItemFormSet(request.POST or None,instance=obj)
    if form.is_valid() and formset.is_valid():
        with transaction.atomic(): obj=form.save(); formset.instance=obj; formset.save(); audit(request.user,"Order",obj.pk,"actualizado" if pk else "creado")
        messages.success(request,"Pedido guardado."); return redirect("order_detail",pk=obj.pk)
    return render(request,"core/formset.html",{"form":form,"formset":formset,"title":"Pedido"})

@login_required
def route_list(request):
    qs=Route.objects.select_related("driver","vehicle").annotate(visit_count=Count("visits"));
    if role(request.user)=="DRIVER": qs=qs.filter(driver=request.user)
    return render(request,"core/route_list.html",{"routes":qs})
@login_required
def route_detail(request,pk):
    obj=get_object_or_404(Route.objects.select_related("driver","vehicle").prefetch_related("visits__order__customer","visits__order__items"),pk=pk)
    if role(request.user)=="DRIVER" and obj.driver_id != request.user.id: return redirect("route_list")
    return render(request,"core/route_detail.html",{"object":obj})
@manager_required
def route_edit(request,pk=None):
    obj=get_object_or_404(Route,pk=pk) if pk else Route(); form=RouteForm(request.POST or None,instance=obj); formset=VisitFormSet(request.POST or None,instance=obj)
    if form.is_valid() and formset.is_valid():
        with transaction.atomic(): obj=form.save(); formset.instance=obj; formset.save(); obj.visits.update(); Order.objects.filter(visits__route=obj,status="PENDING").update(status="ASSIGNED"); audit(request.user,"Route",obj.pk,"actualizada" if pk else "creada")
        messages.success(request,"Ruta guardada."); return redirect("route_detail",pk=obj.pk)
    return render(request,"core/formset.html",{"form":form,"formset":formset,"title":"Ruta"})

@login_required
def payment_list(request): return render(request,"core/payment_list.html",{"payments":Payment.objects.select_related("order__customer","collected_by")[:200]})
@login_required
def payment_create(request):
    form=PaymentForm(request.POST or None)
    if form.is_valid():
        p=form.save(commit=False); p.collected_by=request.user
        if p.amount > p.order.balance: form.add_error("amount","El cobro supera el saldo pendiente.")
        else: p.save(); audit(request.user,"Payment",p.pk,"cobro registrado"); messages.success(request,"Cobro registrado."); return redirect("payment_list")
    return render(request,"core/form.html",{"form":form,"title":"Registrar cobro"})
@manager_required
def reports(request):
    orders=Order.objects.select_related("customer").prefetch_related("items","payments"); return render(request,"core/reports.html",{"sales":sum((o.total for o in orders),Decimal("0")),"collected":Payment.objects.aggregate(v=Sum("amount"))["v"] or 0,"receivable":sum((o.balance for o in orders),Decimal("0")),"delivered":orders.filter(status="DELIVERED").count(),"failed":orders.filter(status="FAILED").count(),"debtors":[o for o in orders if o.balance>0],"routes":Route.objects.annotate(total=Count("visits"),done=Count("visits",filter=Q(visits__status="DELIVERED")))[:20]})
@login_required
def offline(request): return render(request,"core/offline.html")

@login_required
def map_view(request):
    return render(request, "core/map.html", {"google_maps_api_key": settings.GOOGLE_MAPS_API_KEY})

@login_required
def api_map_data(request):
    routes = Route.objects.select_related("driver", "vehicle").prefetch_related("visits__order__customer")
    if role(request.user) == "DRIVER": routes = routes.filter(driver=request.user)
    customers = Customer.objects.filter(active=True, latitude__isnull=False, longitude__isnull=False)
    return JsonResponse({"customers": [{"id": c.id, "name": c.name, "phone": c.phone, "address": c.address, "reference": c.reference, "zone": c.zone, "lat": float(c.latitude), "lng": float(c.longitude)} for c in customers], "routes": [{"id": r.id, "name": r.name, "date": str(r.date), "status": r.get_status_display(), "driver": r.driver.get_full_name() or r.driver.username, "vehicle": str(r.vehicle) if r.vehicle else "Sin vehículo", "stops": [{"visit_id": v.id, "sequence": v.sequence, "customer": v.order.customer.name, "address": v.order.customer.address, "lat": float(v.order.customer.latitude), "lng": float(v.order.customer.longitude)} for v in r.visits.all() if v.order.customer.latitude is not None and v.order.customer.longitude is not None]} for r in routes]})

@login_required
def api_bootstrap(request):
    routes=Route.objects.filter(driver=request.user).prefetch_related("visits__order__customer","visits__order__items__product")
    data=[]
    for r in routes:
        data.append({"id":r.id,"name":r.name,"date":str(r.date),"status":r.status,"visits":[{"id":v.id,"sequence":v.sequence,"status":v.status,"observation":v.observation,"order_id":v.order_id,"customer":v.order.customer.name,"address":v.order.customer.address,"reference":v.order.customer.reference,"phone":v.order.customer.phone,"total":str(v.order.total),"paid":str(v.order.paid),"balance":str(v.order.balance),"items":[{"name":i.product.name,"quantity":i.quantity} for i in v.order.items.all()]} for v in r.visits.all()]})
    return JsonResponse({"routes":data,"generated_at":timezone.now().isoformat()})

@csrf_exempt
@require_POST
@login_required
def api_sync(request):
    try: payload=json.loads(request.body); operations=payload.get("operations",[])
    except (ValueError,TypeError): return JsonResponse({"error":"JSON inválido"},status=400)
    results=[]
    for op in operations:
        oid=op.get("id")
        try:
            oid=uuid.UUID(str(oid)); kind=op.get("type"); data=op.get("data",{})
            if kind=="visit":
                v=Visit.objects.select_related("route","order").get(pk=data["visit_id"])
                if role(request.user)=="DRIVER" and v.route.driver_id!=request.user.id: raise PermissionError()
                v.status=data["status"]; v.observation=data.get("observation",""); v.updated_by=request.user; v.completed_at=timezone.now() if v.status!="PENDING" else None; v.save(); v.order.status=v.status; v.order.save(update_fields=["status"]); audit(request.user,"Visit",v.pk,"sincronizada",{"operation_id":str(oid),"status":v.status})
            elif kind=="payment":
                order=Order.objects.get(pk=data["order_id"]); amount=Decimal(str(data["amount"]))
                Payment.objects.get_or_create(operation_id=oid,defaults={"order":order,"amount":amount,"method":data.get("method","CASH"),"collected_by":request.user,"notes":data.get("notes","")})
            else: raise ValueError("Tipo desconocido")
            results.append({"id":str(oid),"ok":True})
        except Exception as exc: results.append({"id":str(oid),"ok":False,"error":type(exc).__name__})
    return JsonResponse({"results":results})

def service_worker(request):
    from django.http import FileResponse
    from django.conf import settings
    return FileResponse(open(settings.BASE_DIR/"static"/"js"/"sw.js","rb"),content_type="application/javascript")
