from log_management.log_management import LogManagement
from main import celery

@celery.task(name='compress_log_files')
def compress_old_log_files():
    """
    Compress log files older than 7 days
    """
    log_management = LogManagement(log_dir='logs', compress_older_than=1)
    try:
        log_management.compress_old_logs()
        return "Log files compressed successfully"
    except Exception as e:
        log_management.logger.error(f"Error compressing log files: {e}")
        return "Error compressing log files"

@celery.task(name='aggregate_logs')
def aggregate_logs():
    """
    Aggregate logs into daily summaries
    """
    log_management = LogManagement(log_dir='logs', aggregation_days=7)
    try:
        log_management.aggregate_logs()
        return "Logs aggregated successfully"
    except Exception as e:
        log_management.logger.error(f"Error aggregating logs: {e}")
        return "Error aggregating logs"
