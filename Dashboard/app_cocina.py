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

st.set_page_config(page_title="Mi Tosta - Panel de Cocina", page_icon="🍳", layout="wide")

# CSS para compactar al máximo los contenedores y textos
st.markdown("""
<style>
    /* Reducir tamaño de la imagen */
    div[data-testid="stImage"] img { height: 70px !important; object-fit: cover !important; border-radius: 4px; }
    
    /* Reducir márgenes y padding dentro de las tarjetas */
    div[data-testid="stVerticalBlockBorderWrapper"] { padding: 0.6rem !important; }
    
    /* Ajustar tamaño de textos y botones para que ocupen menos altura */
    p { margin-bottom: 0.1rem !important; font-size: 0.9rem !important; }
    div.stButton > button { padding: 0.2rem 0.5rem !important; font-size: 0.85rem !important; }
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

st.title("🍳 KDS - Comandas en Curso")
if st.button("🔄 Refrescar"): st.rerun()

try:
    conn = get_sql_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT id, mesa, producto, fecha_creacion FROM pedidos_activos ORDER BY fecha_creacion ASC")
    pedidos = cursor.fetchall()
    cursor.close()
    conn.close()
except Exception as e:
    st.error(f"Error BD: {e}")
    pedidos = []

if not pedidos:
    st.info("✅ Todo al día. Sin comandas pendientes.")
else:
    # Aumentamos a 5 columnas para hacer los tickets mucho más estrechos y apilados
    cols = st.columns(5)
    for idx, pedido in enumerate(pedidos):
        p_id, mesa, producto, fecha_creacion = pedido
        with cols[idx % 5]:
            with st.container(border=True):
                # Texto condensado en una sola línea para la cabecera
                st.markdown(f"**🪑 M{mesa}** | #{p_id}")
                
                st.image(IMAGENES_PRODUCTOS.get(producto, "https://images.unsplash.com/photo-1504674900247-0877df9cc836?w=500&h=500&fit=crop"), use_container_width=True)
                
                st.markdown(f"**{producto}**")
                st.caption(f"🕒 {fecha_creacion.strftime('%H:%M:%S')}")
                
                if st.button(f"✅ Sacar", key=f"btn_{p_id}", use_container_width=True):
                    try:
                        conn_tx = get_sql_connection()
                        cursor_tx = conn_tx.cursor()
                        cursor_tx.execute("SELECT TOP 1 precio_venta FROM recetas WHERE producto_final = ?", (producto,))
                        res = cursor_tx.fetchone()
                        importe = res[0] if res else 0.0
                        
                        cursor_tx.execute("INSERT INTO historial_pedidos (id, mesa, producto, fecha_creacion, fecha_cierre, importe) VALUES (?, ?, ?, ?, GETDATE(), ?)", (p_id, mesa, producto, fecha_creacion, importe))
                        cursor_tx.execute("DELETE FROM pedidos_activos WHERE id = ?", (p_id,))
                        conn_tx.commit()
                        st.rerun()
                    except Exception as tx_err:
                        if 'conn_tx' in locals() and conn_tx: conn_tx.rollback()
                        st.error(f"❌ Error: {tx_err}")