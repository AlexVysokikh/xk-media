#!/usr/bin/env python3
"""
Generate secure SECRET_KEY for production.
Сгенерировать безопасный SECRET_KEY для production.
"""

import secrets

key = secrets.token_hex(32)
print("\n🔐 Generated SECRET_KEY for .env:\n")
print(f"SECRET_KEY={key}")
print("\n✅ Copy this line to your .env file\n")
