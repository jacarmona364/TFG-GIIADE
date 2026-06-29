# Automatización Inteligente de Recursos Cloud: Despliegue Dinámico de Máquinas Virtuales para la Mejora de la Eficiencia Productiva

Este repositorio contiene el desarrollo técnico del Trabajo Fin de Grado para la titulación de Ingeniería Informática (Especialidad en Tecnologías de la Información) de la Universidad de Granada.

## 🚀 Descripción del Proyecto
El proyecto consiste en el diseño e implementación de una arquitectura de servidores en la nube (Microsoft Azure) orientada a la ejecución de procesos empresariales. El núcleo tecnológico radica en un sistema de autogestión basado en Inteligencia Artificial que analiza métricas de rendimiento y telemetría de la infraestructura en tiempo real. 

Este modelo de IA toma decisiones autónomas para escalar, desplegar o suspender máquinas virtuales (Azure VMs) según la carga de trabajo demandada, optimizando los costes operativos (OPEX) y mejorando la eficiencia productiva.

## 🛠️ Arquitectura Tecnológica (Stack Propuesto)
*   **Cloud Provider:** Microsoft Azure (Azure Compute & Azure Monitor)
*   **Lenguaje Principal:** Python 3.10+
*   **SDK de Conexión:** `azure-mgmt-compute` y `azure-identity` (para la gestión del ciclo de vida de las VMs)
*   **Telemetría:** Azure Monitor API / Monitor Query SDK (para la extracción de métricas de CPU/RAM)
*   **Motor de IA:** (Por definir - p. ej., Redes Neuronales LSTM / Modelos Predictivos de Series Temporales)

## 📂 Estructura del Repositorio (Propuesta Inicial)
*   `/src/core/`: Modelo de Inteligencia Artificial y lógica predictiva.
*   `/src/azure_client/`: Scripts de conexión con la API de Azure (creación, parada y destrucción de recursos).
*   `/src/telemetry/`: Módulo encargado de recolectar las métricas de rendimiento en tiempo real.
*   `/infrastructure/`: Plantillas ARM o scripts de configuración para desplegar la infraestructura base.
*   `/docs/`: Documentación técnica complementaria y análisis económico-empresarial (ROI/OPEX).
