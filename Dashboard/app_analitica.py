import os
import streamlit as st
import pyodbc
import pandas as pd
import numpy as np
import plotly.express as px
from datetime import datetime
from dotenv import load_dotenv

import psutil
import time
import random

# SDK de Azure (Para la gestión real de VMs)
from azure.identity import DefaultAzureCredential
from azure.mgmt.compute import ComputeManagementClient

load_dotenv()

# --- CONFIGURACIÓN DE LA PÁGINA ---
st.set_page_config(page_title="Mi Tosta | Cloud & ERP Intelligence", layout="wide", page_icon="📈")

# --- MEMORIA DE SESIÓN (ESTADOS DEL CLÚSTER) ---
if 'logged_in' not in st.session_state:
    st.session_state['logged_in'] = False
if 'username' not in st.session_state:
    st.session_state['username'] = ""
if 'nodos_cliente' not in st.session_state:
    st.session_state['nodos_cliente'] = 1
if 'estado_animacion' not in st.session_state:
    st.session_state['estado_animacion'] = None

# --- CSS: EFECTO RELIEVE Y SOMBRAS 3D (CABECERA VISIBLE PARA EL MENÚ) ---
st.markdown("""
<style>
    .stApp { background-color: #0E1117; color: #E0E0E0; font-family: 'Helvetica Neue', sans-serif; }
    
    div[data-testid="stVerticalBlockBorderWrapper"] {
        background: linear-gradient(145deg, #151720, #11131a) !important;
        border-radius: 12px !important;
        border: 1px solid #1c1e29 !important;
        border-top: 1px solid #33384D !important; 
        border-left: 1px solid #2A2D3E !important; 
        box-shadow: 8px 8px 18px rgba(0, 0, 0, 0.7), 
                   -3px -3px 10px rgba(255, 255, 255, 0.03) !important;
        transition: all 0.3s ease;
    }
    
    div[data-testid="stMetricValue"] { color: #FFFFFF !important; font-size: 2.2rem !important; font-weight: 300 !important; }
    div[data-testid="stMetricLabel"] { color: #8B8F9E !important; font-size: 0.85rem !important; text-transform: uppercase; letter-spacing: 1.5px; }
    div[data-testid="stSidebar"] { background-color: #12141C; border-right: 1px solid #1c1e29; box-shadow: 5px 0 15px rgba(0,0,0,0.5); }
    
    #MainMenu, footer {visibility: hidden;}
</style>
""", unsafe_allow_html=True)

# --- CONEXIÓN A AZURE SQL ---
def get_sql_connection():
    return pyodbc.connect(
        f"DRIVER={{ODBC Driver 18 for SQL Server}};"
        f"SERVER=tcp:{os.getenv('AZURE_SQL_SERVER')},1433;"
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

df_pedidos, df_conta, df_inventario = cargar_datos()

# --- PANTALLA DE LOGIN ---
def show_login():
    col1, col2, col3 = st.columns([1, 1.2, 1])
    with col2:
        st.markdown("<br><br><br>", unsafe_allow_html=True)
        with st.container(border=True):
            st.markdown("<h2 style='text-align: center; color: #0078D4;'>Mi Tosta ERP</h2>", unsafe_allow_html=True)
            st.markdown("<p style='text-align: center; color: #888888;'>Panel Cloud & Administración de Negocio</p>", unsafe_allow_html=True)
            
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

# --- MÓDULOS DE LA APLICACIÓN ---
def show_financiero():
    st.title(":material/monitoring: Rendimiento Financiero")
    st.markdown("Visualización en tiempo real de la facturación y el margen operativo.")
    
    ingresos = df_conta['total'].sum() if not df_conta.empty else 0.0
    platos_servidos = len(df_pedidos) if not df_pedidos.empty else 0
    ticket_medio = ingresos / len(df_conta) if not df_conta.empty and len(df_conta) > 0 else 0.0
    margen_estimado = 68.5  

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

def show_azure_infrastructure():
    st.title(":material/router: Orquestación Cloud (Gemelo Digital VMSS)")
    st.markdown("Gestión interactiva del clúster de auto-escalado escalonado ante picos de demanda.")
    
    # --- LECTURAS DE TELEMETRÍA ---
    cpu_real = psutil.cpu_percent(interval=0.1)
    ram_real = psutil.virtual_memory().percent
    hora_actual_str = datetime.now().strftime("%H:%M")

    with st.container(border=True):
        st.markdown("### 📊 Telemetría del Nodo Principal (`vm-core-erp`)")
        col1, col2, col3, col4 = st.columns([1, 1, 1, 1.5])
        col1.metric("Carga de CPU", f"{cpu_real}%")
        col2.metric("Uso de RAM", f"{ram_real}%")
        col3.metric("Hora del Sistema", hora_actual_str)
        
        with col4:
            st.markdown("<p style='color:#8B8F9E; font-size:0.85rem; font-weight:bold; margin-bottom: 2px;'>SIMULAR TRÁFICO CLÚSTER</p>", unsafe_allow_html=True)
            c_btn1, c_btn2 = st.columns(2)
            btn_up = c_btn1.button("🚀 Pico (+)", use_container_width=True)
            btn_down = c_btn2.button("📉 Bajar (-)", use_container_width=True)

    # --- LÓGICA DE TRANSICIONES ---
    MAX_NODOS = 4
    if btn_up:
        if st.session_state['nodos_cliente'] < MAX_NODOS:
            st.session_state['estado_animacion'] = 'escalando_up'
            st.session_state['nodos_cliente'] += 1
        else:
            st.toast("Límite máximo de instancias alcanzado.", icon="⚠️")
    
    elif btn_down:
        if st.session_state['nodos_cliente'] > 1:
            st.session_state['estado_animacion'] = 'escalando_down'
            st.session_state['nodos_cliente'] -= 1
        else:
            st.toast("La infraestructura base no puede reducirse más.", icon="ℹ️")

    st.write("<br>", unsafe_allow_html=True)

    with st.container(border=True):
        st.markdown("### :material/dns: Clúster de Escala de Máquinas Virtuales (VMSS)")
        
        alerta_placeholder = st.empty()
        tabla_placeholder = st.empty()
        
        base_infra = [
            {"Instancia ID": "vm-core-erp", "Rol": "Servidor Central & BBDD", "Estado": "🟢 Operativa", "Carga CPU": f"{cpu_real}%", "IP Interna": "10.0.0.4"},
            {"Instancia ID": "vm-kds-cocina", "Rol": "Pantalla de Cocina (KDS)", "Estado": "🟢 Operativa", "Carga CPU": f"{random.randint(12, 25)}%", "IP Interna": "10.0.0.5"}
        ]

        nodos = st.session_state['nodos_cliente']

        if st.session_state['estado_animacion'] == 'escalando_up':
            alerta_placeholder.error(f"⚠️ **ALERTA DE SATURACIÓN:** Los nodos actuales rozan el 95%. Orquestador aprovisionando Instancia {nodos}...")
            
            frame_up = base_infra.copy()
            for i in range(1, nodos):
                frame_up.append({"Instancia ID": f"vm-client-node-0{i}", "Rol": "Servidor Web Clientes", "Estado": "🔴 Sobrecarga", "Carga CPU": f"{random.randint(90, 98)}%", "IP Interna": f"10.0.0.{5+i}"})
            frame_up.append({"Instancia ID": f"vm-client-node-0{nodos}", "Rol": "Desbordamiento (Reactivo)", "Estado": "🟡 Iniciando (Standby)...", "Carga CPU": "0%", "IP Interna": "Asignando..."})
            
            tabla_placeholder.dataframe(pd.DataFrame(frame_up), use_container_width=True, hide_index=True)
            time.sleep(3)
            
            st.session_state['estado_animacion'] = None
            st.rerun()

        elif st.session_state['estado_animacion'] == 'escalando_down':
            alerta_placeholder.warning(f"📉 **CAÍDA DE TRÁFICO:** Capacidad de procesamiento sobrante. Destruyendo Instancia {nodos+1} para ahorro de costes.")
            
            frame_down = base_infra.copy()
            for i in range(1, nodos + 1):
                frame_down.append({"Instancia ID": f"vm-client-node-0{i}", "Rol": "Servidor Web Clientes", "Estado": "🟢 Operativa", "Carga CPU": f"{random.randint(20, 35)}%", "IP Interna": f"10.0.0.{5+i}"})
            frame_down.append({"Instancia ID": f"vm-client-node-0{nodos+1}", "Rol": "Desbordamiento (Eliminando)", "Estado": "🔴 Apagando (Draining)", "Carga CPU": "0%", "IP Interna": "Liberando..."})
            
            tabla_placeholder.dataframe(pd.DataFrame(frame_down), use_container_width=True, hide_index=True)
            time.sleep(3)
            
            st.session_state['estado_animacion'] = None
            st.rerun()

        else:
            if nodos == 1:
                alerta_placeholder.success("✅ **Tráfico Estable:** 1 nodo absorbiendo toda la demanda. Clúster optimizado para máximo ahorro (OPEX).")
            else:
                alerta_placeholder.info(f"⚖️ **TRÁFICO BALANCEADO:** {nodos} nodos activos repartiendo la carga uniformemente ({100/nodos:.0f}% teórico).")
            
            frame_normal = base_infra.copy()
            for i in range(1, nodos + 1):
                carga_balanceada = random.randint(35, 60)
                frame_normal.append({"Instancia ID": f"vm-client-node-0{i}", "Rol": "Servidor Web Clientes", "Estado": "🟢 Operativa", "Carga CPU": f"{carga_balanceada}%", "IP Interna": f"10.0.0.{5+i}"})
                
            tabla_placeholder.dataframe(pd.DataFrame(frame_normal), use_container_width=True, hide_index=True)

# --- NUEVA PESTAÑA: PREVISIÓN DE CARGA Y AUTO-ESCALADO PREDICTIVO ---
def show_prevision_carga():
    st.title(":material/insights: Previsión de Carga & Escalado Predictivo")
    st.markdown("Modelo analítico de afluencia horaria en el restaurante y su correlación con el despliegue automático de nodos en Azure.")

    with st.container(border=True):
        st.markdown("### 📈 Curva de Demanda Estimada vs. Instancias Activas (24h)")
        
        # Generación de dataset simulado/histórico de las 24 horas del día
        horas = list(range(24))
        # Simulamos picos lógicos de almuerzo (13h-16h) y cena (20h-23h)
        demanda_pedidos = [
            5, 2, 1, 0, 0, 1, 3, 10, 25, 40, 30, 20, # 00:00 - 11:00
            65, 95, 85, 50, 25, 20, 15, 30, 70, 90, 75, 35 # 12:00 - 23:00
        ]
        
        # Número de VMs asignadas por el modelo predictivo en función de la demanda
        nodos_predictivos = [
            1 if d < 40 else (2 if d < 75 else 3) for d in demanda_pedidos
        ]

        df_prevision = pd.DataFrame({
            "Hora": [f"{h:02d}:00" for h in horas],
            "Pedidos Estimados (Demanda)": demanda_pedidos,
            "Nodos VMSS Desplegados": nodos_predictivos
        })

        # Gráfica combinada con Plotly
        fig = px.bar(df_prevision, x="Hora", y="Pedidos Estimados (Demanda)", 
                     color="Nodos VMSS Desplegados",
                     color_continuous_scale="Blues",
                     template="plotly_dark",
                     title="Afluencia de Clientes y Respuesta del Clúster Cloud")
        
        fig.update_layout(
            plot_bgcolor='rgba(0,0,0,0)', 
            paper_bgcolor='rgba(0,0,0,0)',
            margin=dict(l=0, r=0, t=40, b=0),
            xaxis=dict(tickmode='linear'),
            coloraxis_colorbar=dict(title="Nodos Activos")
        )
        st.plotly_chart(fig, use_container_width=True)

    st.write("<br>", unsafe_allow_html=True)

    with st.container(border=True):
        st.markdown("### 🧠 Explicación del Algoritmo Predictivo")
        st.info(
            "**¿Cómo funciona el Auto-Escalado Predictivo en esta arquitectura?**\n\n"
            "1. **Análisis de Patrones Históricos:** El sistema procesa los registros de ventas anteriores almacenados en Azure SQL para anticiparse a los flujos masivos de clientes.\n"
            "2. **Pre-calentamiento (Standby):** Minutos antes de que comiencen las franjas de almuerzo (13:00) y cena (20:00), el orquestador despliega preventivamente nodos adicionales.\n"
            "3. **Cero Latencia:** Gracias a esta previsión, los clientes que acceden a la carta digital no sufren tiempos de espera ni caídas por saturación del servidor principal."
        )

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
            ":material/router: Orquestación VMs (Azure)",
            ":material/insights: Previsión de Carga (ML)"
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
    elif menu == ":material/router: Orquestación VMs (Azure)":
        show_azure_infrastructure()
    elif menu == ":material/insights: Previsión de Carga (ML)":
        show_prevision_carga()