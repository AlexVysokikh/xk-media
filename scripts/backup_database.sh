#!/bin/bash
# Скрипт для резервного копирования базы данных PostgreSQL

set -e

BACKUP_DIR="/var/backups/xk-media"
DB_NAME="xk_media"
DB_USER="xk_media_user"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
BACKUP_FILE="$BACKUP_DIR/xk_media_backup_$TIMESTAMP.sql"
RETENTION_DAYS=30

# Создание директории для бэкапов
mkdir -p "$BACKUP_DIR"

echo "💾 Создание резервной копии базы данных..."

# Получение пароля из .env
DB_PASSWORD=$(grep DATABASE_URL /var/www/xk-media-backend/.env | sed 's/.*:\/\/[^:]*:\([^@]*\)@.*/\1/')

# Создание бэкапа
export PGPASSWORD="$DB_PASSWORD"
pg_dump -h localhost -U "$DB_USER" -d "$DB_NAME" -F c -f "${BACKUP_FILE%.sql}.dump" 2>/dev/null || \
pg_dump -h localhost -U "$DB_USER" -d "$DB_NAME" > "$BACKUP_FILE"
unset PGPASSWORD

# Сжатие бэкапа
if [ -f "$BACKUP_FILE" ]; then
    gzip "$BACKUP_FILE"
    BACKUP_FILE="${BACKUP_FILE}.gz"
fi

if [ -f "${BACKUP_FILE%.sql}.dump" ]; then
    gzip "${BACKUP_FILE%.sql}.dump"
    BACKUP_FILE="${BACKUP_FILE%.sql}.dump.gz"
fi

echo "✅ Резервная копия создана: $BACKUP_FILE"

# Удаление старых бэкапов (старше RETENTION_DAYS дней)
echo "🧹 Удаление старых бэкапов (старше $RETENTION_DAYS дней)..."
find "$BACKUP_DIR" -name "xk_media_backup_*" -type f -mtime +$RETENTION_DAYS -delete

echo "✅ Очистка завершена"

# Показываем размер бэкапа
if [ -f "$BACKUP_FILE" ]; then
    SIZE=$(du -h "$BACKUP_FILE" | cut -f1)
    echo "📊 Размер бэкапа: $SIZE"
fi
