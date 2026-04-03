import sys
sys.stdout.reconfigure(encoding='utf-8')
import asyncio
import logging
import os
from aiogram import Bot, Dispatcher, F
from aiogram.types import (
    Message, CallbackQuery,
    ReplyKeyboardMarkup, KeyboardButton,
    InlineKeyboardMarkup, InlineKeyboardButton,
    InputMediaPhoto
)
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.filters import CommandStart

BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN", "8736560386:AAHgOAW2vK2kf_3TfV5_Tli_h0GRilQ8s5o")
CHANNEL = "@TOLOVLARKIRITISHUCHUNTEST"
PAROL = "credomarket0105"

logging.basicConfig(level=logging.INFO)
bot = Bot(token=BOT_TOKEN)
dp = Dispatcher(storage=MemoryStorage())

user_phones = {}
user_kurs = {}
authenticated = set()

# =====================
# STATES
# =====================
class S(StatesGroup):
    parol = State()
    kurs_birinchi = State()
    kurs_yangi = State()
    mijoz = State()
    summa = State()
    tolov_turi = State()
    karta_summa = State()
    naqd_usd = State()
    naqd_uzs = State()
    chek = State()
    finish = State()
    skidka = State()
    preview = State()
    tahrir_field = State()

# =====================
# KEYBOARDS
# =====================
def main_kb():
    return ReplyKeyboardMarkup(keyboard=[
        [KeyboardButton(text="Tolov kiritish")],
        [KeyboardButton(text="Kursni ozgartirish")],
    ], resize_keyboard=True)

def orqaga_kb():
    return ReplyKeyboardMarkup(keyboard=[
        [KeyboardButton(text="Orqaga")]
    ], resize_keyboard=True)

def tayyor_orqaga_kb():
    return ReplyKeyboardMarkup(keyboard=[
        [KeyboardButton(text="Tayyor"), KeyboardButton(text="Orqaga")]
    ], resize_keyboard=True)

def turi_kb():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="Naqd", callback_data="turi_naqd")],
        [InlineKeyboardButton(text="Kartadan", callback_data="turi_karta")],
        [InlineKeyboardButton(text="Aralash (Naqd + Karta)", callback_data="turi_aralash")],
    ])

def finish_kb():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="Ha, finish (skidka bilan)", callback_data="fin_skidka")],
        [InlineKeyboardButton(text="Ha, finish (skidkasiz)", callback_data="fin_yoq")],
        [InlineKeyboardButton(text="Yoq, oddiy tolov", callback_data="fin_oddiy")],
    ])

def preview_kb():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="Tahrirlash", callback_data="pr_edit")],
        [InlineKeyboardButton(text="Yuborish", callback_data="pr_send")],
        [InlineKeyboardButton(text="Bekor qilish", callback_data="pr_cancel")],
    ])

def tahrir_kb():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="Mijoz ismi", callback_data="tr_mijoz")],
        [InlineKeyboardButton(text="Jami summa", callback_data="tr_summa")],
        [InlineKeyboardButton(text="Tolov turi", callback_data="tr_turi")],
        [InlineKeyboardButton(text="Skidka", callback_data="tr_skidka")],
        [InlineKeyboardButton(text="Orqaga", callback_data="tr_orqaga")],
    ])

# =====================
# HELPERS
# =====================
def fmt_uzs(n):
    return "{:,.0f}".format(n).replace(",", " ")

def fmt_tolov(data, uid):
    k = user_kurs.get(uid, 12500)
    turi_map = {"naqd": "Naqd", "karta": "Kartadan", "aralash": "Aralash (Naqd + Karta)"}
    turi = turi_map.get(data.get("turi", ""), "---")

    naqd_usd = data.get("naqd_usd", 0) or 0
    naqd_uzs = data.get("naqd_uzs", 0) or 0
    karta = data.get("karta", 0) or 0

    lines = [
        "YANGI TOLOV",
        "-------------------",
        "Mijoz: " + str(data.get("mijoz", "---")),
        "Jami: $" + str(data.get("summa", 0)),
        "Turi: " + turi,
    ]

    if data.get("turi") == "karta":
        lines.append("Karta: $" + str(data.get("summa", 0)))

    elif data.get("turi") == "naqd":
        if naqd_usd > 0:
            lines.append("  USD: $" + str(naqd_usd))
        if naqd_uzs > 0:
            uzs_usd = round(naqd_uzs / k, 2)
            lines.append("  UZS: " + fmt_uzs(naqd_uzs) + " (~$" + str(uzs_usd) + " | kurs: " + fmt_uzs(k) + ")")
            real = round(naqd_usd + uzs_usd, 2)
            farq = round(real - data.get("summa", 0), 2)
            lines.append("")
            lines.append("Real jami: $" + str(real) + " (farq " + ("+" if farq >= 0 else "") + str(farq) + ")")

    elif data.get("turi") == "aralash":
        lines.append("  Karta: $" + str(karta))
        if naqd_usd > 0:
            lines.append("  Naqd USD: $" + str(naqd_usd))
        if naqd_uzs > 0:
            uzs_usd = round(naqd_uzs / k, 2)
            lines.append("  Naqd UZS: " + fmt_uzs(naqd_uzs) + " (~$" + str(uzs_usd) + " | kurs: " + fmt_uzs(k) + ")")
            real = round(karta + naqd_usd + uzs_usd, 2)
            farq = round(real - data.get("summa", 0), 2)
            lines.append("")
            lines.append("Real jami: $" + str(real) + " (farq " + ("+" if farq >= 0 else "") + str(farq) + ")")

    if data.get("finish"):
        lines.append("FINISH")
        if data.get("skidka", 0) > 0:
            lines.append("Skidka: $" + str(data["skidka"]))

    lines.append("-------------------")
    sname = data.get("sender_name", "")
    suname = data.get("sender_username", "")
    sphone = data.get("sender_phone", "")
    if sname:
        lines.append("Kiritdi: " + sname + (" (@" + suname + ")" if suname else ""))
    if sphone:
        lines.append("Tel: " + sphone)
    return "\n".join(lines)

async def show_preview(message, state, uid):
    data = await state.get_data()
    text = fmt_tolov(data, uid)
    cheklar = data.get("cheklar", [])
    preview = "Tekshiring:\n\n" + text
    if cheklar:
        media = [InputMediaPhoto(media=cheklar[0], caption=preview)]
        for f in cheklar[1:]:
            media.append(InputMediaPhoto(media=f))
        await message.answer_media_group(media)
        await message.answer("Nima qilmoqchisiz?", reply_markup=preview_kb())
    else:
        await message.answer(preview, reply_markup=preview_kb())
    await state.set_state(S.preview)

# =====================
# START / AUTH
# =====================
@dp.message(CommandStart())
async def cmd_start(message: Message, state: FSMContext):
    uid = message.from_user.id
    await state.clear()
    if uid not in authenticated:
        await message.answer("Salom! Parolni kiriting:")
        await state.set_state(S.parol)
    elif uid not in user_phones:
        await message.answer("Telefon raqamingizni ulashing:", reply_markup=ReplyKeyboardMarkup(
            keyboard=[[KeyboardButton(text="Raqamni ulashish", request_contact=True)]],
            resize_keyboard=True, one_time_keyboard=True))
    elif uid not in user_kurs:
        await message.answer("Dollar kursini kiriting (masalan: 12800):", reply_markup=orqaga_kb())
        await state.set_state(S.kurs_birinchi)
    else:
        await message.answer("Xush kelibsiz!", reply_markup=main_kb())

@dp.message(S.parol)
async def check_parol(message: Message, state: FSMContext):
    uid = message.from_user.id
    if message.text.strip() == PAROL:
        authenticated.add(uid)
        await state.clear()
        if uid not in user_phones:
            await message.answer("Parol togri! Telefon raqamingizni ulashing:", reply_markup=ReplyKeyboardMarkup(
                keyboard=[[KeyboardButton(text="Raqamni ulashish", request_contact=True)]],
                resize_keyboard=True, one_time_keyboard=True))
        elif uid not in user_kurs:
            await message.answer("Dollar kursini kiriting (masalan: 12800):", reply_markup=orqaga_kb())
            await state.set_state(S.kurs_birinchi)
        else:
            await message.answer("Xush kelibsiz!", reply_markup=main_kb())
    else:
        await message.answer("Parol notogri! Qaytadan kiriting:")

@dp.message(F.contact)
async def get_contact(message: Message, state: FSMContext):
    uid = message.from_user.id
    if uid not in authenticated:
        return
    user_phones[uid] = message.contact.phone_number
    if uid not in user_kurs:
        await message.answer("Raqam saqlandi!\n\nDollar kursini kiriting (masalan: 12800):", reply_markup=orqaga_kb())
        await state.set_state(S.kurs_birinchi)
    else:
        await message.answer("Raqam saqlandi!", reply_markup=main_kb())

# =====================
# KURS
# =====================
@dp.message(S.kurs_birinchi)
async def kurs_birinchi(message: Message, state: FSMContext):
    uid = message.from_user.id
    try:
        k = int(message.text.strip().replace(" ", "").replace(",", ""))
        if k <= 0: raise ValueError
        user_kurs[uid] = k
        await state.clear()
        await message.answer("Kurs saqlandi: 1$ = " + fmt_uzs(k) + " UZS", reply_markup=main_kb())
    except:
        await message.answer("Faqat raqam kiriting! Masalan: 12800")

@dp.message(F.text == "Kursni ozgartirish")
async def kurs_ozgartirish(message: Message, state: FSMContext):
    uid = message.from_user.id
    if uid not in authenticated: return
    cur = user_kurs.get(uid)
    cur_str = "1$ = " + fmt_uzs(cur) + " UZS" if cur else "kiritilmagan"
    await message.answer("Hozirgi kurs: " + cur_str + "\n\nYangi kursni kiriting:", reply_markup=orqaga_kb())
    await state.set_state(S.kurs_yangi)

@dp.message(S.kurs_yangi)
async def kurs_yangi(message: Message, state: FSMContext):
    uid = message.from_user.id
    if message.text == "Orqaga":
        await state.clear()
        await message.answer("Bosh menyu:", reply_markup=main_kb())
        return
    try:
        k = int(message.text.strip().replace(" ", "").replace(",", ""))
        if k <= 0: raise ValueError
        user_kurs[uid] = k
        await state.clear()
        await message.answer("Kurs yangilandi: 1$ = " + fmt_uzs(k) + " UZS", reply_markup=main_kb())
    except:
        await message.answer("Faqat raqam kiriting!")

# =====================
# TOLOV BOSHLASH
# =====================
@dp.message(F.text == "Tolov kiritish")
async def tolov_boshlash(message: Message, state: FSMContext):
    uid = message.from_user.id
    if uid not in authenticated: return
    if uid not in user_kurs:
        await message.answer("Avval kursni kiriting:", reply_markup=orqaga_kb())
        await state.set_state(S.kurs_birinchi)
        return
    await state.clear()
    await state.update_data(cheklar=[])
    await message.answer("1. Mijoz ismi:", reply_markup=orqaga_kb())
    await state.set_state(S.mijoz)

@dp.message(S.mijoz)
async def get_mijoz(message: Message, state: FSMContext):
    if message.text == "Orqaga":
        await state.clear()
        await message.answer("Bosh menyu:", reply_markup=main_kb())
        return
    await state.update_data(mijoz=message.text)
    await message.answer("2. Jami summa (USD, masalan: 150.50):", reply_markup=orqaga_kb())
    await state.set_state(S.summa)

@dp.message(S.summa)
async def get_summa(message: Message, state: FSMContext):
    if message.text == "Orqaga":
        await message.answer("1. Mijoz ismi:", reply_markup=orqaga_kb())
        await state.set_state(S.mijoz)
        return
    try:
        summa = round(float(message.text.strip().replace(",", ".")), 2)
        if summa <= 0: raise ValueError
        await state.update_data(summa=summa)
        await message.answer("3. Tolov turini tanlang:", reply_markup=orqaga_kb())
        await message.answer("Turni tanlang:", reply_markup=turi_kb())
        await state.set_state(S.tolov_turi)
    except:
        await message.answer("Faqat raqam kiriting! Masalan: 150 yoki 150.50")

@dp.message(S.tolov_turi, F.text == "Orqaga")
async def turi_orqaga(message: Message, state: FSMContext):
    await message.answer("2. Jami summa (USD):", reply_markup=orqaga_kb())
    await state.set_state(S.summa)

@dp.callback_query(F.data.startswith("turi_"), S.tolov_turi)
async def get_turi(callback: CallbackQuery, state: FSMContext):
    turi = callback.data.replace("turi_", "")
    await state.update_data(turi=turi, karta=0, naqd_usd=0, naqd_uzs=0)
    await callback.message.edit_reply_markup()
    if turi == "naqd":
        await callback.message.answer("Naqd USD qismi (0 yozing agar hammasi UZS bolsa):", reply_markup=orqaga_kb())
        await state.set_state(S.naqd_usd)
    elif turi == "karta":
        await callback.message.answer("Chek rasmini yuboring:", reply_markup=tayyor_orqaga_kb())
        await state.set_state(S.chek)
    elif turi == "aralash":
        data = await state.get_data()
        await callback.message.answer("Karta qismi USD (Jami: $" + str(data["summa"]) + "):", reply_markup=orqaga_kb())
        await state.set_state(S.karta_summa)
    await callback.answer()

@dp.message(S.karta_summa)
async def get_karta(message: Message, state: FSMContext):
    if message.text == "Orqaga":
        data = await state.get_data()
        await message.answer("Tolov turini tanlang:", reply_markup=orqaga_kb())
        await message.answer("Turni tanlang:", reply_markup=turi_kb())
        await state.set_state(S.tolov_turi)
        return
    try:
        data = await state.get_data()
        karta = round(float(message.text.strip().replace(",", ".")), 2)
        naqd = round(data["summa"] - karta, 2)
        if karta < 0 or naqd < 0: raise ValueError
        await state.update_data(karta=karta)
        await message.answer("Karta: $" + str(karta) + " | Naqd: $" + str(naqd) + "\n\nNaqd USD qismi (0 yozing agar hammasi UZS bolsa):", reply_markup=orqaga_kb())
        await state.set_state(S.naqd_usd)
    except:
        await message.answer("Faqat raqam kiriting!")

@dp.message(S.naqd_usd)
async def get_naqd_usd(message: Message, state: FSMContext):
    if message.text == "Orqaga":
        data = await state.get_data()
        if data.get("turi") == "aralash":
            await message.answer("Karta qismi USD:", reply_markup=orqaga_kb())
            await state.set_state(S.karta_summa)
        else:
            await message.answer("Tolov turini tanlang:", reply_markup=orqaga_kb())
            await message.answer("Turni tanlang:", reply_markup=turi_kb())
            await state.set_state(S.tolov_turi)
        return
    try:
        naqd_usd = round(float(message.text.strip().replace(",", ".")), 2)
        if naqd_usd < 0: raise ValueError
        await state.update_data(naqd_usd=naqd_usd)
        await message.answer("Naqd UZS qismi (0 yozing agar yoq bolsa):", reply_markup=orqaga_kb())
        await state.set_state(S.naqd_uzs)
    except:
        await message.answer("Faqat raqam kiriting!")

@dp.message(S.naqd_uzs)
async def get_naqd_uzs(message: Message, state: FSMContext):
    if message.text == "Orqaga":
        await message.answer("Naqd USD qismi:", reply_markup=orqaga_kb())
        await state.set_state(S.naqd_usd)
        return
    try:
        naqd_uzs = int(message.text.strip().replace(" ", "").replace(",", ""))
        if naqd_uzs < 0: raise ValueError
        await state.update_data(naqd_uzs=naqd_uzs)
        data = await state.get_data()
        if data.get("turi") == "aralash":
            await message.answer("Chek rasmini yuboring:", reply_markup=tayyor_orqaga_kb())
            await state.set_state(S.chek)
        else:
            await message.answer("Bu oxirgi tolov (finish) mi?", reply_markup=orqaga_kb())
            await message.answer("Tanlang:", reply_markup=finish_kb())
            await state.set_state(S.finish)
    except:
        await message.answer("Faqat raqam kiriting!")

@dp.message(S.chek, F.photo)
async def get_chek(message: Message, state: FSMContext):
    data = await state.get_data()
    cheklar = data.get("cheklar", [])
    cheklar.append(message.photo[-1].file_id)
    await state.update_data(cheklar=cheklar)
    await message.answer("Chek qabul qilindi (" + str(len(cheklar)) + " ta). Yana yuborishingiz yoki Tayyor bosing.")

@dp.message(S.chek, F.text == "Tayyor")
async def chek_tayyor(message: Message, state: FSMContext):
    await message.answer("Bu oxirgi tolov (finish) mi?", reply_markup=orqaga_kb())
    await message.answer("Tanlang:", reply_markup=finish_kb())
    await state.set_state(S.finish)

@dp.message(S.chek, F.text == "Orqaga")
async def chek_orqaga(message: Message, state: FSMContext):
    await state.update_data(cheklar=[])
    await message.answer("Naqd UZS qismi:", reply_markup=orqaga_kb())
    await state.set_state(S.naqd_uzs)

@dp.message(S.finish, F.text == "Orqaga")
async def finish_orqaga(message: Message, state: FSMContext):
    data = await state.get_data()
    if data.get("turi") in ["karta", "aralash"]:
        await message.answer("Chek rasmini yuboring:", reply_markup=tayyor_orqaga_kb())
        await state.set_state(S.chek)
    else:
        await message.answer("Naqd UZS qismi:", reply_markup=orqaga_kb())
        await state.set_state(S.naqd_uzs)

@dp.callback_query(F.data.startswith("fin_"), S.finish)
async def get_finish(callback: CallbackQuery, state: FSMContext):
    action = callback.data.replace("fin_", "")
    await callback.message.edit_reply_markup()
    uid = callback.from_user.id
    if action == "oddiy":
        await state.update_data(finish=False, skidka=0)
        await show_preview(callback.message, state, uid)
    elif action == "yoq":
        await state.update_data(finish=True, skidka=0)
        await show_preview(callback.message, state, uid)
    elif action == "skidka":
        await state.update_data(finish=True)
        await callback.message.answer("Skidka miqdori (USD):", reply_markup=orqaga_kb())
        await state.set_state(S.skidka)
    await callback.answer()

@dp.message(S.skidka)
async def get_skidka(message: Message, state: FSMContext):
    uid = message.from_user.id
    if message.text == "Orqaga":
        await message.answer("Bu oxirgi tolov (finish) mi?", reply_markup=orqaga_kb())
        await message.answer("Tanlang:", reply_markup=finish_kb())
        await state.set_state(S.finish)
        return
    try:
        skidka = round(float(message.text.strip().replace(",", ".")), 2)
        await state.update_data(skidka=skidka)
        await show_preview(message, state, uid)
    except:
        await message.answer("Faqat raqam kiriting!")

# =====================
# PREVIEW
# =====================
@dp.callback_query(F.data == "pr_edit", S.preview)
async def pr_edit(callback: CallbackQuery, state: FSMContext):
    await callback.message.answer("Qaysi maydonni ozgartirmoqchisiz?", reply_markup=tahrir_kb())
    await callback.answer()

@dp.callback_query(F.data == "pr_send", S.preview)
async def pr_send(callback: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    uid = callback.from_user.id
    await state.update_data(
        sender_name=callback.from_user.full_name,
        sender_username=callback.from_user.username or "",
        sender_phone=user_phones.get(uid, "")
    )
    data = await state.get_data()
    text = fmt_tolov(data, uid)
    cheklar = data.get("cheklar", [])
    try:
        if cheklar:
            media = [InputMediaPhoto(media=cheklar[0], caption=text)]
            for f in cheklar[1:]:
                media.append(InputMediaPhoto(media=f))
            await bot.send_media_group(CHANNEL, media)
        else:
            await bot.send_message(CHANNEL, text)
        await callback.message.answer("Tolov kanalga yuborildi!", reply_markup=main_kb())
        await state.clear()
    except Exception as e:
        await callback.message.answer("Xato: " + str(e))
    await callback.answer()

@dp.callback_query(F.data == "pr_cancel", S.preview)
async def pr_cancel(callback: CallbackQuery, state: FSMContext):
    await state.clear()
    await callback.message.answer("Bekor qilindi.", reply_markup=main_kb())
    await callback.answer()

@dp.callback_query(F.data.startswith("tr_"), S.preview)
async def tahrir_field(callback: CallbackQuery, state: FSMContext):
    field = callback.data.replace("tr_", "")
    uid = callback.from_user.id
    if field == "orqaga":
        await show_preview(callback.message, state, uid)
    elif field == "turi":
        await callback.message.answer("Yangi tolov turini tanlang:", reply_markup=turi_kb())
        await state.set_state(S.tolov_turi)
    else:
        labels = {"mijoz": "Yangi mijoz ismi:", "summa": "Yangi jami summa (USD):", "skidka": "Yangi skidka (USD):"}
        await state.update_data(tahrir_field=field)
        await callback.message.answer(labels.get(field, "Yangi qiymat:"), reply_markup=orqaga_kb())
        await state.set_state(S.tahrir_field)
    await callback.answer()

@dp.message(S.tahrir_field)
async def save_tahrir(message: Message, state: FSMContext):
    uid = message.from_user.id
    if message.text == "Orqaga":
        await show_preview(message, state, uid)
        return
    data = await state.get_data()
    field = data.get("tahrir_field")
    if field in ["summa", "skidka"]:
        try:
            val = round(float(message.text.strip().replace(",", ".")), 2)
            await state.update_data(**{field: val})
        except:
            await message.answer("Faqat raqam kiriting!")
            return
    else:
        await state.update_data(**{field: message.text})
    await state.set_state(S.preview)
    await show_preview(message, state, uid)

# =====================
# MAIN
# =====================
async def main():
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
