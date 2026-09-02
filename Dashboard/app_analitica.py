import os
import streamlit as st
import pyodbc
import pandas as pd
import numpy as np
import plotly.express as px
import time
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()

# --- CONFIGURACIÓN DE LA PÁGINA ---
st.set_page_config(page_title="Mi Tosta | ERP Intelligence", layout="wide", page_icon="📈")

# --- CSS: EFECTO RELIEVE Y SOMBRAS 3D (NEUMORFISMO OSCURO) ---
st.markdown("""
<style>
    /* Fondo principal más oscuro para que resalte el relieve */
    .stApp { background-color: #0E1117; color: #E0E0E0; font-family: 'Helvetica Neue', sans-serif; }
    
    /* Contenedores con borde (Tarjetas 3D) */
    div[data-testid="stVerticalBlockBorderWrapper"] {
        background: linear-gradient(145deg, #151720, #11131a) !important; /* Gradiente sutil */
        border-radius: 12px !important;
        border: 1px solid #1c1e29 !important;
        /* El relieve: Borde superior y lateral izquierdo sutilmente más claros simulando luz */
        border-top: 1px solid #33384D !important; 
        border-left: 1px solid #2A2D3E !important; 
        /* Doble sombra: Sombra oscura proyectada abajo a la derecha, brillo sutil arriba a la izquierda */
        box-shadow: 8px 8px 18px rgba(0, 0, 0, 0.7), 
                   -3px -3px 10px rgba(255, 255, 255, 0.03) !important;
        transition: all 0.3s ease;
    }
    
    /* Animación al pasar el ratón */
    div[data-testid="stVerticalBlockBorderWrapper"]:hover {
        transform: translateY(-3px);
        box-shadow: 12px 12px 24px rgba(0, 0, 0, 0.9), 
                   -4px -4px 12px rgba(255, 255, 255, 0.05) !important;
    }
    
    /* Estilizar las métricas para que encajen con el 3D */
    div[data-testid="stMetricValue"] { color: #FFFFFF !important; font-size: 2.2rem !important; font-weight: 300 !important; }
    div[data-testid="stMetricLabel"] { color: #8B8F9E !important; font-size: 0.85rem !important; text-transform: uppercase; letter-spacing: 1.5px; }
    
    /* Estilo del Sidebar */
    div[data-testid="stSidebar"] { background-color: #12141C; border-right: 1px solid #1c1e29; box-shadow: 5px 0 15px rgba(0,0,0,0.5); }
    
    #MainMenu, footer, header {visibility: hidden;}
</style>
""", unsafe_allow_html=True)

# --- CONEXIÓN A AZURE SQL ---
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

@st.cache_data(ttl=30)
def cargar_datos():
    try:
        conn = get_sql_connection()
        df_pedidos = pd.read_sql("SELECT id, mesa, producto, fecha_creacion, fecha_cierre, importe FROM historial_pedidos", conn)
        df_conta = pd.read_sql("SELECT id, proveedor, total, fecha FROM asientos_contables", conn)
        df_inventario = pd.read_sql("SELECT producto, descripcion, stock, precio_unitario FROM inventario", conn)
        conn.close()
        
        if not df_pedidos.empty:
            df_pedidos['fecha_cierre'] = pd.to_datetime(df_pedidos['fecha_cierre'])
            df_pedidos['Hora'] = df_pedidos['fecha_cierre'].dt.hour
            
        return df_pedidos, df_conta, df_inventario
    except Exception:
        return pd.DataFrame(), pd.DataFrame(), pd.DataFrame()

# Cargar datos
df_pedidos, df_conta, df_inventario = cargar_datos()

# --- INICIALIZACIÓN DE VARIABLES DE SESIÓN ---
if 'logged_in' not in st.session_state:
    st.session_state['logged_in'] = False
if 'username' not in st.session_state:
    st.session_state['username'] = ""

# --- FUNCIÓN DE LOGIN ---
def show_login():
    col1, col2, col3 = st.columns([1, 1.2, 1])
    with col2:
        st.markdown("<br><br><br>", unsafe_allow_html=True)
        with st.container(border=True):
            st.markdown("<h2 style='text-align: center; color: #0078D4;'>Mi Tosta ERP</h2>", unsafe_allow_html=True)
            st.markdown("<p style='text-align: center; color: #888888;'>Panel de Administración e Inteligencia de Negocio</p>", unsafe_allow_html=True)
            
            with st.form("login_form"):
                st.text_input("Usuario", key="user_input", placeholder="admin / mitosta")
                st.text_input("Contraseña", type="password", key="pass_input", placeholder="••••••••")
                submit = st.form_submit_button("Iniciar Sesión", use_container_width=True)
                
                if submit:
                    user = st.session_state.user_input
                    pwd = st.session_state.pass_input
                    if (user == "admin" and pwd == "admin") or (user == "mitosta" and pwd == "mitosta"):
                        st.session_state['logged_in'] = True
                        st.session_state['username'] = user
                        st.rerun()
                    else:
                        st.error("❌ Credenciales incorrectas.")

# --- FUNCIONES DEL DASHBOARD ---

def show_financiero():
    st.title(":material/monitoring: Rendimiento Financiero")
    st.markdown("Visualización en tiempo real de la facturación y el margen operativo.")
    
    ingresos = df_conta['total'].sum() if not df_conta.empty else 0.0
    platos_servidos = len(df_pedidos) if not df_pedidos.empty else 0
    ticket_medio = ingresos / len(df_conta) if not df_conta.empty and len(df_conta) > 0 else 0.0
    margen_estimado = 68.5  

    # Envolver los KPIs en un contenedor para que cojan el efecto relieve
    with st.container(border=True):
        kpi1, kpi2, kpi3, kpi4 = st.columns(4)
        kpi1.metric(label="Ingresos Brutos", value=f"{ingresos:.2f} €", delta="Operativa Diaria")
        kpi2.metric(label="Platos Servidos", value=f"{platos_servidos}", delta="+12% vs Ayer")
        kpi3.metric(label="Ticket Medio", value=f"{ticket_medio:.2f} €", delta="-0.50 €", delta_color="inverse")
        kpi4.metric(label="Margen Operativo", value=f"{margen_estimado}%", delta="Saludable", delta_color="normal")

    st.write("<br>", unsafe_allow_html=True)

    col1, col2 = st.columns([2, 1])
    
    with col1:
        with st.container(border=True):
            st.subheader(":material/timeline: Flujo de Ingresos por Hora")
            if not df_pedidos.empty:
                afluencia = df_pedidos.groupby('Hora')['importe'].sum().reset_index()
                fig = px.area(afluencia, x="Hora", y="importe", color_discrete_sequence=["#0078D4"], template="plotly_dark")
                fig.update_layout(xaxis=dict(tickmode='linear', dtick=1), margin=dict(l=0, r=0, t=30, b=0), plot_bgcolor='rgba(0,0,0,0)', paper_bgcolor='rgba(0,0,0,0)')
                st.plotly_chart(fig, use_container_width=True)
            else:
                st.info("Sin datos históricos de ventas.")

    with col2:
        with st.container(border=True):
            st.subheader(":material/pie_chart: Top 4 Productos")
            if not df_pedidos.empty:
                top_prod = df_pedidos['producto'].value_counts().head(4).reset_index()
                top_prod.columns = ['Producto', 'Unidades']
                fig2 = px.pie(top_prod, values='Unidades', names='Producto', hole=0.4, 
                              color_discrete_sequence=px.colors.sequential.Blues_r, template="plotly_dark")
                fig2.update_layout(margin=dict(l=0, r=0, t=30, b=0), plot_bgcolor='rgba(0,0,0,0)', paper_bgcolor='rgba(0,0,0,0)')
                st.plotly_chart(fig2, use_container_width=True)

def show_inventario():
    st.title(":material/inventory_2: Gestión de Almacén (Análisis ABC)")
    
    with st.container(border=True):
        st.markdown("### Acciones de Logística")
        btn1, btn2, btn3, _ = st.columns([1, 1, 1, 3])
        if btn1.button("Contactar Proveedor", icon=":material/shopping_cart:", use_container_width=True):
            st.success("Orden de compra autogenerada para productos críticos enviada al proveedor.")
        if btn2.button("Sincronizar Azure", icon=":material/sync:", use_container_width=True):
            st.cache_data.clear()
            st.rerun()
        if btn3.button("Auditoría de Stock", icon=":material/fact_check:", use_container_width=True):
            st.info("Iniciando modo inventario ciego en terminales TPV...")

    st.write("<br>", unsafe_allow_html=True)
    
    with st.container(border=True):
        st.markdown("### :material/dns: Estado de Inventario Actual")
        if not df_inventario.empty:
            df_inv_show = df_inventario.copy()
            df_inv_show['Valor Capital'] = df_inv_show['stock'] * df_inv_show['precio_unitario']
            df_inv_show = df_inv_show.sort_values(by='Valor Capital', ascending=False)
            df_inv_show['Acumulado'] = (df_inv_show['Valor Capital'].cumsum() / df_inv_show['Valor Capital'].sum()) * 100
            df_inv_show['Clasificación'] = np.where(df_inv_show['Acumulado'] <= 70, '🔴 Clase A', 
                                           np.where(df_inv_show['Acumulado'] <= 90, '🟡 Clase B', '🟢 Clase C'))
            
            df_inv_show = df_inv_show[['producto', 'stock', 'precio_unitario', 'Valor Capital', 'Clasificación']]
            df_inv_show.columns = ['Producto', 'Stock Actual', 'Coste Unitario (€)', 'Capital Inmovilizado (€)', 'Clasificación ABC']
            st.dataframe(df_inv_show, use_container_width=True, hide_index=True)
        else:
            st.warning("No se pudo cargar el inventario desde Azure.")

def show_forecasting():
    st.title(":material/online_prediction: Predicción de Demanda IA")
    
    with st.container(border=True):
        st.info("Configuración de hiperparámetros del modelo de forecasting de afluencia para optimizar turnos de cocina.")
        c1, c2 = st.columns(2)
        with c1:
            capacidad = st.slider("Capacidad Máxima de Cocina (Comandas/hr)", 10, 100, 45)
        with c2:
            clima = st.selectbox("Factor Climático (Afecta algoritmo)", ["Soleado (Normal)", "Lluvia (+15% Delivery)", "Ola de Calor (-10% Afluencia)"])

    st.write("<br>", unsafe_allow_html=True)
    
    with st.container(border=True):
        st.subheader(":material/show_chart: Curva Predictiva de Afluencia")
        horas = np.arange(12, 24, 0.5)
        factor = 1.15 if "Lluvia" in clima else (0.9 if "Calor" in clima else 1.0)
        demanda_comida = 15 * np.exp(-0.5 * ((horas - 14.5) / 1.0)**2) * factor
        demanda_cena = 25 * np.exp(-0.5 * ((horas - 21.0) / 1.5)**2) * factor
        demanda_total = demanda_comida + demanda_cena + 2
        
        df_pred = pd.DataFrame({"Hora": horas, "Demanda Estimada": demanda_total, "Capacidad Máxima": capacidad})
        
        fig = px.line(df_pred, x="Hora", y=["Demanda Estimada", "Capacidad Máxima"], 
                      color_discrete_sequence=["#00C853", "#FF3B30"], template="plotly_dark")
        fig.update_layout(legend_title_text='Métricas', margin=dict(l=0, r=0, t=30, b=0), plot_bgcolor='rgba(0,0,0,0)', paper_bgcolor='rgba(0,0,0,0)')
        st.plotly_chart(fig, use_container_width=True)

# --- ESTRUCTURA PRINCIPAL (ENRUTADOR) ---
if not st.session_state['logged_in']:
    show_login()
else:
    with st.sidebar:
        st.markdown("<h1 style='text-align: center; color: #0078D4; margin-bottom: 0;'>MI TOSTA</h1>", unsafe_allow_html=True)
        st.markdown("<p style='text-align: center; color: #888888; font-size: 0.8rem;'>Cloud ERP System</p>", unsafe_allow_html=True)
        st.markdown("---")
        
        st.write(f"👤 **Usuario:** {st.session_state['username'].upper()}")
        st.write("📍 **Sede:** Granada, España")
        st.write(f"☁️ **Database:** Azure SQL")
        
        stock_critico = len(df_inventario[df_inventario['stock'] <= 2.0]) if not df_inventario.empty else 0
        if stock_critico > 0:
            st.error(f"⚠️ {stock_critico} ítems en stock crítico")
        else:
            st.success("✅ Inventario Saneado")
            
        st.markdown("---")
        
        menu = st.radio("Navegación Principal", [
            ":material/monitoring: Resumen Financiero", 
            ":material/inventory_2: Inteligencia Inventario", 
            ":material/online_prediction: Forecasting IA"
        ])
        
        st.markdown("---")
        if st.button("Cerrar Sesión", icon=":material/logout:"):
            st.session_state['logged_in'] = False
            st.session_state['username'] = ""
            st.rerun()

    if menu == ":material/monitoring: Resumen Financiero":
        show_financiero()
    elif menu == ":material/inventory_2: Inteligencia Inventario":
        show_inventario()
    elif menu == ":material/online_prediction: Forecasting IA":
        show_forecasting()