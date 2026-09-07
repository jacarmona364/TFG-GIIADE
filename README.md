# Automatización Inteligente de Recursos Cloud para la Mejora de la Eficiencia Productiva
> **Ecosistema integral de monitorización y despliegue dinámico para la optimización de procesos empresariales.**

Este repositorio contiene el código fuente y la arquitectura de despliegue del Trabajo Fin de Grado para el Doble Grado en Ingeniería Informática y Administración y Dirección de Empresas (Universidad de Granada).

---

## 🚀 Descripción del Proyecto

El proyecto fusiona la Ingeniería de Sistemas con la Dirección Estratégica para resolver ineficiencias estructurales en las PYMES del sector HORECA (caso de estudio empírico: *Mi Tosta*). El núcleo tecnológico plantea una transición desde modelos de infraestructura On-Premise (altos costes de CAPEX) hacia una **arquitectura Cloud asimétrica y elástica** en Microsoft Azure.

Mediante orquestación inteligente (pago por uso o modelo OPEX), el sistema adapta su consumo computacional milimétricamente a la volatilidad de la demanda en tiempo real. 

### ✨ Funcionalidades Principales
* **Auto-escalado Dinámico:** Orquestación reactiva y predictiva de servidores (VMSS) para absorber picos de demanda sin interrupción de servicio (*Zero-Downtime*).
* **Hiperautomatización Logística (Bot OCR):** Agente conversacional asíncrono que digitaliza albaranes y facturas mediante IA (Deep Learning y NLP), normaliza inventarios y almacena copias inmutables en la nube.
* **Cuadro de Mando Integral (KDS y Dashboard):** Ecosistema de interfaces interactivas para la gestión operativa en cocina y la telemetría IT/financiera para gerencia.

---

## ⚙️ Arquitectura Tecnológica (Stack Final)

El ecosistema se despliega en **Microsoft Azure** segmentando responsabilidades entre modelos IaaS y PaaS:

* **Lenguaje Principal:** Python 3.9+
* **Computación (IaaS):** Azure Virtual Machines (VM B2s) y Virtual Machine Scale Sets (VMSS).
* **Servicios Cognitivos y Datos (PaaS):** 
  * Azure AI Document Intelligence (Extracción OCR).
  * Azure SQL Database (Persistencia relacional de inventario y operativa).
  * Azure Blob Storage (Almacenamiento de imágenes).
* **Interfaces y Visualización:** Streamlit, Plotly, Telegram Bot API.
* **Telemetría y Control:** `psutil`, `pyodbc`, simulador interactivo de estrés (*Gemelo Digital*).

---

## 📂 Estructura del Repositorio

La arquitectura del software está modularizada para garantizar el aislamiento de dependencias:

* `/Dashboard/`: Interfaz analítica para la gerencia (`app_analitica.py`), panel interactivo de producción (`app_cocina.py`) e interfaz de toma de demanda (`app_cliente.py`).
* `/Telegram/`: Orquestador conversacional (`bot_main.py`) encargado de la ingesta de imágenes y comunicación con la API Cognitiva.
* Archivos `.service` nativos de Linux para la ejecución de los módulos en segundo plano (*daemons*).

---

## 🛠️ Despliegue y Ejecución Local

Para reproducir o auditar el entorno tecnológico en local, se requiere **Python 3.9 o superior**.

**1. Clonar el repositorio**
```bash
git clone [https://github.com/tu-usuario/TFG-GIIADE.git](https://github.com/tu-usuario/TFG-GIIADE.git)
cd TFG-GIIADE
