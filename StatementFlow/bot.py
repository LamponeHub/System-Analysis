from telegram import Update, ForceReply
from telegram.ext import (
    Application, CommandHandler, MessageHandler, 
    ConversationHandler, filters, ContextTypes
)
from sqlalchemy.orm import Session
import database
import models
import auth
from config import settings
from pdf_generator import generate_statement_pdf
import io

# States for conversation
NAME, ADDRESS, DEPARTMENT, TITLE, DESCRIPTION = range(5)

# Temporary storage for user data
user_data_temp = {}

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "👮 Добро пожаловать в StatementFlow Bot!\n\n"
        "Я помогу вам составить заявление в правоохранительные органы.\n\n"
        "Для начала отправьте мне ваше **ФИО** полностью.",
        parse_mode='Markdown'
    )
    return NAME

async def get_name(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_data_temp[update.effective_user.id] = {'name': update.message.text}
    await update.message.reply_text(
        f"✅ Принято: {update.message.text}\n\n"
        "Теперь отправьте ваш **адрес проживания**."
    )
    return ADDRESS

async def get_address(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_data_temp[update.effective_user.id]['address'] = update.message.text
    await update.message.reply_text(
        "✅ Адрес сохранён.\n\n"
        "Куда подаём заявление?\n"
        "1️⃣ В Полицию (ОВД)\n"
        "2️⃣ В Прокуратуру\n"
        "3️⃣ В Суд\n\n"
        "Отправьте номер варианта."
    )
    return DEPARTMENT

async def get_department(update: Update, context: ContextTypes.DEFAULT_TYPE):
    departments = {
        '1': 'В Полицию (ОВД)',
        '2': 'В Прокуратуру',
        '3': 'В Суд'
    }
    dept = departments.get(update.message.text, 'В Полицию (ОВД)')
    user_data_temp[update.effective_user.id]['department'] = dept
    await update.message.reply_text(
        f"✅ Выбрано: {dept}\n\n"
        "Теперь отправьте **заголовок заявления**\n"
        "(например: О краже имущества)"
    )
    return TITLE

async def get_title(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_data_temp[update.effective_user.id]['title'] = update.message.text
    await update.message.reply_text(
        "✅ Заголовок сохранён.\n\n"
        "Теперь опишите **обстоятельства дела**.\n"
        "Можете отправлять несколько сообщений. Когда закончите, отправьте слово **ГОТОВО**."
    )
    return DESCRIPTION

async def get_description(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message.text.upper() == 'ГОТОВО':
        await generate_and_send_pdf(update, context)
        return ConversationHandler.END
    else:
        if 'description' not in user_data_temp[update.effective_user.id]:
            user_data_temp[update.effective_user.id]['description'] = ''
        user_data_temp[update.effective_user.id]['description'] += update.message.text + '\n'
        await update.message.reply_text("✅ Продолжайте описание или отправьте **ГОТОВО**")
        return DESCRIPTION

async def generate_and_send_pdf(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    data = user_data_temp.get(user_id, {})
    
    # Создаём временного пользователя или находим по telegram_id
    db = database.SessionLocal()
    try:
        user = db.query(models.User).filter(models.User.telegram_id == str(user_id)).first()
        if not user:
            # Создаём анонимного пользователя для бота
            username = f"telegram_{user_id}"
            user = models.User(
                username=username,
                hashed_password=auth.get_password_hash("bot_access"),
                telegram_id=str(user_id)
            )
            db.add(user)
            db.commit()
            db.refresh(user)
        
        # Создаём заявление
        statement = models.Statement(
            user_id=user.id,
            applicant_name=data.get('name', ''),
            applicant_address=data.get('address', ''),
            target_department=data.get('department', ''),
            title=data.get('title', ''),
            description=data.get('description', ''),
            status=models.StatementStatus.DRAFT
        )
        db.add(statement)
        db.commit()
        db.refresh(statement)
        
        # Генерируем PDF
        pdf_bytes = generate_statement_pdf(statement)
        
        # Отправляем файл
        await update.message.reply_document(
            document=io.BytesIO(pdf_bytes),
            filename=f"statement_{statement.id}.pdf",
            caption=f"✅ Ваше заявление готово!\n\n"
                    f"📄 ID: {statement.id}\n"
                    f"📊 Статус: {statement.status.value}\n\n"
                    f"Распечатайте и подайте в {statement.target_department}"
        )
        
        # Очищаем временные данные
        if user_id in user_data_temp:
            del user_data_temp[user_id]
            
    finally:
        db.close()

async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id in user_data_temp:
        del user_data_temp[update.effective_user.id]
    await update.message.reply_text("❌ Процесс создания заявления отменён.\n/started - начать заново")
    return ConversationHandler.END

async def status_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    db = database.SessionLocal()
    try:
        user = db.query(models.User).filter(models.User.telegram_id == str(update.effective_user.id)).first()
        if not user:
            await update.message.reply_text("У вас ещё нет заявлений. Используйте /start для создания.")
            return
        
        statements = db.query(models.Statement).filter(models.Statement.user_id == user.id).all()
        if not statements:
            await update.message.reply_text("У вас ещё нет заявлений.")
            return
        
        response = "📋 Ваши заявления:\n\n"
        for stmt in statements:
            status_emoji = {
                'draft': '📝',
                'submitted': '📤',
                'answered': '✅'
            }.get(stmt.status.value, '📄')
            response += f"{status_emoji} #{stmt.id} - {stmt.title}\n"
            response += f"   Статус: {stmt.status.value}\n"
            response += f"   Дата: {stmt.created_at.strftime('%d.%m.%Y')}\n\n"
        
        await update.message.reply_text(response)
    finally:
        db.close()

def run_bot():
    application = Application.builder().token(settings.TELEGRAM_BOT_TOKEN).build()
    
    conv_handler = ConversationHandler(
        entry_points=[CommandHandler('start', start)],
        states={
            NAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_name)],
            ADDRESS: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_address)],
            DEPARTMENT: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_department)],
            TITLE: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_title)],
            DESCRIPTION: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_description)],
        },
        fallbacks=[CommandHandler('cancel', cancel)],
    )
    
    application.add_handler(conv_handler)
    application.add_handler(CommandHandler('status', status_command))
    application.add_handler(CommandHandler('cancel', cancel))
    
    print("🤖 Бот запущен...")
    application.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == "__main__":
    run_bot()