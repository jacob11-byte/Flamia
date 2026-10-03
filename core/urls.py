from django.urls import path
from . import views

urlpatterns = [
    path("", views.dashboard, name="dashboard"),
    path("clientes/", views.customer_list, name="customer_list"), path("clientes/nuevo/", views.customer_edit, name="customer_create"), path("clientes/<int:pk>/", views.customer_detail, name="customer_detail"), path("clientes/<int:pk>/editar/", views.customer_edit, name="customer_edit"),
    path("productos/", views.product_list, name="product_list"), path("productos/nuevo/", views.product_edit, name="product_create"), path("productos/<int:pk>/editar/", views.product_edit, name="product_edit"),
    path("vehiculos/", views.vehicle_list, name="vehicle_list"), path("vehiculos/nuevo/", views.vehicle_edit, name="vehicle_create"), path("vehiculos/<int:pk>/editar/", views.vehicle_edit, name="vehicle_edit"),
    path("pedidos/", views.order_list, name="order_list"), path("pedidos/nuevo/", views.order_edit, name="order_create"), path("pedidos/<int:pk>/", views.order_detail, name="order_detail"), path("pedidos/<int:pk>/editar/", views.order_edit, name="order_edit"),
    path("rutas/", views.route_list, name="route_list"), path("rutas/nueva/", views.route_edit, name="route_create"), path("rutas/<int:pk>/", views.route_detail, name="route_detail"), path("rutas/<int:pk>/editar/", views.route_edit, name="route_edit"),
    path("cobros/", views.payment_list, name="payment_list"), path("cobros/nuevo/", views.payment_create, name="payment_create"),
    path("reportes/", views.reports, name="reports"), path("offline/", views.offline, name="offline"),
    path("mapa/", views.map_view, name="map"), path("api/mapa/", views.api_map_data, name="api_map_data"),
    path("api/bootstrap/", views.api_bootstrap, name="api_bootstrap"), path("api/sync/", views.api_sync, name="api_sync"),
]
