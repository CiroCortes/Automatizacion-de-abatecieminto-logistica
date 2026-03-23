# Plan de Abastecimiento PESCO Chile

Sistema de planificación de abastecimiento para sucursales y bodegas de PESCO en Chile. Genera un plan de transferencias desde Santiago hacia regiones (Calama, Antofagasta, Los Ángeles, Puerto Montt) basado en stock disponible y pedidos pendientes.

## 🎯 Problema

Las sucursales y bodegas en Chile están desabastecidas: la venta supera la capacidad de reposición. Este sistema prioriza qué transferir, desde qué bodega de Santiago y hacia qué destino, considerando solo el **pendiente** por despachar (no la cantidad total original del pedido).

## ✨ Características

- **PC y OF**: Procesa tanto Pedidos de Compra (PC) como Órdenes de Fabricación (OF)
- **Cliente desde Detalle_pedidos**: Para PC usa Razón Social; para OF usa Vendedor o Usuario
- **Stock en tránsito**: No solicita transferencia si ya hay unidades en camino hacia la sucursal
- **Pendiente real**: Asigna solo lo que falta por despachar (ej: pedido 4 unidades, pendiente 1 → asigna 1)
- **Bodegas Santiago**: 13, 013-01, 013-03, 013-05, 013-06, 013-08, 013-09, 013-PP, 013-PS

## 📋 Requisitos

- Python 3.8+
- pandas
- openpyxl

## 🚀 Instalación

```bash
# Clonar el repositorio
git clone https://github.com/tu-usuario/proyecto_backorder_pesco.git
cd proyecto_backorder_pesco

# Crear entorno virtual (recomendado)
python -m venv venv
venv\Scripts\activate   # Windows
# source venv/bin/activate  # Linux/Mac

# Instalar dependencias
pip install -r requirements.txt
```

## 📁 Archivos de entrada

Coloca estos archivos en la raíz del proyecto:

| Archivo | Descripción |
|---------|-------------|
| `stock.xlsx` | Stock actual por producto y bodega |
| `RH_Comprometido.xlsx` | Pedidos y órdenes con pendiente por despachar |
| `Detalle_pedidos.xlsx` | Detalle de pedidos (Razón Social, Vendedor) para cruce con PC |

## ▶️ Uso

```bash
python generar_plan_abastecimiento.py
```

**Salida:** `plan_abastecimiento.xlsx`

### Filtros aplicados

- Pedidos con `Fecha Creacion` ≥ 2026
- Solo líneas con `Pendiente` > 0

## 📊 Columnas del Excel generado

| Columna | Descripción |
|---------|-------------|
| Tipo | PC u OF |
| Numero | Número de pedido/orden |
| Fecha_Pedido | Fecha de creación (RH_Comprometido) |
| Cliente | Razón Social (PC) o Vendedor/Usuario (OF) |
| Codigo | Código del producto |
| Descripcion | Descripción del artículo |
| Tipo_Material | Grupo/tipo de material (Stock) |
| Cantidad_a_enviar | Unidades a transferir |
| Almacen_Origen | Bodega donde picar (013-03, 013-01, etc.) |
| Almacen_Destino | Código sucursal destino |
| Sucursal_Destino | Región (CALAMA, ANTOFAGASTA, etc.) |
| Destino | Formato combinado (ej. "2 CALAMA") |
| Vendedor | Nombre del vendedor |
| Usuario | Usuario |

## 📂 Estructura del proyecto

```
proyecto_backorder_pesco/
├── generar_plan_abastecimiento.py   # Script principal
├── PLANIFICACION.md                 # Documentación técnica y flujo
├── requirements.txt
├── README.md
├── stock.xlsx                       # (input)
├── RH_Comprometido.xlsx            # (input)
├── Detalle_pedidos.xlsx            # (input)
└── plan_abastecimiento.xlsx        # (output)
```

## 🔄 Flujo del sistema

```
Stock (Santiago)  +  RH_Comprometido (pendientes)  +  Detalle_pedidos (clientes)
        │                         │                            │
        └─────────────────────────┴────────────────────────────┘
                                    │
                                    ▼
                    Asignación por bodega (013-03, 013-01, etc.)
                    - Descuenta stock en tránsito
                    - Solo asigna Pendiente
                                    │
                                    ▼
                        plan_abastecimiento.xlsx
```

## 📖 Documentación adicional

Ver `PLANIFICACION.md` para detalles del modelo de datos, mapeo de bodegas y lógica de tránsito.

## 📄 Licencia

Proyecto interno PESCO. Uso según políticas de la organización.
