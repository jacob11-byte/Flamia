from datetime import timedelta
from django.contrib.auth.models import User
from django.core.management.base import BaseCommand
from django.utils import timezone
from core.models import Customer, Order, OrderItem, Product, Profile, Route, Vehicle, Visit

class Command(BaseCommand):
    help="Crea usuarios y datos ficticios para demostración"
    def handle(self,*args,**kwargs):
        admin,_=User.objects.get_or_create(username="admin",defaults={"first_name":"Ana","last_name":"Administradora","email":"admin@example.test","is_staff":True,"is_superuser":True});admin.set_password("Flamia2026!");admin.save();admin.profile.role=Profile.Role.ADMIN;admin.profile.save()
        driver,_=User.objects.get_or_create(username="repartidor",defaults={"first_name":"Carlos","last_name":"López"});driver.set_password("Ruta2026!");driver.save();driver.profile.role=Profile.Role.DRIVER;driver.profile.save()
        water,_=Product.objects.get_or_create(name="Garrafón",presentation="5 galones",kind="WATER",defaults={"price":18})
        gas,_=Product.objects.get_or_create(name="Cilindro",presentation="25 libras",kind="GAS",defaults={"price":135})
        vehicle,_=Vehicle.objects.get_or_create(plate="P-123ABC",defaults={"description":"Panel de reparto","capacity":60})
        customers=[]
        for name,address,zone,lat,lng in [("Tienda La Esperanza","12 avenida 4-20","Zona 1",14.6427,-90.5133),("María González","5 calle 8-15","Zona 2",14.6576,-90.5056),("Café Central","3 avenida 2-10","Zona 4",14.6206,-90.5168)]:
            customer,_=Customer.objects.get_or_create(name=name,defaults={"address":address,"zone":zone,"phone":"5555-0000","frequency":"Lunes y jueves"});customer.latitude=lat;customer.longitude=lng;customer.save(update_fields=["latitude","longitude"]);customers.append(customer)
        route,_=Route.objects.get_or_create(date=timezone.localdate(),name="Ruta Centro",driver=driver,defaults={"vehicle":vehicle,"status":"ACTIVE"})
        for n,c in enumerate(customers,1):
            order,_=Order.objects.get_or_create(customer=c,scheduled_date=timezone.localdate(),defaults={"status":"ASSIGNED"});OrderItem.objects.get_or_create(order=order,product=water,defaults={"quantity":2,"unit_price":water.price});Visit.objects.get_or_create(route=route,order=order,defaults={"sequence":n})
        self.stdout.write(self.style.SUCCESS("Demo creada: admin/Flamia2026! y repartidor/Ruta2026!"))
