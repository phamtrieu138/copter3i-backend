import os
import glob
import subprocess
import logging
from datetime import datetime
from config import settings

logger = logging.getLogger("copter3i")

BACKUP_DIR = "backups"
MAX_BACKUPS = 20

def perform_backup():
    """
    Thực hiện backup database theo ngày.
    Chỉ giữ lại tối đa MAX_BACKUPS file theo nguyên tắc FIFO.
    """
    try:
        os.makedirs(BACKUP_DIR, exist_ok=True)
        now = datetime.now()
        # Tên file ghi rõ ngày tháng năm
        timestamp = now.strftime("%Y_%m_%d_%H%M%S")
        filename = f"{settings.DB_NAME}_{timestamp}.sql"
        filepath = os.path.join(BACKUP_DIR, filename)

        env = os.environ.copy()
        if settings.DB_PASSWORD:
            env["MYSQL_PWD"] = settings.DB_PASSWORD
            
        cmd = [
            "mysqldump",
            "-h", settings.DB_HOST,
            "-P", str(settings.DB_PORT),
            "-u", settings.DB_USER,
            settings.DB_NAME
        ]
        
        logger.info(f"Starting database backup: {filepath}")
        
        with open(filepath, "w", encoding="utf-8") as f:
            subprocess.run(cmd, env=env, stdout=f, check=True)
            
        logger.info(f"Database backup successful: {filepath}")
        
        # Xóa các file backup cũ (FIFO)
        backup_files = glob.glob(os.path.join(BACKUP_DIR, f"{settings.DB_NAME}_*.sql"))
        backup_files.sort(key=os.path.getctime)
        
        if len(backup_files) > MAX_BACKUPS:
            files_to_delete = backup_files[:-MAX_BACKUPS]
            for file_to_delete in files_to_delete:
                try:
                    os.remove(file_to_delete)
                    logger.info(f"Deleted old backup: {file_to_delete}")
                except Exception as e:
                    logger.error(f"Failed to delete old backup {file_to_delete}: {e}")

    except subprocess.CalledProcessError as e:
        logger.error(f"mysqldump failed. Make sure mysqldump is installed and in PATH. Error: {e}")
    except Exception as e:
        logger.error(f"Backup process failed: {e}", exc_info=True)
