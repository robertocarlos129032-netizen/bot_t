import random
import logging
from datetime import datetime
from telegram import Update
from telegram.ext import ApplicationBuilder, ContextTypes, CommandHandler, MessageHandler, filters

# --- TU BASE DE DATOS DE BINS (Simplificada para el ejemplo) ---
BINS_DB = [
    ("4342xxxxxxxxxxxx", "Visa-N.C.M.B. / Nations Bank"),
    ("4xxxxxxxxxxxxxxx", "Visa"),
    ("5xxxxxxxxxxxxxxx", "MasterCard"),
    # ... puedes pegar aquí toda tu lista BINS_DB original ...
]

# --- LÓGICA DE GENERACIÓN (Tu código original adaptado) ---

def chk_card(numero):
    numero_limpio = ''.join(c for c in str(numero) if c.isdigit())
    for patron, red in BINS_DB:
        patron_limpio = ''.join(c for c in patron if c.isdigit() or c == 'x')
        if len(numero_limpio) < len(patron_limpio): continue
        comparar = numero_limpio[:len(patron_limpio)]
        match = True
        for a, p in zip(comparar, patron_limpio):
            if p != 'x' and a != p:
                match = False
                break
        if match: return red
    return "Unknown"

def luhn_valido(numero):
    digits = [int(d) for d in str(numero)]
    suma = 0
    par = len(digits) % 2 == 0
    for i, d in enumerate(digits):
        if (i % 2 == 0 and par) or (i % 2 != 0 and not par):
            d *= 2
            if d > 9: d -= 9
        suma += d
    return suma % 10 == 0

def generar_luhn_fuerza_bruta(bin_pattern, max_intentos=1000):
    for _ in range(max_intentos):
        res = ""
        for c in bin_pattern:
            res += str(random.randint(0, 9)) if c.lower() == 'x' else c
        if luhn_valido(res): return res
    return None

def generar_cvv(red):
    if "amex" in red.lower(): return str(random.randint(1000, 9998))
    return str(random.randint(112, 998))

# --- FUNCIONES DEL BOT ---

# Diccionario temporal para guardar la cantidad por usuario (default 10)
user_settings = {}

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Bot de Generación Activo.\nComandos:\n.cant [n]\n.gen bin|mes|año|cvv")

async def set_cant(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    try:
        # Tomar el argumento después de .cant
        nueva_cant = int(context.args[0])
        user_settings[user_id] = nueva_cant
        await update.message.reply_text(f"✅ Cantidad actualizada a: {nueva_cant}")
    except (IndexError, ValueError):
        await update.message.reply_text("❌ Uso correcto: `.cant 15`", parse_mode='Markdown')

async def gen_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    # Obtenemos la cantidad configurada por el usuario o 10 por defecto
    cantidad = user_settings.get(user_id, 10)
    
    # Obtenemos el texto completo del mensaje enviado
    full_text = update.message.text
    
    # Dividimos el mensaje: el primer elemento es el comando (.gen) 
    # y el segundo es todo lo que viene después (el BIN y los parámetros)
    parts = full_text.split(maxsplit=1)
    
    if len(parts) < 2:
        await update.message.reply_text("❌ Debes proporcionar un BIN.\nEjemplo: `.gen 4567xxxxxxx` o `.gen 4567xxxxxxx|05|2028|123`")
        return

    # Limpiamos los datos de entrada
    raw_data = parts[1].strip()
    
    # Separamos por el carácter "|"
    input_split = raw_data.split('|')
    
    # Asignación de valores (si no existen o están vacíos, se usa "rnd")
    bin_pattern = input_split[0].strip()
    mes = input_split[1].strip() if len(input_split) > 1 and input_split[1].strip() != "" else "rnd"
    ano = input_split[2].strip() if len(input_split) > 2 and input_split[2].strip() != "" else "rnd"
    cvv_in = input_split[3].strip() if len(input_split) > 3 and input_split[3].strip() != "" else "rnd"

    # Mensaje visual para indicar que el bot está trabajando
    msg_espera = await update.message.reply_text("⏳ Generando tarjetas válidas...")
    
    resultados = []
    for _ in range(cantidad):
        # IMPORTANTE: Asegúrate de que el nombre coincida con tu función: generar_luhn_fuerza_bruta
        num = generar_luhn_fuerza_bruta(bin_pattern)
        
        if num:
            red = chk_card(num)
            
            # Formatear Mes
            m = str(random.randint(1, 12)).zfill(2) if mes == "rnd" else mes.zfill(2)
            
            # Formatear Año (si es rnd, genera entre +2 y +6 años)
            if ano == "rnd":
                a = str(datetime.now().year + random.randint(2, 6))
            else:
                a = ano
                
            # Formatear CVV
            cvv = generar_cvv(red) if cvv_in == "rnd" else cvv_in
            
            # Guardamos en formato de código para que sea fácil de copiar en Telegram
            resultados.append(f"`{num}|{m}|{a}|{cvv}`")

    if resultados:
        # Detectar la red para mostrarla en el encabezado
        info_red = chk_card(bin_pattern)
        header = f"💳 **BIN:** `{bin_pattern}`\n🏦 **Red:** {info_red}\n🎲 **Cantidad:** {cantidad}\n\n"
        final_msg = header + "\n".join(resultados)
        
        await msg_espera.edit_text(final_msg, parse_mode='Markdown')
    else:
        await msg_espera.edit_text("❌ No se pudieron generar tarjetas. Verifica que el BIN sea válido o intenta con menos 'x'.")
        
if __name__ == '__main__':
    # Reemplaza 'TU_TOKEN_AQUÍ' por el token que te dio @BotFather
    app = ApplicationBuilder().token('8613878245:AAE8TDDKY5H1qCg6l5PsaP62ySvGROrZMGM').build()
    
    # Comandos con punto (.) o barra (/)
    app.add_handler(CommandHandler("cant", set_cant))
    app.add_handler(CommandHandler("gen", gen_handler))
    # Soporte para comandos que empiecen con punto de forma manual
    app.add_handler(MessageHandler(filters.Regex(r'^\.cant'), set_cant))
    app.add_handler(MessageHandler(filters.Regex(r'^\.gen'), gen_handler))
    app.add_handler(CommandHandler("start", start))

    print("Bot corriendo...")
    app.run_polling()
