import os
import webbrowser
import pyautogui
import logging
import subprocess
from PIL import Image
import win32print
import win32ui
from PIL import ImageWin
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, ContextTypes, ConversationHandler
import tempfile
import io
import asyncio
from wakeonlan import send_magic_packet
from plyer import notification

# Настройка логирования
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)

# Токен вашего бота
BOT_TOKEN = "8115963718:AAEo-ZLb0Z9oWMRd0IqUnzS11EHhgjpn_KY"

# Константы для ConversationHandler
ASK_IP, MAIN_MENU = range(2)

# Словарь для хранения данных пользователей
user_data = {}

# Запрос IP-адреса
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    logger.info(f"Пользователь {update.message.chat.id} начал настройку.")
    await update.message.reply_text("Привет! Пожалуйста, введите ваш IP-адрес:")
    return ASK_IP

# Сохранение IP-адреса и переход в главное меню
async def set_ip(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.message.chat.id
    user_data[user_id] = {"ip_address": update.message.text}
    logger.info(f"Пользователь {user_id} установил IP-адрес: {update.message.text}")
    await update.message.reply_text("IP-адрес установлен! Выберите команду:\n\n"
                                     "/open_website [URL] - Открыть сайт\n\n"
                                     "/telegram - Открыть Telegram Web\n\n"
                                     "/whatsapp - Открыть WhatsApp Web\n\n"
                                     "/wake - Включить устройство\n\n"
                                     "/shutdown - Выключить устройство\n\n"
                                     "/screenshot - Сделать скриншот экрана\n\n"
                                     "/sleep - Перевести устройство в спящий режим\n\n"
                                     "/print - Отправить файл на печать\n\n"
                                     "/ink_level - Проверить уровень чернил\n\n"
                                     "/notify [сообщение] - Отправить уведомление\n\n"
                                     "/timer [время в секундах] - Установить таймер\n\n"
                                     "/cancel - Отменить настройку")
    return MAIN_MENU

# Открытие сайта
async def open_website(update: Update, context: ContextTypes.DEFAULT_TYPE):
    logger.info(f"Пользователь {update.message.chat.id} запросил открыть сайт: {context.args}")
    if context.args:
        website = context.args[0]
        webbrowser.open(website)
        await update.message.reply_text(f"Открываю сайт: {website}")
    else:
        await update.message.reply_text("Укажите адрес сайта. Например: /open_website https://example.com")

# Открытие Telegram Web
async def open_telegram(update: Update, context: ContextTypes.DEFAULT_TYPE):
    webbrowser.open("https://web.telegram.org")
    await update.message.reply_text("Открываю Telegram Web")

# Открытие WhatsApp Web
async def open_whatsapp(update: Update, context: ContextTypes.DEFAULT_TYPE):
    webbrowser.open("https://web.whatsapp.com")
    await update.message.reply_text("Открываю WhatsApp Web")

# Включение устройства по MAC-адресу
async def wake_device(update: Update, context: ContextTypes.DEFAULT_TYPE):
    mac_address = "D0-37-45-DE-81-DE"  # Заданный MAC-адрес
    send_magic_packet(mac_address)
    await update.message.reply_text(f"Отправлен магический пакет на {mac_address}.")
    notification.notify(
        title='Wake-on-LAN',
        message=f"Отправлен магический пакет на {mac_address}.",
        app_name='Ваше приложение',
        timeout=10
    )

# Выключение устройства
async def shutdown_device(update: Update, context: ContextTypes.DEFAULT_TYPE):
    subprocess.call(["shutdown", "/s", "/t", "1"])
    await update.message.reply_text("Устройство будет выключено.")

# Сделать скриншот
async def screenshot(update: Update, context: ContextTypes.DEFAULT_TYPE):
    screenshot = pyautogui.screenshot()
    file_path = tempfile.mktemp(suffix=".png")
    screenshot.save(file_path)
    await update.message.reply_photo(photo=open(file_path, 'rb'))

# Перевод в спящий режим
async def sleep_device(update: Update, context: ContextTypes.DEFAULT_TYPE):
    subprocess.call(["rundll32", "powrprof.dll,SetSuspendState", "0", "1", "0"])
    await update.message.reply_text("Устройство переводится в спящий режим.")

# Проверка уровня чернил
async def ink_level(update: Update, context: ContextTypes.DEFAULT_TYPE):
    printer_name = win32print.GetDefaultPrinter()
    await update.message.reply_text(f"Проверка уровня чернил для принтера: {printer_name} (реализуйте логику)")

# Команда для отправки уведомления
async def notify(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if context.args:
        message = ' '.join(context.args)
        await update.message.reply_text(f"Уведомление: {message}")
        notification.notify(
            title='Уведомление',
            message=message,
            app_name='Ваше приложение',
            timeout=10
        )
    else:
        await update.message.reply_text("Пожалуйста, введите сообщение для уведомления.")

# Команда для установки таймера
async def timer(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if context.args:
        try:
            time_seconds = int(context.args[0])
            await update.message.reply_text(f"Таймер установлен на {time_seconds} секунд(ы).")
            await asyncio.sleep(time_seconds)
            await update.message.reply_text("Время вышло!")
            notification.notify(
                title='Таймер',
                message='Время вышло!',
                app_name='Ваше приложение',
                timeout=10
            )
        except ValueError:
            await update.message.reply_text("Пожалуйста, введите время в секундах.")
    else:
        await update.message.reply_text("Пожалуйста, укажите время в секундах.")

# Отмена настройки
async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Настройка отменена.")
    return ConversationHandler.END

# Команда для печати файла
async def print_file(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message.document:
        file = await update.message.document.get_file()
        file_path = f"downloads/{update.message.document.file_name}"
        os.makedirs(os.path.dirname(file_path), exist_ok=True)
        try:
            await file.download_to_drive(file_path)
            logger.info(f"Файл {file_path} загружен успешно.")
            print_document(file_path)
            await update.message.reply_text("Файл отправлен на печать.")
        except Exception as e:
            await update.message.reply_text(f"Ошибка при печати: {e}")
            logger.error(f"Ошибка при печати файла {file_path}: {e}")
    else:
        await update.message.reply_text("Пожалуйста, отправьте файл для печати.")

# Функция для печати документа
def print_document(file_path):
    try:
        file_extension = os.path.splitext(file_path)[1].lower()
        printer_name = win32print.GetDefaultPrinter()

        if file_extension in ['.jpg', '.jpeg', '.png', '.bmp']:
            print_image(file_path, printer_name)
        elif file_extension == '.pdf':
            print_pdf(file_path, printer_name)
        else:
            raise ValueError("Неподдерживаемый формат файла.")

    except Exception as e:
        logger.error(f"Ошибка при печати документа: {e}")
        raise

# Функция для печати изображений
def print_image(file_path, printer_name):
    hdc = win32ui.CreateDC("WINSPOOL", printer_name, None)
    hdc.StartDoc(file_path)
    hdc.StartPage()

    bmp = Image.open(file_path)
    dib = ImageWin.Dib(bmp)
    dib.draw(hdc.GetHandleOutput(), (0, 0, bmp.size[0], bmp.size[1]))

    hdc.EndPage()
    hdc.EndDoc()
    hdc.DeleteDC()

# Функция для печати PDF
def print_pdf(file_path, printer_name):
    subprocess.Popen(['start', '/MIN', 'AcroRd32.exe', '/t', file_path, printer_name], shell=True)

# Основная функция для запуска бота
def main():
    application = ApplicationBuilder().token(BOT_TOKEN).build()

    conv_handler = ConversationHandler(
        entry_points=[CommandHandler('start', start)],
        states={
            ASK_IP: [MessageHandler(filters.TEXT & ~filters.COMMAND, set_ip)],
            MAIN_MENU: [
                CommandHandler('open_website', open_website),
                CommandHandler('telegram', open_telegram),
                CommandHandler('whatsapp', open_whatsapp),
                CommandHandler('wake', wake_device),
                CommandHandler('shutdown', shutdown_device),
                CommandHandler('screenshot', screenshot),
                CommandHandler('sleep', sleep_device),
                CommandHandler('print', print_file),
                CommandHandler('ink_level', ink_level),
                CommandHandler('notify', notify),
                CommandHandler('timer', timer),
                CommandHandler('cancel', cancel),
            ],
        },
        fallbacks=[CommandHandler('cancel', cancel)],
    )

    application.add_handler(conv_handler)
    application.run_polling()

if __name__ == '__main__':
    main()
