import os
import random
import logging
import math
from datetime import datetime
from itertools import permutations
from collections import Counter
from telegram import Update
from telegram.ext import ApplicationBuilder, ContextTypes, CommandHandler, MessageHandler, filters

# Configuración de Logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

async def error_handler(update, context):
    logging.error("Exception while handling an update:", exc_info=context.error)

# --- BASE DE DATOS DE BINS ---
BINS_DB = [
    ("37xxxxxxxxxxxxx",  "AmEx"),
    ("4xxxxxxxxxxxxxx", "Visa"),
    ("5xxxxxxxxxxxxxxx", "MasterCard/Access/Eurocard"),
    ("60xxxxxxxxxxxxxx", "Discover"),
]

# --- LÓGICA DE APOYO (ORIGINAL) ---

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

# --- LÓGICA DE EXTRACCIÓN (XTP) ---

def calcular_logicas(cc1, cc2):
    # --- Lógica XTP 1 ---
    cc_edit = []
    for x in [cc1, cc2]:
        lista = list(x)
        for i in range(len(lista)):
            if not (i < 8 or i in (10, 11)):
                lista[i] = "x"
        cc_edit.append("".join(lista))

    res1 = 0
    for y in range(2):
        v1 = int(cc_edit[0][10+y])
        v2 = int(cc_edit[1][10+y])
        res1 += math.floor(((v1 + v2) / 2) * 5)

    xtp1 = str(cc_edit[0])[:8] + str(res1)
    xtp1 = xtp1 + ('x' * (len(cc1) - len(xtp1)))

    # --- Lógica XTP 2 ---
    try:
        res_list = [int(a) * int(b) for a, b in zip(cc2[8:], cc2[:8])]
        res2_str = "".join(str(x) for x in res_list)
        cc2_fake = cc2[:8] + res2_str[:8]
        
        xtp2_list = [None] * len(cc1)
        for i in range(len(cc1)):
            if i < len(cc2_fake) and cc1[i] == cc2_fake[i]:
                xtp2_list[i] = cc2_fake[i]
            else:
                xtp2_list[i] = 'x'
        xtp2 = "".join(xtp2_list)
    except:
        xtp2 = "Error_en_calculo"
    
    return xtp1, xtp2

# --- VARIABLES DE ESTADO ---
user_settings = {}
user_history = {}

# --- PROCESADORES CENTRALES ---

async def ejecutar_generacion(update: Update, context: ContextTypes.DEFAULT_TYPE, raw_data: str):
    user_id = update.effective_user.id
    cantidad = user_settings.get(user_id, 10)
    
    input_split = raw_data.split('|')
    bin_pattern = input_split[0].strip()
    mes = input_split[1].strip() if len(input_split) > 1 and input_split[1].strip() != "" else "rnd"
    ano = input_split[2].strip() if len(input_split) > 2 and input_split[2].strip() != "" else "rnd"
    cvv_in = input_split[3].strip() if len(input_split) > 3 and input_split[3].strip() != "" else "rnd"

    msg_espera = await update.message.reply_text("⏳ Generando...")
    
    resultados = []
    for _ in range(cantidad):
        num = generar_luhn_fuerza_bruta(bin_pattern)
        if num:
            red = chk_card(num)
            m = str(random.randint(1, 12)).zfill(2) if mes == "rnd" else mes.zfill(2)
            a = str(datetime.now().year + random.randint(2, 6)) if ano == "rnd" else ano
            cvv = generar_cvv(red) if cvv_in == "rnd" else cvv_in
            resultados.append(f"`{num}|{m}|{a}|{cvv}`")

    if resultados:
        info_red = chk_card(bin_pattern)
        header = f"💳 **BIN:** `{bin_pattern}`\n🏦 **Red:** {info_red}\n🎲 **Cant:** {cantidad}\n\n"
        await msg_espera.edit_text(header + "\n".join(resultados), parse_mode='Markdown')
    else:
        await msg_espera.edit_text("❌ No se pudieron generar tarjetas.")

# --- HANDLERS ---

async def xtr_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    raw_text = update.message.text
    # Extraer solo los números de 15 o 16 dígitos (posibles tarjetas)
    import re
    # Buscamos bloques de números largos (ignorando separadores | / etc)
    all_numbers = re.findall(r'\b\d{15,16}\b', raw_text)
    
    if len(all_numbers) < 2:
        await update.message.reply_text("❌ Se requieren al menos 2 tarjetas para extraer.")
        return

    msg_espera = await update.message.reply_text(f"🔍 Analizando {len(all_numbers)} CCs...")
    
    resultados_xtp1 = []
    resultados_xtp2 = []
    origen_xtp1 = {}
    origen_xtp2 = {}

    combinaciones = list(permutations(all_numbers, 2))

    for c1, c2 in combinaciones:
        x1, x2 = calcular_logicas(c1, c2)
        
        resultados_xtp1.append(x1)
        if x1 not in origen_xtp1: origen_xtp1[x1] = (c1, c2)
            
        resultados_xtp2.append(x2)
        if x2 not in origen_xtp2: origen_xtp2[x2] = (c1, c2)

    def build_top_text(titulo, emoji, lista_res, mapa_origen):
        conteo = Counter(lista_res)
        tops = conteo.most_common(10)
        txt = f"{emoji} **{titulo}**\n`RESULTADO           | REP | GEN` \n"
        for res, veces in tops:
            c1, c2 = mapa_origen.get(res)
            # Acortar origen para que quepa en pantalla de Telegram
            txt += f"`{res:<18} | {veces:<3} | {c1[-4:]}&{c2[-4:]}`\n"
        return txt

    res_final = f"🧪 **EXTRACCIÓN COMPLETADA**\n"
    res_final += f"Permutaciones: {len(combinaciones)}\n\n"
    res_final += build_top_text("RANKING XTP 1", "🟦", resultados_xtp1, origen_xtp1)
    res_final += "\n" + build_top_text("RANKING XTP 2", "🟩", resultados_xtp2, origen_xtp2)

    await msg_espera.edit_text(res_final, parse_mode='Markdown')

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("🤖 Bot Activo.\nComandos: `.gen`, `.ggen`, `.rep`, `.repu`, `.cant`, `.xtr`, `.dep`.")

async def set_cant(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    try:
        parts = update.message.text.split()
        nueva_cant = int(parts[1])
        user_settings[user_id] = nueva_cant
        await update.message.reply_text(f"✅ Cantidad: **{nueva_cant}**", parse_mode='Markdown')
    except:
        await update.message.reply_text("❌ Uso: `.cant 15`")

async def gen_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    parts = update.message.text.split(maxsplit=1)
    if len(parts) < 2: return
    await ejecutar_generacion(update, context, parts[1])

async def ggen_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    parts = update.message.text.split(maxsplit=1)
    if len(parts) < 2: return
    pattern = parts[1].strip()
    user_history.setdefault(user_id, []).append(pattern)
    await update.message.reply_text(f"📥 Guardado en #{len(user_history[user_id])}")
    await ejecutar_generacion(update, context, pattern)

async def rep_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    history = user_history.get(user_id, [])
    parts = update.message.text.split()

    if not history:
        await update.message.reply_text("❌ Historial vacío.")
        return

    if len(parts) == 1:
        lista = [f"{i+1}. `{p}`" for i, p in enumerate(history)]
        await update.message.reply_text("🗂 **Historial:**\n" + "\n".join(lista), parse_mode='Markdown')
    else:
        try:
            idx = int(parts[1]) - 1
            await ejecutar_generacion(update, context, history[idx])
        except:
            await update.message.reply_text("❌ Índice inválido.")

async def repu_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    history = user_history.get(user_id, [])
    if not history:
        await update.message.reply_text("❌ Nada guardado.")
        return
    await ejecutar_generacion(update, context, history[-1])

async def dep_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    parts = update.message.text.split()
    try:
        idx = int(parts[1]) - 1
        eliminado = user_history[user_id].pop(idx)
        await update.message.reply_text(f"🗑 Eliminado: `{eliminado}`")
    except:
        await update.message.reply_text("❌ Error al eliminar.")

# Lista de links que quieres mostrar
LINKS = [
    "https://asociar.qzz.io/",
    "https://elit3signal.com/",
    "https://shop.nirvana.com/checkouts/cn/hWN79ih1uiCkeTLcld2Nd6yf/en-mx?_r=AQABwKyHwhFXNqz_h10JDN_NX6EH0exGABf7K8JWjjZMGqs&auto_redirect=false&edge_redirect=true&skip_shop_pay=true",
    "https://www.gardenweasel.com/checkouts/cn/hWN8konY7ytgeNEMm9Itx1l3/en-us?_r=AQABEqtN8qEpBNMN0upFoVlprgfgf3ZIjAewF-t5rWnpPlE&skip_shop_pay=true"
]

async def send_links(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message.text == ".lnk":
        links_text = "\n".join(LINKS)
        await update.message.reply_text(
            f"🔗 Aquí tienes los links:\n\n{links_text}"
        )
if __name__ == '__main__':
    # Reemplaza con tu TOKEN real
    TOKEN = "8613878245:AAGvV4lcztveZGwZ-iMIWEcgZ8sc2dzdSCY"
    app = ApplicationBuilder().token(TOKEN).build()
    
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.Regex(r'^[./]repu'), repu_handler))
    app.add_handler(MessageHandler(filters.Regex(r'^[./]rep'), rep_handler))
    app.add_handler(MessageHandler(filters.Regex(r'^[./]cant'), set_cant))
    app.add_handler(MessageHandler(filters.Regex(r'^[./]gen'), gen_handler))
    app.add_handler(MessageHandler(filters.Regex(r'^[./]ggen'), ggen_handler))
    app.add_handler(MessageHandler(filters.Regex(r'^[./]xtr'), xtr_handler))
    app.add_handler(MessageHandler(filters.Regex(r'^[./]dep'), dep_handler))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, send_links))
    app.add_error_handler(error_handler)
    
    print("Bot ACTIVO")
    app.run_polling()
