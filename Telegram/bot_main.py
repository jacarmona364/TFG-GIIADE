import os
import telebot
import pyodbc
from dotenv import load_dotenv
from azure.storage.blob import BlobServiceClient
from azure.ai.formrecognizer import DocumentAnalysisClient
from azure.core.credentials import AzureKeyCredential

load_dotenv()
TOKEN = os.getenv("TELEGRAM_TOKEN")
AZURE_CONN_STR = os.getenv("AZURE_STORAGE_CONNECTION_STRING")
AI_ENDPOINT = os.getenv("AZURE_AI_ENDPOINT")
AI_KEY = os.getenv("AZURE_AI_KEY")

# Credenciales de Azure SQL Database (las añadiremos al .env)
SQL_SERVER = os.getenv("AZURE_SQL_SERVER")
SQL_DATABASE = os.getenv("AZURE_SQL_DATABASE")
SQL_USER = os.getenv("AZURE_SQL_USER")
SQL_PASSWORD = os.getenv("AZURE_SQL_PASSWORD")

bot = telebot.TeleBot(TOKEN)
blob_service_client = BlobServiceClient.from_connection_string(AZURE_CONN_STR)
document_analysis_client = DocumentAnalysisClient(
    endpoint=AI_ENDPOINT, credential=AzureKeyCredential(AI_KEY)
)
container_name = "facturas"

def get_sql_connection():
    connection_string = (
        f"DRIVER={{ODBC Driver 18 for SQL Server}};"
        f"SERVER={SQL_SERVER};"
        f"DATABASE={SQL_DATABASE};"
        f"UID={SQL_USER};"
        f"PWD={SQL_PASSWORD};"
        f"Encrypt=yes;TrustServerCertificate=no;Connection Timeout=30;"
    )
    return pyodbc.connect(connection_string)

@bot.message_handler(commands=['start'])
def send_welcome(message):
    bot.reply_to(message, "¡Hola! Gestor de Mi Tosta operativo con Azure SQL y Cloud AI.")

@bot.message_handler(content_types=['photo', 'document'])
def handle_file(message):
    bot.reply_to(message, "Procesando documento, actualizando inventario y contabilidad en Azure...")
    
    try:
        if message.content_type == 'photo':
            file_id = message.photo[-1].file_id
            extension = ".jpg"
        elif message.content_type == 'document':
            if message.document.mime_type != 'application/pdf':
                bot.reply_to(message, "Formato no válido. Envía solo fotos o PDFs.")
                return
            file_id = message.document.file_id
            extension = ".pdf"
            
        file_info = bot.get_file(file_id)
        downloaded_file = bot.download_file(file_info.file_path)
        file_name = f"factura_{message.message_id}{extension}"
        
        # 1. Subir a Azure Blob Storage
        blob_client = blob_service_client.get_blob_client(container=container_name, blob=file_name)
        blob_client.upload_blob(downloaded_file, overwrite=True)
        
        # 2. Análisis con Azure Document Intelligence
        poller = document_analysis_client.begin_analyze_document(
            "prebuilt-invoice", downloaded_file
        )
        result = poller.result()
        
        for invoice in result.documents:
            vendor_name = invoice.fields.get("VendorName")
            vendor_value = vendor_name.value if vendor_name else "Proveedor Desconocido"
            
            total_field = invoice.fields.get("InvoiceTotal")
            total_value = total_field.value if total_field else 0.0
            
            items_field = invoice.fields.get("Items")
            parsed_items = []
            
            if items_field and items_field.value:
                for idx, item in enumerate(items_field.value):
                    item_fields = item.value
                    description = item_fields.get("Description").value if item_fields.get("Description") else f"Artículo {idx+1}"
                    quantity = item_fields.get("Quantity").value if item_fields.get("Quantity") else 1.0
                    price = item_fields.get("UnitPrice").value if item_fields.get("UnitPrice") else 0.0
                    total_price = item_fields.get("Amount").value if item_fields.get("Amount") else (quantity * price)
                    
                    parsed_items.append({
                        "descripcion": description,
                        "cantidad": quantity,
                        "precio": price,
                        "total": total_price
                    })

            # 3. Guardar en Azure SQL Database
            conn = get_sql_connection()
            cursor = conn.cursor()
            
            # Registrar asiento contable general de la factura
            cursor.execute(
                "INSERT INTO asientos_contables (proveedor, total, fecha) VALUES (?, ?, GETDATE())",
                (vendor_value, total_value)
            )
            
            # Actualizar inventario por cada ítem detectado
            for itm in parsed_items:
                cursor.execute(
                    """
                    IF EXISTS (SELECT * FROM inventario WHERE descripcion = ?)
                        UPDATE inventario SET stock = stock + ?, precio_unitario = ? WHERE descripcion = ?
                    ELSE
                        INSERT INTO inventario (descripcion, stock, precio_unitario) VALUES (?, ?, ?)
                    """,
                    (itm["descripcion"], itm["cantidad"], itm["precio"], itm["descripcion"],
                     itm["descripcion"], itm["cantidad"], itm["precio"])
                )
            
            conn.commit()
            cursor.close()
            conn.close()

            # 4. Respuesta por Telegram
            response_text = f"✅ **Factura procesada y guardada en Azure**\n\n" \
                            f"🏢 **Proveedor:** {vendor_value}\n" \
                            f"💰 **Total:** {total_value} €\n\n" \
                            f"📦 **Inventario y Contabilidad actualizados:**\n"
            
            for itm in parsed_items:
                response_text += f"- {itm['cantidad']}x {itm['descripcion']} ({itm['total']} €)\n"
                
            bot.reply_to(message, response_text, parse_mode="Markdown")
            return
            
        bot.reply_to(message, f"Archivo guardado en Azure como '{file_name}', pero sin estructura de factura válida.")
        
    except Exception as e:
        bot.reply_to(message, f"Error al procesar y registrar la factura: {e}")

if __name__ == '__main__':
    print("Bot avanzado con Azure SQL activo...")
    bot.infinity_polling()