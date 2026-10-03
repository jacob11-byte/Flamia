# Flamia

Sistema web *offline-first* para gestionar rutas, entregas y cobros de negocios de reparto de agua purificada o gas en Guatemala.

## Funciones

- Usuarios con roles de administrador, supervisor/propietario y repartidor.
- Clientes, direcciones, referencias, frecuencia e historial.
- Productos de agua o gas, vehículos, pedidos y detalle de productos.
- Planificación diaria de rutas, asignación de repartidor/vehículo y secuencia de visitas.
- Estados de visita, observaciones, trazabilidad y auditoría.
- Cobros al contado, abonos, saldos e historial por cliente.
- Reportes de ventas, cobros, cuentas pendientes, entregas y rendimiento.
- PWA responsive con caché, IndexedDB, rutas precargadas, cola local e idempotencia de cobros.

## Instalación

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
pip install -r requirements.txt
python manage.py migrate
python manage.py seed_demo
python manage.py runserver
```

Abra `http://127.0.0.1:8000`. Datos ficticios de demostración:

- Administrador: `admin` / `Flamia2026!`
- Repartidor: `repartidor` / `Ruta2026!`

Cambie estas contraseñas antes de utilizar datos reales. El service worker requiere HTTPS en producción (localhost está permitido para desarrollo).

## Prueba offline

Inicie sesión como repartidor, abra **Sin conexión**, pulse **Descargar / actualizar rutas**, visite la ruta del día y luego desactive la red. Los estados y cobros quedan en IndexedDB y se sincronizan automáticamente al volver la conexión. El identificador UUID de cada cobro evita duplicados.
