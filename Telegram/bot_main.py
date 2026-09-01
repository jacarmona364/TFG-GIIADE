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

SQL_SERVER = os.getenv("AZURE_SQL_SERVER")
SQL_DATABASE = os.getenv("AZURE_SQL_DATABASE")
SQL_USER = os.getenv("AZURE_SQL_USER")
SQL_PASSWORD = os.getenv("AZURE_SQL_PASSWORD")

bot = telebot.TeleBot(TOKEN)

# Memoria temporal para productos desconocidos
productos_en_cuarentena = {}

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
    bot.reply_to(message, "¡Hola! Gestor de Mi Tosta operativo con Azure SQL y Cloud AI. Sube tu documento para almacenarlo en la base de datos.")

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
            
            # Extraer solo el valor numérico del total
            total_field = invoice.fields.get("InvoiceTotal")
            total_value = 0.0
            if total_field and total_field.value:
                total_value = getattr(total_field.value, 'amount', total_field.value)
            
            items_field = invoice.fields.get("Items")
            parsed_items = []
            
            if items_field and items_field.value:
                for idx, item in enumerate(items_field.value):
                    item_fields = item.value
                    description = item_fields.get("Description").value if item_fields.get("Description") else f"Artículo {idx+1}"
                    quantity = item_fields.get("Quantity").value if item_fields.get("Quantity") else 1.0
                    
                    # Extraer solo el valor numérico del precio unitario
                    price_field = item_fields.get("UnitPrice")
                    price = 0.0
                    if price_field and price_field.value:
                        price = getattr(price_field.value, 'amount', price_field.value)
                        
                    # Extraer solo el valor numérico del total de la línea
                    amount_field = item_fields.get("Amount")
                    total_price = (quantity * price)
                    if amount_field and amount_field.value:
                        total_price = getattr(amount_field.value, 'amount', amount_field.value)
                    
                    parsed_items.append({
                        "descripcion": description,
                        "cantidad": quantity,
                        "precio": price,
                        "total": total_price
                    })

            # 3. Guardar en Azure SQL Database con lógica de HOMOLOGACIÓN
            conn = get_sql_connection()
            cursor = conn.cursor()
            
            # Registrar asiento contable general de la factura (como gasto negativo)
            cursor.execute(
                "INSERT INTO asientos_contables (proveedor, total, fecha) VALUES (?, ?, GETDATE())",
                (f"Gasto: {vendor_value}", -abs(float(total_value)))
            )
            
            articulos_conocidos = []
            articulos_desconocidos = []

            # Clasificar los items: ¿Los conocemos o son nuevos?
            for itm in parsed_items:
                nombre_ocr = itm["descripcion"]
                
                # 3.1 Buscar en el diccionario de equivalencias
                cursor.execute("SELECT nombre_inventario, factor_conversion FROM equivalencias_proveedor WHERE LOWER(nombre_factura) = LOWER(?)", (nombre_ocr,))
                equivalencia = cursor.fetchone()
                
                if equivalencia:
                    nombre_real = equivalencia[0]
                    cantidad_real = itm["cantidad"] * equivalencia[1]
                    articulos_conocidos.append((nombre_real, cantidad_real, itm["precio"]))
                else:
                    # 3.2 Comprobar si el nombre coincide exactamente con la descripción o producto por casualidad
                    cursor.execute("SELECT producto FROM inventario WHERE LOWER(producto) = LOWER(?) OR LOWER(descripcion) = LOWER(?)", (nombre_ocr, nombre_ocr))
                    si_existe = cursor.fetchone()
                    if si_existe:
                        articulos_conocidos.append((si_existe[0], itm["cantidad"], itm["precio"]))
                        # Lo guardamos en el diccionario para que el cruce sea directo la próxima vez
                        cursor.execute("INSERT INTO equivalencias_proveedor (nombre_factura, nombre_inventario) VALUES (?, ?)", (nombre_ocr, si_existe[0]))
                    else:
                        articulos_desconocidos.append(itm)

            # 3.3 Actualizar inventario SOLO con los artículos conocidos (agrupando por la columna 'producto')
            for nombre, cant, precio in articulos_conocidos:
                cursor.execute(
                    """
                    IF EXISTS (SELECT 1 FROM inventario WHERE LOWER(producto) = LOWER(?))
                        UPDATE inventario SET stock = stock + ?, precio_unitario = ? WHERE LOWER(producto) = LOWER(?)
                    ELSE
                        INSERT INTO inventario (producto, descripcion, stock, precio_unitario) VALUES (?, ?, ?, ?)
                    """,
                    (nombre, cant, precio, nombre, nombre, nombre, cant, precio)
                )
            
            conn.commit()
            cursor.close()
            conn.close()

            # 4. Respuesta por Telegram de lo procesado automáticamente
            response_text = f"✅ **Factura procesada y guardada en Azure**\n\n" \
                            f"🏢 **Proveedor:** {vendor_value}\n" \
                            f"💰 **Total:** -{abs(float(total_value))} €\n\n" \
                            f"📦 **Inventario actualizado automáticamente ({len(articulos_conocidos)} items):**\n"
            
            for nombre, cant, precio in articulos_conocidos:
                response_text += f"- {cant}x {nombre}\n"
                
            bot.reply_to(message, response_text, parse_mode="Markdown")
            
            # 5. Activar el sistema de aprendizaje para los desconocidos
            if articulos_desconocidos:
                chat_id = message.chat.id
                productos_en_cuarentena[chat_id] = articulos_desconocidos
                procesar_siguiente_cuarentena(chat_id)
                
            return
            
        bot.reply_to(message, f"Archivo guardado en Azure como '{file_name}', pero sin estructura de factura válida.")
        
    except Exception as e:
        bot.reply_to(message, f"Error al procesar y registrar la factura: {e}")

# --- SISTEMA DE CUARENTENA INTERACTIVO CON BOTONES ---

def procesar_siguiente_cuarentena(chat_id):
    lista_pendientes = productos_en_cuarentena.get(chat_id, [])
    if not lista_pendientes:
        bot.send_message(chat_id, "🎉 Todos los productos de la factura han sido mapeados y guardados.")
        return

    siguiente_item = lista_pendientes[0]
    
    try:
        conn = get_sql_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT DISTINCT producto FROM inventario ORDER BY producto ASC")
        filas = cursor.fetchall()
        cursor.close()
        conn.close()
        
        markup = telebot.types.InlineKeyboardMarkup(row_width=2)
        botones = []
        for fila in filas:
            nombre_gen = fila[0]
            botones.append(telebot.types.InlineKeyboardButton(text=nombre_gen, callback_data=f"map_{nombre_gen}"))
        
        markup.add(*botones)
        markup.add(telebot.types.InlineKeyboardButton(text="🚫 Ignorar este producto", callback_data="map_ignorar"))

        bot.send_message(
            chat_id, 
            f"⚠️ **Nuevo producto detectado en la factura:**\n"
            f"🧾 Nombre original: `{siguiente_item['descripcion']}`\n"
            f"⚖️ Cantidad: {siguiente_item['cantidad']} | 💶 Precio: {siguiente_item['precio']}€\n\n"
            f"¿Con qué producto del inventario se corresponde?",
            reply_markup=markup,
            parse_mode="Markdown"
        )
    except Exception as e:
        bot.send_message(chat_id, f"❌ Error al cargar opciones de inventario: {e}")

@bot.callback_query_handler(func=lambda call: call.data.startswith('map_'))
def callback_mapeo(call):
    chat_id = call.message.chat.id
    lista_pendientes = productos_en_cuarentena.get(chat_id, [])
    
    if not lista_pendientes:
        bot.answer_callback_query(call.id, "No hay pendientes.")
        return

    siguiente_item = lista_pendientes[0]
    seleccion = call.data.replace('map_', '')

    bot.answer_callback_query(call.id, f"Seleccionado: {seleccion}")

    if seleccion != 'ignorar':
        try:
            conn = get_sql_connection()
            cursor = conn.cursor()
            
            # Guardar la equivalencia para futuras facturas
            cursor.execute(
                "INSERT INTO equivalencias_proveedor (nombre_factura, nombre_inventario) VALUES (?, ?)", 
                (siguiente_item['descripcion'], seleccion)
            )
            
            # Actualizar el stock sumándolo al producto del inventario seleccionado
            cursor.execute(
                """
                UPDATE inventario 
                SET stock = stock + ?, precio_unitario = ? 
                WHERE producto = ?
                """,
                (siguiente_item['cantidad'], siguiente_item['precio'], seleccion)
            )
            
            conn.commit()
            cursor.close()
            conn.close()
            
            bot.edit_message_text(
                chat_id=chat_id,
                message_id=call.message.message_id,
                text=f"✅ Vinculado con éxito:\n`{siguiente_item['descripcion']}` ➔ **{seleccion}**\n¡Guardado en el inventario!",
                parse_mode="Markdown"
            )
        except Exception as e:
            bot.send_message(chat_id, f"❌ Error al aplicar el mapeo en base de datos: {e}")
    else:
        bot.edit_message_text(
            chat_id=chat_id,
            message_id=call.message.message_id,
            text=f"🚫 Producto `{siguiente_item['descripcion']}` ignorado.",
            parse_mode="Markdown"
        )

    # Eliminar el item procesado y continuar con el siguiente de la cuarentena
    productos_en_cuarentena[chat_id].pop(0)
    procesar_siguiente_cuarentena(chat_id)

if __name__ == '__main__':
    print("Bot avanzado con Azure SQL activo...")
    bot.infinity_polling()