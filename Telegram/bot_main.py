import os
import telebot
from dotenv import load_dotenv
from azure.storage.blob import BlobServiceClient

load_dotenv()
TOKEN = os.getenv("TELEGRAM_TOKEN")
AZURE_CONN_STR = os.getenv("AZURE_STORAGE_CONNECTION_STRING")

bot = telebot.TeleBot(TOKEN)
blob_service_client = BlobServiceClient.from_connection_string(AZURE_CONN_STR)
container_name = "facturas"

@bot.message_handler(commands=['start'])
def send_welcome(message):
    bot.reply_to(message, "¡Hola! Soy el gestor de Mi Tosta. Envíame la foto de una factura y la subiré a la nube.")

@bot.message_handler(content_types=['photo', 'document'])
def handle_file(message):
    bot.reply_to(message, "Archivo detectado. Procesando y subiendo a Azure...")
    
    try:
        # 1. Identificar el tipo de archivo y extraer el ID y su extensión
        if message.content_type == 'photo':
            file_id = message.photo[-1].file_id
            extension = ".jpg"
        elif message.content_type == 'document':
            # Validar que el documento sea estrictamente un PDF
            if message.document.mime_type != 'application/pdf':
                bot.reply_to(message, "Formato no válido. Por favor, envía solo fotos o PDFs.")
                return
            file_id = message.document.file_id
            extension = ".pdf"
            
        # 2. Descargar desde los servidores de Telegram
        file_info = bot.get_file(file_id)
        downloaded_file = bot.download_file(file_info.file_path)
        
        # 3. Generar nombre dinámico
        file_name = f"factura_{message.message_id}{extension}"
        
        # 4. Conectar y subir a Azure Blob Storage
        blob_client = blob_service_client.get_blob_client(container=container_name, blob=file_name)
        blob_client.upload_blob(downloaded_file, overwrite=True)
        
        bot.reply_to(message, f"¡Éxito! Archivo guardado en Azure como '{file_name}'.")
        
    except Exception as e:
        bot.reply_to(message, f"Error al procesar el archivo: {e}")

if __name__ == '__main__':
    print("Bot de Mi Tosta iniciado. Esperando facturas...")
    bot.infinity_polling()