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
    cantidad = user_settings.get(user_id, 10)
    
    # Capturamos el texto completo del mensaje
    full_text = update.message.text
    
    # Eliminamos el comando (.gen o /gen) y nos quedamos con el resto
    # Esto evita que context.args falle si hay formatos extraños
    try:
        # Separamos por el primer espacio. Ejemplo: ".gen 1234xx" -> ["1234xx"]
        parts = full_text.split(maxsplit=1)
        
        if len(parts) < 2:
            await update.message.reply_text("❌ Debes proporcionar un BIN. Ej: `.gen 4567xxxxxxx`")
            return
        
        raw_data = parts[1].strip() # Aquí queda: "434256xxxxxxxxxx|mes|año|cvv"
        
        input_split = raw_data.split('|')
        bin_pattern = input_split[0].strip()
        mes = input_split[1] if len(input_split) > 1 and input_split[1] != "" else "rnd"
        ano = input_split[2] if len(input_split) > 2 and input_split[2] != "" else "rnd"
        cvv_in = input_split[3] if len(input_split) > 3 and input_split[3] != "" else "rnd"

    msg_espera = await update.message.reply_text("⏳ Generando...")
    
    resultados = []
    for _ in range(cantidad):
        num = generar_luhn_fuerza_bruta(bin_pattern)
        if num:
            red = chk_card(num)
            m = str(random.randint(1, 12)).zfill(2) if mes == "rnd" else mes.zfill(2)
            # Año: actual + random(2,6)
            a = str(datetime.now().year + random.randint(2, 6)) if ano == "rnd" else ano
            cvv = generar_cvv(red) if cvv_input == "rnd" else cvv_input
            resultados.append(f"`{num}|{m}|{a}|{cvv}`")

    if resultados:
        header = f"🔹 **BIN:** {bin_pattern}\n🔹 **Red:** {chk_card(bin_pattern)}\n🔹 **Cantidad:** {cantidad}\n\n"
        response = header + "\n".join(resultados)
        await msg_espera.edit_text(response, parse_mode='Markdown')
    else:
        await msg_espera.edit_text("❌ No se pudieron generar tarjetas válidas con ese BIN.")

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
