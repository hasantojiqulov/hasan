# always_on.py - PythonAnywhere uchun 24/7 bot
import os
import asyncio
import sys

# bot.py faylini import qilish uchun yo'l qo'shish
sys.path.append('/home/xovosmaktab2')

from bot import main  # bot.py dan main funksiyasini import qiladi

if __name__ == "__main__":
    print("Xovos 2-maktab Bot ishga tushdi (PythonAnywhere)")
    asyncio.run(main())
