import os
import random
import logging
from datetime import datetime
from flask import Flask
from threading import Thread
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes

# --- LÓGICA DE GEN_JS.PY (Mantenida intacta) ---
BINS_DB = [
    ("37xxxxxxxxxxxxx",  "AmEx"), ("3782xxxxxxxxxx", "AmEx Small Corporate"),
    ("4048xxxxxxxxxxxx", "Visa CV"), ("4xxxxxxxxxxxxxx", "Visa"),
    ("5xxxxxxxxxxxxxxx", "MasterCard/Access/Eurocard"), ("60xxxxxxxxxxxxxx", "Discover"),
    # ... (He resumido aquí para ahorrar espacio, pero usa tu lista completa)
]

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

def generar_luhn_fuerza_bruta(bin_pattern):
    for _ in range(1000):
        numero = "".join(str(random.randint(0, 9)) if c.lower() == 'x' else c for c in bin_pattern)
        if luhn_valido(numero): return numero
    return None

def generar_cvv(red):
    if "amex" in red.lower(): return str(random.randint(1000, 9998))
    return str(random.randint(112, 998))

# --- GESTIÓN DE ESTADO ---
user_config = {} # {user_id: {'cantidad': 10, 'lista': []}}

# --- FUNCIONES DEL BOT ---

async def get_user_data(user_id):
    if user_id not in user_config:
        user_config[user_id] = {'cantidad': 10, 'lista': []}
    return user_config[user_id]

async def cmd_cant(update: Update, context: ContextTypes.DEFAULT_TYPE):
    data = await get_user_data(update.effective_user.id)
    try:
        nueva_cant = int(context.args[0])
        data['cantidad'] = nueva_cant
        await update.message.reply_text(f"✅ Cantidad actualizada a: {nueva_cant}")
    except:
        await update.message.reply_text("❌ Uso: .cant [numero]")

def procesar_gen(input_str, cantidad):
    parts = input_str.split('|')
    bin_p = parts[0]
    mes = parts[1] if len(parts) > 1 else "rnd"
    ano = parts[2] if len(parts) > 2 else "rnd"
    cvv_input = parts[3] if len(parts) > 3 else "rnd"
    
    res = []
    for _ in range(cantidad):
        num = generar_luhn_fuerza_bruta(bin_p)
        if num:
            red = chk_card(num)
            m = str(random.randint(1, 12)).zfill(2) if mes == "rnd" else mes.zfill(2)
            a = str(datetime.now().year + random.randint(2, 6)) if ano == "rnd" else ano
            c = generar_cvv(red) if cvv_input == "rnd" else cvv_input
            res.append(f"<code>{num}|{m}|{a}|{c}</code>")
    
    header = f"<b>BIN:</b> {bin_p}\n<b>Red:</b> {chk_card(bin_p.replace('x','0'))}\n\n"
    return header + "\n".join(res)

async def cmd_gen(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args: return
    data = await get_user_data(update.effective_user.id)
    texto = procesar_gen(context.args[0], data['cantidad'])
    await update.message.reply_html(texto)

async def cmd_ggen(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args: return
    data = await get_user_data(update.effective_user.id)
    entrada = context.args[0]
    data['lista'].append(entrada)
    # Ejecuta directamente .gen
    texto = procesar_gen(entrada, data['cantidad'])
    await update.message.reply_html(f"📌 <b>Guardado en posición {len(data['lista'])}</b>\n\n{texto}")

async def cmd_rep(update: Update, context: ContextTypes.DEFAULT_TYPE):
    data = await get_user_data(update.effective_user.id)
    if not context.args:
        if not data['lista']: return await update.message.reply_text("Lista vacía.")
        msg = "\n".join([f"{i+1}. {item}" for i, item in enumerate(data['lista'])])
        return await update.message.reply_text(f"📋 Lista guardada:\n{msg}")
    
    try:
        idx = int(context.args[0]) - 1
        texto = procesar_gen(data['lista'][idx], data['cantidad'])
        await update.message.reply_html(texto)
    except:
        await update.message.reply_text("❌ Índice no válido.")

async def cmd_repu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    data = await get_user_data(update.effective_user.id)
    if not data['lista']: return await update.message.reply_text("No hay tarjetas guardadas.")
    texto = procesar_gen(data['lista'][-1], data['cantidad'])
    await update.message.reply_html(texto)

async def cmd_dep(update: Update, context: ContextTypes.DEFAULT_TYPE):
    data = await get_user_data(update.effective_user.id)
    try:
        idx = int(context.args[0]) - 1
        del data['lista'][idx]
        await update.message.reply_text(f"🗑 Eliminado. Lista reordenada.")
    except:
        await update.message.reply_text("❌ Uso: .dep [indice]")

# --- CONFIGURACIÓN PARA RENDER ---
app_flask = Flask('')
@app_flask.route('/')
def home(): return "Bot is Alive"

def run_flask():
    app_flask.run(host='0.0.0.0', port=int(os.environ.get('PORT', 8080)))

if __name__ == '__main__':
    # Hilo para que Render no cierre el puerto
    Thread(target=run_flask).start()
    
    # Reemplaza con tu TOKEN
    TOKEN = "8613878245:AAE8TDDKY5H1qCg6l5PsaP62ySvGROrZMGM"
    
    bot = ApplicationBuilder().token(TOKEN).build()
    
    # Handlers con prefijo "."
    bot.add_handler(CommandHandler("cant", cmd_cant))
    bot.add_handler(CommandHandler("gen", cmd_gen))
    bot.add_handler(CommandHandler("ggen", cmd_ggen))
    bot.add_handler(CommandHandler("rep", cmd_rep))
    bot.add_handler(CommandHandler("repu", cmd_repu))
    bot.add_handler(CommandHandler("dep", cmd_dep))
    
    print("Bot activo")
    bot.run_polling()
