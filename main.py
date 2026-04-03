python# -*- coding: utf-8 -*-
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
from aiogram.filters import CommandStart

BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN", "8736560386:AAHgOAW2vK2kf_3TfV5_Tli_h0GRilQ8s5o")
CHANNEL = "@TOLOVLARKIRITISHUCHUNTEST"

logging.basicConfig(level=logging.INFO)
bot = Bot(token=BOT_TOKEN)
dp = Dispatcher(storage=MemoryStorage())
user_phones = {}

class Tolov(StatesGroup):
    mijoz = State()
    summa = State()
    tolov_turi = State()
    naqd_qismi = State()
    chek = State()
    finish = State()
    skidka = State()
    tasdiqlash = State()

def main_menu():
    return ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton(text="Tolov kiritish")]],
        resize_keyboard=True
    )

def tolov_turi_kb():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="Naqd", callback_data="turi_naqd")],
        [InlineKeyboardButton(text="Kartadan", callback_data="turi_karta")],
        [InlineKeyboardButton(text="Aralash", callback_data="turi_aralash")],
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

@dp.message(CommandStart())
async def start(message: Message, state: FSMContext):
    if message.from_user.id not in user_phones:
        kb = ReplyKeyboardMarkup(
            keyboard=[[KeyboardButton(text="Raqamni ulashish", request_contact=True)]],
            resize_keyboard=True,
            one_time_keyboard=True
        )
        await message.answer("Salom! Avval telefon raqamingizni ulashing:", reply_markup=kb)
    else:
        await message.answer("Salom! Quyidagi menyudan foydalaning:", reply_markup=main_menu())

@dp.message(F.contact)
async def get_contact(message: Message):
    user_phones[message.from_user.id] = message.contact.phone_number
    await message.answer("Raqam saqlandi!", reply_markup=main_menu())

@dp.message(F.text == "Tolov kiritish")
async def start_tolov(message: Message, state: FSMContext):
    await state.clear()
    await state.update_data(chek_ids=[])
    await message.answer(
        "Mijoz ismi:",
        reply_markup=ReplyKeyboardMarkup(keyboard=[], resize_keyboard=True)
    )
    await state.set_state(Tolov.mijoz)

@dp.message(Tolov.mijoz)
async def get_mijoz(message: Message, state: FSMContext):
    await state.update_data(mijoz=message.text)
    await message.answer("Necha dollar tolayapti? (faqat raqam, masalan: 150.50)")
    await state.set_state(Tolov.summa)

@dp.message(Tolov.summa)
async def get_summa(message: Message, state: FSMContext):
    text = message.text.strip().replace(",", ".")
    try:
        summa = round(float(text), 2)
        if summa <= 0:
            raise ValueError
        await state.update_data(summa=summa)
        await message.answer(
            "Summa: $" + str(summa) + "\n\nTolov turini tanlang:",
            reply_markup=tolov_turi_kb()
        )
        await state.set_state(Tolov.tolov_turi)
    except:
        await message.answer("Faqat raqam kiriting! Masalan: 150 yoki 150.50")

@dp.callback_query(F.data.startswith("turi_"), Tolov.tolov_turi)
async def get_turi(callback: CallbackQuery, state: FSMContext):
    turi = callback.data.replace("turi_", "")
    await state.update_data(tolov_turi=turi, naqd=None, karta=None)
    await callback.message.edit_reply_markup()
    if turi == "naqd":
        await show_finish(callback.message, state)
    elif turi == "karta":
        await callback.message.answer("Chek rasmini yuboring (tugagach /tayyor yozing):")
        await state.set_state(Tolov.chek)
    elif turi == "aralash":
        data = await state.get_data()
        await callback.message.answer("Naqd qismi (USD)? Jami: $" + str(data["summa"]))
        await state.set_state(Tolov.naqd_qismi)
    await callback.answer()

@dp.message(Tolov.naqd_qismi)
async def get_naqd(message: Message, state: FSMContext):
    try:
        data = await state.get_data()
        naqd = round(float(message.text.strip().replace(",", ".")), 2)
        karta = round(data["summa"] - naqd, 2)
        if naqd < 0 or karta < 0:
            raise ValueError
        await state.update_data(naqd=naqd, karta=karta)
        await message.answer(
            "Naqd: $" + str(naqd) + " | Karta: $" + str(karta) + "\n\nChek rasmini yuboring (tugagach /tayyor yozing):"
        )
        await state.set_state(Tolov.chek)
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

def format_tolov(data, sender_name="", sender_username="", sender_phone=""):
    turi_map = {"naqd": "Naqd", "karta": "Kartadan", "aralash": "Aralash"}
    turi = turi_map.get(data.get("tolov_turi", ""), "---")
    lines = [
        "YANGI TOLOV",
        "-------------------",
        "Mijoz: " + str(data.get("mijoz", "---")),
        "Tolov: $" + str(data.get("summa", 0)),
        "Turi: " + turi,
    ]
    if data.get("tolov_turi") == "aralash" and data.get("naqd") is not None:
        lines.append("  Naqd: $" + str(data["naqd"]))
        lines.append("  Karta: $" + str(data["karta"]))
    if data.get("finish"):
        lines.append("FINISH ✅")
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
    text = format_tolov(data)
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

@dp.callback_query(F.data == "send", Tolov.tasdiqlash)
async def send_tolov(callback: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    user = callback.from_user
    phone = user_phones.get(user.id, "")
    text = format_tolov(data, user.full_name, user.username or "", phone)
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
