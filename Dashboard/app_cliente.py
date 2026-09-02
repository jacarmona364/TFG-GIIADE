import os
import streamlit as st
import pyodbc
from dotenv import load_dotenv

load_dotenv()

def get_sql_connection():
    return pyodbc.connect(
        f"DRIVER={{ODBC Driver 18 for SQL Server}};"
        f"SERVER={os.getenv('AZURE_SQL_SERVER')};"
        f"DATABASE={os.getenv('AZURE_SQL_DATABASE')};"
        f"UID={os.getenv('AZURE_SQL_USER')};"
        f"PWD={os.getenv('AZURE_SQL_PASSWORD')};"
        f"Encrypt=yes;TrustServerCertificate=no;Connection Timeout=30;", 
        autocommit=False
    )

st.set_page_config(page_title="Mi Tosta | Carta Digital", page_icon="⬛", layout="wide")

# CSS para Animación Suave del Botón Verde y Diseño Premium
st.markdown("""
<style>
    .stApp { background-color: #0E1117; color: #E0E0E0; font-family: 'Helvetica Neue', sans-serif; }
    div[data-testid="stContainer"] { background-color: #1A1C23; border: 1px solid #2D303E; border-radius: 6px; padding: 15px; height: 100%; transition: 0.3s; }
    div[data-testid="stImage"] img { height: 180px !important; object-fit: cover !important; border-radius: 4px; }
    
    /* Botón verde con animación smooth */
    button[kind="primary"] {
        background-color: #00C853 !important;
        color: #FFFFFF !important;
        border: none !important;
        border-radius: 6px !important;
        font-weight: 800 !important;
        letter-spacing: 1.5px !important;
        padding: 20px !important;
        transition: all 0.3s cubic-bezier(0.25, 0.8, 0.25, 1) !important;
        transform: scale(1);
    }
    button[kind="primary"]:hover {
        background-color: #00E676 !important;
        transform: scale(1.03);
        box-shadow: 0 8px 20px rgba(0, 200, 83, 0.4) !important;
    }
</style>
""", unsafe_allow_html=True)

IMAGENES_PRODUCTOS = {
    "Patatas Bravas": "https://images.pexels.com/photos/1583884/pexels-photo-1583884.jpeg?auto=compress&cs=tinysrgb&w=500&h=500&fit=crop",
    "Alitas Crujientes": "https://images.unsplash.com/photo-1524114664604-cd8133cd67ad?w=500&h=500&fit=crop",
    "Tosta Clasica": "https://images.unsplash.com/photo-1528735602780-2552fd46c7af?w=500&h=500&fit=crop",
    "Tosta Mixta": "https://images.unsplash.com/photo-1550547660-d9450f859349?w=500&h=500&fit=crop",
    "Tosta Nordica": "https://images.unsplash.com/photo-1525351484163-7529414344d8?w=500&h=500&fit=crop",
    "Tosta de Pollo": "https://images.pexels.com/photos/1600711/pexels-photo-1600711.jpeg?auto=compress&cs=tinysrgb&w=500&h=500&fit=crop",
    "Tosta Bolonesa": "https://images.unsplash.com/photo-1572449043416-55f4685c9bb7?w=500&h=500&fit=crop",
    "Tosta de Cabra": "https://images.unsplash.com/photo-1604908176997-125f25cc6f3d?w=500&h=500&fit=crop",
    "Tosta Caprese": "https://images.pexels.com/photos/1640772/pexels-photo-1640772.jpeg?auto=compress&cs=tinysrgb&w=500&h=500&fit=crop",
    "Tosta Marinera": "https://images.pexels.com/photos/769289/pexels-photo-769289.jpeg?auto=compress&cs=tinysrgb&w=500&h=500&fit=crop",
    "Tosta Americana": "https://images.unsplash.com/photo-1606755962773-d324e0a13086?w=500&h=500&fit=crop",
    "Tosta Iberica": "https://images.pexels.com/photos/3752608/pexels-photo-3752608.jpeg?auto=compress&cs=tinysrgb&w=500&h=500&fit=crop",
    "Tosta de la Huerta": "https://images.unsplash.com/photo-1490645935967-10de6ba17061?w=500&h=500&fit=crop",
    "Tosta Philadelphia": "https://images.unsplash.com/photo-1528736235302-52922df5c122?w=500&h=500&fit=crop",
    "Tosta Dulce": "https://images.pexels.com/photos/376464/pexels-photo-376464.jpeg?auto=compress&cs=tinysrgb&w=500&h=500&fit=crop",
    "Tosta Mediterranea": "https://images.pexels.com/photos/1633525/pexels-photo-1633525.jpeg?auto=compress&cs=tinysrgb&w=500&h=500&fit=crop",
    "Tosta Fitness": "https://images.unsplash.com/photo-1504674900247-0877df9cc836?w=500&h=500&fit=crop",
    "Agua": "https://images.unsplash.com/photo-1548839140-29a749e1cf4d?w=500&h=500&fit=crop",
    "Cerveza": "https://images.unsplash.com/photo-1535958636474-b021ee887b13?w=500&h=500&fit=crop",
    "Vino": "https://images.unsplash.com/photo-1510812431401-41d2bd2722f3?w=500&h=500&fit=crop"
}

# Inicializamos el contador de reset si no existe
if 'reset_counter' not in st.session_state:
    st.session_state.reset_counter = 0

# Control de éxito del pago para mostrar globos tras el reset
if st.session_state.get('pago_exitoso', False):
    st.success("🎉 ¡TRANSACCIÓN APROBADA! Comanda enviada a producción.")
    st.balloons()
    st.session_state.pago_exitoso = False

st.title("MI TOSTA")
col_carta, col_carrito = st.columns([2.5, 1], gap="large")

try:
    conn = get_sql_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT DISTINCT producto_final, categoria, precio_venta, descripcion_plato FROM recetas")
    productos_bd = cursor.fetchall()
    cursor.close()
    conn.close()
except Exception as e:
    st.error(f"Fallo de servidor: {e}")
    productos_bd = []

categorias = {"Entrantes": [], "Tostas": [], "Bebidas": []}
for p in productos_bd:
    if p[1] in categorias: categorias[p[1]].append(p)

cantidades = {}

with col_carta:
    tab1, tab2, tab3 = st.tabs(["ENTRANTES", "TOSTAS", "BEBIDAS"])
    def renderizar_categoria(lista_productos):
        for i in range(0, len(lista_productos), 3):
            cols = st.columns(3, gap="medium")
            for j in range(3):
                if i + j < len(lista_productos):
                    prod, cat, precio, desc = lista_productos[i + j]
                    with cols[j]:
                        with st.container():
                            st.image(IMAGENES_PRODUCTOS.get(prod, "https://images.unsplash.com/photo-1504674900247-0877df9cc836?w=500&h=500&fit=crop"), use_container_width=True)
                            st.markdown(f"**{prod.upper()}**")
                            st.caption(f"{desc}")
                            st.markdown(f"**{precio:.2f} €**")
                            
                            # USAMOS EL RESET_COUNTER EN LA KEY PARA REINICIAR LOS WIDGETS
                            key_cant = f"cant_{prod}_{st.session_state.reset_counter}"
                            
                            cantidades[prod] = st.number_input(
                                f"Uds. de {prod}", min_value=0, max_value=20, value=0, step=1, 
                                label_visibility="collapsed", key=key_cant
                            )
            st.write("")

    with tab1: renderizar_categoria(categorias["Entrantes"])
    with tab2: renderizar_categoria(categorias["Tostas"])
    with tab3: renderizar_categoria(categorias["Bebidas"])

with col_carrito:
    st.markdown("### RESUMEN DEL PEDIDO")
    mesa = st.number_input("NÚMERO DE MESA", min_value=1, max_value=50, value=1, step=1)
    st.divider()
    
    total_pedido = 0.0
    items_seleccionados = {p: c for p, c in cantidades.items() if c > 0}
    
    if not items_seleccionados:
        st.info("Tu carrito está vacío.")
    else:
        for prod, cant in items_seleccionados.items():
            precio_unitario = next((p[2] for p in productos_bd if p[0] == prod), 0.0)
            subtotal = precio_unitario * cant
            total_pedido += subtotal
            st.markdown(f"{cant}x **{prod}** : {subtotal:.2f} €")
            
        st.divider()
        st.markdown(f"## TOTAL: {total_pedido:.2f} €")
        
        # Botón con type="primary" para enlazarlo con el CSS verde
        if st.button("💳 PROCESAR PAGO", type="primary", use_container_width=True):
            exito = False
            
            try:
                conn = get_sql_connection()
                cursor = conn.cursor()
                
                for prod, cant in items_seleccionados.items():
                    for _ in range(cant):
                        cursor.execute("INSERT INTO pedidos_activos (mesa, producto) VALUES (?, ?)", (int(mesa), prod))
                        cursor.execute("SELECT ingrediente_inventario, cantidad_usada FROM recetas WHERE producto_final = ?", (prod,))
                        for ing in cursor.fetchall():
                            cursor.execute("UPDATE inventario SET stock = stock - ? WHERE descripcion = ?", (ing[1], ing[0]))
                
                cursor.execute("INSERT INTO asientos_contables (proveedor, total, fecha) VALUES (?, ?, GETDATE())", (f"Terminal Venta Mesa {mesa}", total_pedido))
                conn.commit()
                exito = True
                
            except Exception as tx_err:
                if 'conn' in locals() and conn: 
                    try: 
                        conn.rollback() 
                    except Exception: 
                        pass
                st.error(f"Error en la transacción: {tx_err}")
                
            finally:
                if 'cursor' in locals() and cursor:
                    try:
                        cursor.close()
                    except Exception:
                        pass
                if 'conn' in locals() and conn:
                    try:
                        conn.close()
                    except Exception:
                        pass

            if exito:
                st.session_state.pago_exitoso = True
                # EN LUGAR DE BORRAR CADA KEY, SIMPLEMENTE AVANZAMOS EL CONTADOR
                st.session_state.reset_counter += 1
                st.rerun()