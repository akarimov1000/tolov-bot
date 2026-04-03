import sys
sys.stdout.reconfigure(encoding='utf-8')
import asyncio
import logging
import os
from aiogram import Bot, Dispatcher, F
from aiogram.types import Message, CallbackQuery, ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton, InputMediaPhoto
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.filters import CommandStart, Command

BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN", "8736560386:AAHgOAW2vK2kf_3TfV5_Tli_h0GRilQ8s5o")
CHANNEL = "@TOLOVLARKIRITISHUCHUNTEST"

logging.basicConfig(level=logging.INFO)
bot = Bot(token=BOT_TOKEN)
dp = Dispatcher(storage=MemoryStorage())

user_phones = {}
kurs = {}  # {user_id: 12500}

class Tolov(StatesGroup):
    kurs_kirish = State()
    mijoz = State()
    summa = State()
    tolov_turi = State()
    karta_summa = State()
    naqd_usd = State()
    naqd_uzs = State()
    chek = State()
    finish = State()
    skidka = State()
    tasdiqlash = State()
    tahrirlash = State()

class KursState(StatesGroup):
    yangi_kurs = State()

def main_menu():
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="Tolov kiritish")],
            [KeyboardButton(text="Kursni ozgartirish")],
        ],
        resize_keyboard=True
    )

def tolov_turi_kb():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="Naqd", callback_data="turi_naqd")],
        [InlineKeyboardButton(text="Kartadan", callback_data="turi_karta")],
        [InlineKeyboardButton(text="Aralash (Naqd + Karta)", callback_data="turi_aralash")],
    ])

def finish_kb():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="Ha, finish (skidka bilan)", callback_data="finish_skidka")],
        [InlineKeyboardButton(text="Ha, finish (skidkasiz)", callback_data="finish_yoq")],
        [InlineKeyboardButton(text="Yoq, oddiy tolov", callback_data="finish_oddiy")],
    ])

def tasdiq_kb():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="Tahrirlash", callback_data="edit")],
        [InlineKeyboardButton(text="Yuborish", callback_data="send")],
        [InlineKeyboardButton(text="Bekor qilish", callback_data="cancel")],
    ])

def tahrirlash_kb():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="Mijoz ismi", callback_data="tahrirla_mijoz")],
        [InlineKeyboardButton(text="Jami summa", callback_data="tahrirla_summa")],
        [InlineKeyboardButton(text="Tolov turi", callback_data="tahrirla_turi")],
        [InlineKeyboardButton(text="Skidka", callback_data="tahrirla_skidka")],
        [InlineKeyboardButton(text="Orqaga", callback_data="tahrirla_orqaga")],
    ])

def uzs_format(uzs):
    return "{:,.0f}".format(uzs).replace(",", " ")

@dp.message(CommandStart())
async def start(message: Message, state: FSMContext):
    uid = message.from_user.id
    if uid not in user_phones:
        kb = ReplyKeyboardMarkup(
            keyboard=[[KeyboardButton(text="Raqamni ulashish", request_contact=True)]],
            resize_keyboard=True, one_time_keyboard=True
        )
        await message.answer("Salom! Avval telefon raqamingizni ulashing:", reply_markup=kb)
    elif uid not in kurs:
        await message.answer("Hozirgi dollar kursini kiriting (masalan: 12800):")
        await state.set_state(Tolov.kurs_kirish)
    else:
        await message.answer("Salom! Quyidagi menyudan foydalaning:", reply_markup=main_menu())

@dp.message(F.contact)
async def get_contact(message: Message, state: FSMContext):
    uid = message.from_user.id
    user_phones[uid] = message.contact.phone_number
    if uid not in kurs:
        await message.answer("Raqam saqlandi!\n\nHozirgi dollar kursini kiriting (masalan: 12800):")
        await state.set_state(Tolov.kurs_kirish)
    else:
        await message.answer("Raqam saqlandi!", reply_markup=main_menu())

@dp.message(Tolov.kurs_kirish)
async def get_kurs(message: Message, state: FSMContext):
    try:
        k = int(message.text.strip().replace(" ", "").replace(",", ""))
        if k <= 0:
            raise ValueError
        kurs[message.from_user.id] = k
        await message.answer("Kurs saqlandi: 1$ = " + uzs_format(k) + " UZS", reply_markup=main_menu())
        await state.clear()
    except:
        await message.answer("Faqat raqam kiriting! Masalan: 12800")

@dp.message(F.text == "Kursni ozgartirish")
async def change_kurs(message: Message, state: FSMContext):
    uid = message.from_user.id
    cur = kurs.get(uid, "---")
    await message.answer("Hozirgi kurs: 1$ = " + (uzs_format(cur) if cur != "---" else "---") + " UZS\n\nYangi kursni kiriting:")
    await state.set_state(KursState.yangi_kurs)

@dp.message(KursState.yangi_kurs)
async def save_kurs(message: Message, state: FSMContext):
    try:
        k = int(message.text.strip().replace(" ", "").replace(",", ""))
        if k <= 0:
            raise ValueError
        kurs[message.from_user.id] = k
        await message.answer("Kurs yangilandi: 1$ = " + uzs_format(k) + " UZS", reply_markup=main_menu())
        await state.clear()
    except:
        await message.answer("Faqat raqam kiriting!")

@dp.message(F.text == "Tolov kiritish")
async def start_tolov(message: Message, state: FSMContext):
    uid = message.from_user.id
    if uid not in kurs:
        await message.answer("Avval kursni kiriting:")
        await state.set_state(Tolov.kurs_kirish)
        return
    await state.clear()
    await state.update_data(chek_ids=[])
    await message.answer("Mijoz ismi:", reply_markup=ReplyKeyboardMarkup(keyboard=[], resize_keyboard=True))
    await state.set_state(Tolov.mijoz)

@dp.message(Tolov.mijoz)
async def get_mijoz(message: Message, state: FSMContext):
    await state.update_data(mijoz=message.text)
    await message.answer("Jami qancha tolayabdi? (masalan: 150.50)")
    await state.set_state(Tolov.summa)

@dp.message(Tolov.summa)
async def get_summa(message: Message, state: FSMContext):
    text = message.text.strip().replace(",", ".")
    try:
        summa = round(float(text), 2)
        if summa <= 0:
            raise ValueError
        await state.update_data(summa=summa)
        await message.answer("Jami: $" + str(summa) + "\n\nTolov turini tanlang:", reply_markup=tolov_turi_kb())
        await state.set_state(Tolov.tolov_turi)
    except:
        await message.answer("Faqat raqam kiriting! Masalan: 150 yoki 150.50")

@dp.callback_query(F.data.startswith("turi_"), Tolov.tolov_turi)
async def get_turi(callback: CallbackQuery, state: FSMContext):
    turi = callback.data.replace("turi_", "")
    await state.update_data(tolov_turi=turi, karta=None, naqd_usd=None, naqd_uzs=0)
    await callback.message.edit_reply_markup()

    if turi == "naqd":
        data = await state.get_data()
        await callback.message.answer("Naqd USD qismi: (masalan: 100)\n(Hammasi UZS da bolsa 0 yozing)")
        await state.set_state(Tolov.naqd_usd)

    elif turi == "karta":
        await callback.message.answer("Chek rasmini yuboring (tugagach /tayyor yozing):")
        await state.set_state(Tolov.chek)

    elif turi == "aralash":
        data = await state.get_data()
        await callback.message.answer("Karta qismi USD (masalan: 50):\n(Jami: $" + str(data["summa"]) + ")")
        await state.set_state(Tolov.karta_summa)

    await callback.answer()

@dp.message(Tolov.karta_summa)
async def get_karta_summa(message: Message, state: FSMContext):
    try:
        data = await state.get_data()
        karta_s = round(float(message.text.strip().replace(",", ".")), 2)
        naqd_total = round(data["summa"] - karta_s, 2)
        if karta_s < 0 or naqd_total < 0:
            raise ValueError
        await state.update_data(karta=karta_s)
        await message.answer("Karta: $" + str(karta_s) + "\nNaqd jami: $" + str(naqd_total) + "\n\nNaqd USD qismi (masalan: 70):\n(Hammasi UZS bolsa 0 yozing)")
        await state.set_state(Tolov.naqd_usd)
    except:
        await message.answer("Faqat raqam kiriting!")

@dp.message(Tolov.naqd_usd)
async def get_naqd_usd(message: Message, state: FSMContext):
    try:
        naqd_usd = round(float(message.text.strip().replace(",", ".")), 2)
        if naqd_usd < 0:
            raise ValueError
        await state.update_data(naqd_usd=naqd_usd)
        await message.answer("Naqd UZS qismi (masalan: 610000):\n(Yoq bolsa 0 yozing)")
        await state.set_state(Tolov.naqd_uzs)
    except:
        await message.answer("Faqat raqam kiriting!")

@dp.message(Tolov.naqd_uzs)
async def get_naqd_uzs(message: Message, state: FSMContext):
    try:
        naqd_uzs = int(message.text.strip().replace(" ", "").replace(",", ""))
        if naqd_uzs < 0:
            raise ValueError
        await state.update_data(naqd_uzs=naqd_uzs)
        data = await state.get_data()
        if data.get("tolov_turi") == "karta":
            pass
        elif data.get("tolov_turi") in ["naqd", "aralash"]:
            if data.get("tolov_turi") == "aralash":
                await message.answer("Chek rasmini yuboring (tugagach /tayyor yozing):")
                await state.set_state(Tolov.chek)
                return
        await show_finish(message, state)
    except:
        await message.answer("Faqat raqam kiriting!")

@dp.message(Tolov.chek, F.photo)
async def get_chek(message: Message, state: FSMContext):
    data = await state.get_data()
    cheklar = data.get("chek_ids", [])
    cheklar.append(message.photo[-1].file_id)
    await state.update_data(chek_ids=cheklar)
    await message.answer("Chek qabul qilindi (" + str(len(cheklar)) + " ta). Yana yuborishingiz yoki /tayyor yozing.")

@dp.message(Tolov.chek, F.text == "/tayyor")
async def chek_tayyor(message: Message, state: FSMContext):
    await show_finish(message, state)

async def show_finish(message: Message, state: FSMContext):
    await message.answer("Bu mijozning oxirgi tolovi (finish) mi?", reply_markup=finish_kb())
    await state.set_state(Tolov.finish)

@dp.callback_query(F.data.startswith("finish_"), Tolov.finish)
async def get_finish(callback: CallbackQuery, state: FSMContext):
    action = callback.data.replace("finish_", "")
    await callback.message.edit_reply_markup()
    if action == "oddiy":
        await state.update_data(finish=False, skidka=0)
        await show_preview(callback.message, state)
    elif action == "yoq":
        await state.update_data(finish=True, skidka=0)
        await show_preview(callback.message, state)
    elif action == "skidka":
        await state.update_data(finish=True)
        await callback.message.answer("Skidka miqdori (USD):")
        await state.set_state(Tolov.skidka)
    await callback.answer()

@dp.message(Tolov.skidka)
async def get_skidka(message: Message, state: FSMContext):
    try:
        skidka = round(float(message.text.strip().replace(",", ".")), 2)
        await state.update_data(skidka=skidka)
        await show_preview(message, state)
    except:
        await message.answer("Faqat raqam kiriting!")

def format_tolov(data, user_kurs=12500, sender_name="", sender_username="", sender_phone=""):
    turi_map = {"naqd": "Naqd", "karta": "Kartadan", "aralash": "Aralash (Naqd + Karta)"}
    turi = turi_map.get(data.get("tolov_turi", ""), "---")

    lines = [
        "YANGI TOLOV",
        "-------------------",
        "Mijoz: " + str(data.get("mijoz", "---")),
        "Jami: $" + str(data.get("summa", 0)),
        "Turi: " + turi,
    ]

    if data.get("tolov_turi") == "karta":
        lines.append("Karta: $" + str(data.get("summa", 0)))

    elif data.get("tolov_turi") == "naqd":
        naqd_usd = data.get("naqd_usd", 0)
        naqd_uzs = data.get("naqd_uzs", 0)
        if naqd_usd > 0:
            lines.append("  USD: $" + str(naqd_usd))
        if naqd_uzs > 0:
            uzs_usd = round(naqd_uzs / user_kurs, 2)
            lines.append("  UZS: " + uzs_format(naqd_uzs) + " (~$" + str(uzs_usd) + " | kurs: " + uzs_format(user_kurs) + ")")

    elif data.get("tolov_turi") == "aralash":
        karta_s = data.get("karta", 0)
        naqd_usd = data.get("naqd_usd", 0)
        naqd_uzs = data.get("naqd_uzs", 0)
        lines.append("  Karta: $" + str(karta_s))
        if naqd_usd > 0:
            lines.append("  Naqd USD: $" + str(naqd_usd))
        if naqd_uzs > 0:
            uzs_usd = round(naqd_uzs / user_kurs, 2)
            lines.append("  Naqd UZS: " + uzs_format(naqd_uzs) + " (~$" + str(uzs_usd) + " | kurs: " + uzs_format(user_kurs) + ")")

    # Real jami va farq
    naqd_usd_v = data.get("naqd_usd", 0) or 0
    naqd_uzs_v = data.get("naqd_uzs", 0) or 0
    karta_v = data.get("karta", 0) or 0
    turi_v = data.get("tolov_turi", "")
    if naqd_uzs_v > 0:
        uzs_usd_v = round(naqd_uzs_v / user_kurs, 2)
        if turi_v == "naqd":
            real_jami = round(naqd_usd_v + uzs_usd_v, 2)
        elif turi_v == "aralash":
            real_jami = round(karta_v + naqd_usd_v + uzs_usd_v, 2)
        else:
            real_jami = None
        if real_jami is not None:
            farq = round(real_jami - data.get("summa", 0), 2)
            farq_str = ("+" if farq >= 0 else "") + str(farq)
            lines.append("")
            lines.append("Real jami: $" + str(real_jami) + " (farq " + farq_str + ")")

    if data.get("finish"):
        lines.append("FINISH")
        if data.get("skidka", 0) > 0:
            lines.append("Skidka: $" + str(data["skidka"]))

    lines.append("-------------------")
    if sender_name:
        uname = " (@" + sender_username + ")" if sender_username else ""
        lines.append("Kiritdi: " + sender_name + uname)
    if sender_phone:
        lines.append("Tel: " + sender_phone)

    return "\n".join(lines)

async def show_preview(message: Message, state: FSMContext):
    data = await state.get_data()
    uid = message.chat.id
    user_kurs = kurs.get(uid, 12500)
    text = format_tolov(data, user_kurs)
    cheklar = data.get("chek_ids", [])
    preview = "Tekshiring:\n\n" + text
    if cheklar:
        media = [InputMediaPhoto(media=cheklar[0], caption=preview)]
        for f in cheklar[1:]:
            media.append(InputMediaPhoto(media=f))
        await message.answer_media_group(media)
        await message.answer("Nima qilmoqchisiz?", reply_markup=tasdiq_kb())
    else:
        await message.answer(preview, reply_markup=tasdiq_kb())
    await state.set_state(Tolov.tasdiqlash)

@dp.callback_query(F.data == "edit", Tolov.tasdiqlash)
async def edit_menu(callback: CallbackQuery, state: FSMContext):
    await callback.message.answer("Qaysi maydonni ozgartirmoqchisiz?", reply_markup=tahrirlash_kb())
    await callback.answer()

@dp.callback_query(F.data.startswith("tahrirla_"), Tolov.tasdiqlash)
async def tahrirla_field(callback: CallbackQuery, state: FSMContext):
    field = callback.data.replace("tahrirla_", "")
    if field == "orqaga":
        await show_preview(callback.message, state)
        await callback.answer()
        return
    if field == "turi":
        await callback.message.answer("Yangi tolov turini tanlang:", reply_markup=tolov_turi_kb())
        await state.set_state(Tolov.tolov_turi)
    else:
        labels = {
            "mijoz": "Yangi mijoz ismini yozing:",
            "summa": "Yangi jami summani yozing (USD):",
            "skidka": "Yangi skidkani yozing (USD):"
        }
        await state.update_data(tahrirlash_field=field)
        await callback.message.answer(labels.get(field, "Yangi qiymatni yozing:"))
        await state.set_state(Tolov.tahrirlash)
    await callback.answer()

@dp.message(Tolov.tahrirlash)
async def save_tahrirlash(message: Message, state: FSMContext):
    data = await state.get_data()
    field = data.get("tahrirlash_field")
    if field in ["summa", "skidka"]:
        try:
            val = round(float(message.text.strip().replace(",", ".")), 2)
            await state.update_data(**{field: val})
        except:
            await message.answer("Faqat raqam kiriting!")
            return
    else:
        await state.update_data(**{field: message.text})
    await message.answer("Saqlandi!")
    await state.set_state(Tolov.tasdiqlash)
    await show_preview(message, state)

@dp.callback_query(F.data == "send", Tolov.tasdiqlash)
async def send_tolov(callback: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    user = callback.from_user
    phone = user_phones.get(user.id, "")
    user_kurs = kurs.get(user.id, 12500)
    text = format_tolov(data, user_kurs, user.full_name, user.username or "", phone)
    cheklar = data.get("chek_ids", [])
    try:
        if cheklar:
            media = [InputMediaPhoto(media=cheklar[0], caption=text)]
            for f in cheklar[1:]:
                media.append(InputMediaPhoto(media=f))
            await bot.send_media_group(CHANNEL, media)
        else:
            await bot.send_message(CHANNEL, text)
        await callback.message.answer("Tolov kanalga yuborildi!", reply_markup=main_menu())
    except Exception as e:
        await callback.message.answer("Xato: " + str(e))
    await state.clear()
    await callback.answer()

@dp.callback_query(F.data == "cancel")
async def cancel(callback: CallbackQuery, state: FSMContext):
    await state.clear()
    await callback.message.answer("Bekor qilindi.", reply_markup=main_menu())
    await callback.answer()

async def main():
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
