"""
Generador de Plan de Abastecimiento - PESCO Chile
Salida: Excel con Tipo (PC/OF), Numero, Cliente, Vendedor, Usuario, Almacen origen,
        Bodega destino, Sucursal destino, Codigo, Cantidad - listo para copiar.
Incluye PC y OF. Cliente: PC=Razon Social (Detalle_pedidos), OF=Nombre Vendedor o Usuario.
"""
import pandas as pd

# Configuración según PLANIFICACION.md
BODEGAS_PRINCIPALES = [
    "13", "013-01", "013-03", "013-05", "013-06", "013-08", "013-09", "013-PP", "013-PS"
]
TRANSITO_POR_DESTINO = {
    "2": "T013-002", "002-02": "T013-022", "8": "T013-008", "10": "T013-010",
}
SUCURSAL_POR_ALMACEN = {
    "2": "CALAMA", "002-02": "ANTOFAGASTA", "8": "LOS ANGELES", "10": "PUERTO MONTT",
    "13": "SANTIAGO", "013-01": "SANTIAGO", "013-03": "SANTIAGO", "013-05": "SANTIAGO",
    "013-06": "SANTIAGO", "013-08": "SANTIAGO", "013-09": "SANTIAGO",
    "013-PP": "SANTIAGO", "013-PS": "SANTIAGO",
}

def cargar_datos():
    """Carga stock, RH (PC y OF) y Detalle_pedidos para Razon Social (solo PC)."""
    stock = pd.read_excel("stock.xlsx", sheet_name=0)
    rh = pd.read_excel("RH_Comprometido.xlsx", sheet_name=0)
    detalle = pd.read_excel("Detalle_pedidos.xlsx", sheet_name=0)

    stock["Codigo"] = stock["Codigo"].astype(str).str.strip()
    stock["Cod.Bodega"] = stock["Cod.Bodega"].astype(str).str.strip()
    rh["Codigo"] = rh["Codigo"].astype(str).str.strip()
    rh["Almacen"] = rh["Almacen"].astype(str).str.strip()

    # Filtrar RH: PC y OF, solo 2026, pendiente > 0
    rh["Fecha Creacion"] = pd.to_datetime(rh["Fecha Creacion"])
    rh = rh[rh["Fecha Creacion"].dt.year >= 2026].copy()
    rh = rh[rh["Pendiente"].fillna(0) > 0].copy()

    # Lookup Nro.Pedido -> Razon Social, Vendedor, Usuario (primer registro por pedido)
    detalle["Nro.Pedido"] = detalle["Nro.Pedido"].astype(str).str.strip()
    lookup = detalle.drop_duplicates("Nro.Pedido", keep="first")[
        ["Nro.Pedido", "Razon Social", "Vendedor", "Usuario"]
    ].set_index("Nro.Pedido")

    # Lookup Codigo -> Descripcion, Tipo_material (Stock)
    prod = stock.drop_duplicates("Codigo", keep="first")[["Codigo", "Descripcion", "Descripcion Grupo"]]
    prod = prod.rename(columns={"Descripcion Grupo": "Tipo_Material"})
    prod["Tipo_Material"] = prod["Tipo_Material"].fillna("").astype(str)
    lookup_producto = prod.set_index("Codigo")

    return stock, rh, lookup, lookup_producto


def obtener_stock_por_bodega(stock):
    """Stock de bodegas principales por (Codigo, Bodega)."""
    stk_princ = stock[stock["Cod.Bodega"].isin(BODEGAS_PRINCIPALES)].copy()
    stk_princ = stk_princ[stk_princ["Stock"].fillna(0) > 0]
    return stk_princ.groupby(["Codigo", "Cod.Bodega"])["Stock"].sum().reset_index()


def asignar_desde_bodegas(pendiente, stock_por_bodega, lookup_detalle, lookup_producto):
    """
    Asigna unidades desde bodegas Santiago. PC y OF.
    PC: Cliente = Razon Social (Detalle_pedidos). OF: Cliente = Nombre Vendedor o Usuario.
    """
    orden_bodegas = ["013-03", "013-01", "013-05", "013-06", "013-09", "013-PP", "013-PS", "013-08", "13"]
    filas = []
    stk_princ = stock_por_bodega[stock_por_bodega["Cod.Bodega"].isin(BODEGAS_PRINCIPALES)]

    for _, row in pendiente.iterrows():
        tipo = row["Tipo"]
        numero = row["Numero"]
        fecha_pedido = row["Fecha Creacion"]
        numero_str = str(numero)
        codigo = row["Codigo"]
        alm_destino = row["Almacen"]
        pend = row["Pendiente"]
        descripcion = "" if pd.isna(row.get("Descripcion")) else str(row["Descripcion"])
        tipo_material = lookup_producto.loc[codigo, "Tipo_Material"] if codigo in lookup_producto.index else ""

        # PC: Cliente = Razon Social (Detalle_pedidos). OF: Cliente = Vendedor o Usuario
        if tipo == "PC" and numero_str in lookup_detalle.index:
            info = lookup_detalle.loc[numero_str]
            cliente = "" if pd.isna(info["Razon Social"]) else str(info["Razon Social"])
            vendedor = "" if pd.isna(info["Vendedor"]) else str(info["Vendedor"])
            usuario = "" if pd.isna(info["Usuario"]) else str(info["Usuario"])
        else:
            # OF o PC sin match en Detalle: usar Nombre del Vendedor o Usuario como Cliente
            vendedor = "" if pd.isna(row.get("Nombre del Vendedor")) else str(row["Nombre del Vendedor"])
            usuario = "" if pd.isna(row.get("Usuario")) else str(row["Usuario"])
            cliente = vendedor if vendedor else usuario

        bodega_destino = alm_destino
        sucursal_destino = SUCURSAL_POR_ALMACEN.get(alm_destino, alm_destino)
        destino = f"{bodega_destino} {sucursal_destino}"  # ej: 2 CALAMA, 002-02 ANTOFAGASTA

        # Descontar stock en tránsito
        pendiente_efectivo = pend
        if alm_destino in TRANSITO_POR_DESTINO:
            transito = TRANSITO_POR_DESTINO[alm_destino]
            stk_trans = stock_por_bodega[
                (stock_por_bodega["Codigo"] == codigo) & (stock_por_bodega["Cod.Bodega"] == transito)
            ]
            if not stk_trans.empty:
                pendiente_efectivo = max(0, pend - stk_trans["Stock"].sum())

        if pendiente_efectivo <= 0:
            continue

        stk_disponible = stk_princ[stk_princ["Codigo"] == codigo].copy()
        if stk_disponible.empty:
            continue

        stk_disponible["_orden"] = stk_disponible["Cod.Bodega"].map(
            lambda x: orden_bodegas.index(x) if x in orden_bodegas else 99
        )
        stk_disponible = stk_disponible.sort_values("_orden").drop(columns=["_orden"])

        restante = pendiente_efectivo
        for _, st in stk_disponible.iterrows():
            if restante <= 0:
                break
            disponible = st["Stock"]
            a_tomar = min(restante, disponible)
            if a_tomar > 0:
                filas.append({
                    "Tipo": tipo,
                    "Numero": numero,
                    "Fecha_Pedido": fecha_pedido,
                    "Cliente": cliente,
                    "Codigo": codigo,
                    "Descripcion": descripcion,
                    "Tipo_Material": tipo_material,
                    "Cantidad_a_enviar": int(a_tomar),
                    "Almacen_Origen": st["Cod.Bodega"],
                    "Almacen_Destino": bodega_destino,
                    "Sucursal_Destino": sucursal_destino,
                    "Destino": destino,
                    "Vendedor": vendedor,
                    "Usuario": usuario,
                })
                restante -= a_tomar

    return pd.DataFrame(filas)


def main():
    print("Cargando datos...")
    stock, rh, lookup, lookup_producto = cargar_datos()

    print(f"Stock: {len(stock)} filas | RH PC+OF (>=2026, pendiente>0): {len(rh)} filas")

    stock_por_bodega = obtener_stock_por_bodega(stock)
    transito_bodegas = list(TRANSITO_POR_DESTINO.values())
    stk_trans = stock[stock["Cod.Bodega"].isin(transito_bodegas)].copy()
    stk_trans = stk_trans[stk_trans["Stock"].fillna(0) > 0]
    stk_trans = stk_trans.groupby(["Codigo", "Cod.Bodega"])["Stock"].sum().reset_index()
    stock_por_bodega = pd.concat([stock_por_bodega, stk_trans], ignore_index=True)

    print("Asignando stock a pedidos (PC y OF)...")
    plan = asignar_desde_bodegas(rh, stock_por_bodega, lookup, lookup_producto)

    # Orden: tipo, numero, fecha pedido, cliente, codigo, descripcion, tipo material, cantidad a enviar, almacen origen, almacen destino, sucursal destino, destino, vendedor, usuario
    cols = ["Tipo", "Numero", "Fecha_Pedido", "Cliente", "Codigo", "Descripcion", "Tipo_Material", "Cantidad_a_enviar",
            "Almacen_Origen", "Almacen_Destino", "Sucursal_Destino", "Destino", "Vendedor", "Usuario"]
    plan = plan[cols].sort_values(["Tipo", "Numero", "Almacen_Origen"])

    salida = "plan_abastecimiento.xlsx"
    plan.to_excel(salida, index=False, sheet_name="Plan")
    print(f"\nGuardado: {salida}")
    print(f"Filas: {len(plan)}")
    print(plan.head(12))


if __name__ == "__main__":
    main()
