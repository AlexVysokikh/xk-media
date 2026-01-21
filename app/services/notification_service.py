"""
Сервис для отправки уведомлений на email и в Telegram.
"""

import smtplib
import httpx
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import Optional
from datetime import datetime

from app.settings import settings


class NotificationService:
    """Сервис для отправки уведомлений."""
    
    @staticmethod
    async def send_email(
        to_email: str,
        subject: str,
        body_html: str,
        body_text: Optional[str] = None
    ) -> bool:
        """
        Отправить email.
        
        Args:
            to_email: Email получателя
            subject: Тема письма
            body_html: HTML тело письма
            body_text: Текстовое тело письма (опционально)
        
        Returns:
            True если отправлено успешно, False иначе
        """
        if not settings.SMTP_HOST or not settings.SMTP_USER:
            print("SMTP not configured, skipping email notification")
            return False
        
        try:
            msg = MIMEMultipart('alternative')
            msg['Subject'] = subject
            msg['From'] = settings.SMTP_FROM_EMAIL or settings.SMTP_USER
            msg['To'] = to_email
            
            if body_text:
                msg.attach(MIMEText(body_text, 'plain', 'utf-8'))
            msg.attach(MIMEText(body_html, 'html', 'utf-8'))
            
            with smtplib.SMTP(settings.SMTP_HOST, settings.SMTP_PORT) as server:
                if settings.SMTP_USE_TLS:
                    server.starttls()
                if settings.SMTP_USER and settings.SMTP_PASSWORD:
                    server.login(settings.SMTP_USER, settings.SMTP_PASSWORD)
                server.send_message(msg)
            
            print(f"Email sent to {to_email}: {subject}")
            return True
        except Exception as e:
            print(f"Error sending email to {to_email}: {e}")
            import traceback
            traceback.print_exc()
            return False
    
    @staticmethod
    async def send_telegram(
        message: str,
        parse_mode: str = "HTML"
    ) -> bool:
        """
        Отправить сообщение в Telegram.
        
        Args:
            message: Текст сообщения
            parse_mode: Режим парсинга (HTML или Markdown)
        
        Returns:
            True если отправлено успешно, False иначе
        """
        if not settings.TELEGRAM_BOT_TOKEN or not settings.TELEGRAM_CHAT_ID:
            print("Telegram not configured, skipping Telegram notification")
            return False
        
        try:
            url = f"https://api.telegram.org/bot{settings.TELEGRAM_BOT_TOKEN}/sendMessage"
            data = {
                "chat_id": settings.TELEGRAM_CHAT_ID,
                "text": message,
                "parse_mode": parse_mode
            }
            
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.post(url, json=data)
                response.raise_for_status()
            
            print(f"Telegram message sent to chat {settings.TELEGRAM_CHAT_ID}")
            return True
        except Exception as e:
            print(f"Error sending Telegram message: {e}")
            import traceback
            traceback.print_exc()
            return False
    
    @staticmethod
    async def notify_new_user(
        email: str,
        role: str,
        first_name: Optional[str] = None,
        last_name: Optional[str] = None,
        company_name: Optional[str] = None
    ):
        """
        Отправить уведомление о новом пользователе.
        
        Args:
            email: Email пользователя
            role: Роль пользователя
            first_name: Имя
            last_name: Фамилия
            company_name: Название компании
        """
        role_names = {
            "advertiser": "Рекламодатель",
            "venue": "Площадка показа",
            "admin": "Администратор"
        }
        role_name = role_names.get(role, role)
        
        user_name = f"{first_name or ''} {last_name or ''}".strip() or email
        if company_name:
            user_name += f" ({company_name})"
        
        # Email уведомление
        email_subject = f"Новая регистрация: {role_name}"
        email_body = f"""
        <html>
        <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
            <h2 style="color: #e94560;">Новая регистрация на XK Media</h2>
            <p><strong>Роль:</strong> {role_name}</p>
            <p><strong>Пользователь:</strong> {user_name}</p>
            <p><strong>Email:</strong> {email}</p>
            <p><strong>Дата:</strong> {datetime.now().strftime('%d.%m.%Y %H:%M:%S')}</p>
        </body>
        </html>
        """
        
        admin_email = settings.ADMIN_EMAIL or "admin@xk-media.ru"
        await NotificationService.send_email(admin_email, email_subject, email_body)
        
        # Telegram уведомление
        telegram_message = f"""
<b>🆕 Новая регистрация</b>

<b>Роль:</b> {role_name}
<b>Пользователь:</b> {user_name}
<b>Email:</b> {email}
<b>Дата:</b> {datetime.now().strftime('%d.%m.%Y %H:%M:%S')}
        """.strip()
        
        await NotificationService.send_telegram(telegram_message)
    
    @staticmethod
    async def notify_advertiser_request(
        name: str,
        email: str,
        phone: str,
        company: Optional[str] = None,
        description: Optional[str] = None
    ):
        """
        Отправить уведомление о заявке рекламодателя с лендинга.
        
        Args:
            name: Имя
            email: Email
            phone: Телефон
            company: Компания
            description: Описание
        """
        # Email уведомление
        email_subject = "Новая заявка: Хочу рекламировать"
        email_body = f"""
        <html>
        <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
            <h2 style="color: #e94560;">Новая заявка с сайта</h2>
            <p><strong>Тип заявки:</strong> Хочу рекламировать свои услуги/товары локально</p>
            <p><strong>Имя:</strong> {name}</p>
            <p><strong>Email:</strong> {email}</p>
            <p><strong>Телефон:</strong> {phone}</p>
            {f'<p><strong>Компания:</strong> {company}</p>' if company else ''}
            {f'<p><strong>Описание:</strong> {description}</p>' if description else ''}
            <p><strong>Дата:</strong> {datetime.now().strftime('%d.%m.%Y %H:%M:%S')}</p>
        </body>
        </html>
        """
        
        admin_email = settings.ADMIN_EMAIL or "admin@xk-media.ru"
        await NotificationService.send_email(admin_email, email_subject, email_body)
        
        # Telegram уведомление
        telegram_message = f"""
<b>📢 Новая заявка: Хочу рекламировать</b>

<b>Имя:</b> {name}
<b>Email:</b> {email}
<b>Телефон:</b> {phone}
{f'<b>Компания:</b> {company}' if company else ''}
{f'<b>Описание:</b> {description}' if description else ''}
<b>Дата:</b> {datetime.now().strftime('%d.%m.%Y %H:%M:%S')}
        """.strip()
        
        await NotificationService.send_telegram(telegram_message)
    
    @staticmethod
    async def notify_venue_request(
        name: str,
        email: str,
        phone: str,
        venue_name: Optional[str] = None,
        description: Optional[str] = None
    ):
        """
        Отправить уведомление о заявке площадки с лендинга.
        
        Args:
            name: Имя
            email: Email
            phone: Телефон
            venue_name: Название заведения
            description: Описание
        """
        # Email уведомление
        email_subject = "Новая заявка: Хочу получать доход"
        email_body = f"""
        <html>
        <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
            <h2 style="color: #e94560;">Новая заявка с сайта</h2>
            <p><strong>Тип заявки:</strong> Хочу получать дополнительный доход</p>
            <p><strong>Имя:</strong> {name}</p>
            <p><strong>Email:</strong> {email}</p>
            <p><strong>Телефон:</strong> {phone}</p>
            {f'<p><strong>Заведение:</strong> {venue_name}</p>' if venue_name else ''}
            {f'<p><strong>Описание:</strong> {description}</p>' if description else ''}
            <p><strong>Дата:</strong> {datetime.now().strftime('%d.%m.%Y %H:%M:%S')}</p>
        </body>
        </html>
        """
        
        admin_email = settings.ADMIN_EMAIL or "admin@xk-media.ru"
        await NotificationService.send_email(admin_email, email_subject, email_body)
        
        # Telegram уведомление
        telegram_message = f"""
<b>💰 Новая заявка: Хочу получать доход</b>

<b>Имя:</b> {name}
<b>Email:</b> {email}
<b>Телефон:</b> {phone}
{f'<b>Заведение:</b> {venue_name}' if venue_name else ''}
{f'<b>Описание:</b> {description}' if description else ''}
<b>Дата:</b> {datetime.now().strftime('%d.%m.%Y %H:%M:%S')}
        """.strip()
        
        await NotificationService.send_telegram(telegram_message)
