import glob
import gzip
import json
import logging
import os
import shutil
from datetime import datetime, timedelta


class LogManagement:
    def __init__(self, log_dir: str, compress_older_than: int = 7, aggregation_days: int = 7):
        self.log_dir = log_dir
        self.compress_older_than = compress_older_than
        self.aggregation_days = aggregation_days

    def fetch_log_files(self):
        """Fetch log files from the log directory"""
        log_files = []
        for log_file in glob.glob(f"{self.log_dir}/*"):
            log_files.append(log_file)
        return log_files

    def compress_old_logs(self):
        """Compress log files older than specified days"""
        cutoff_date = datetime.now() - timedelta(days=self.compress_older_than)

        for log_file in self.fetch_log_files():
            # Skip if already compressed
            if log_file.endswith('.gz'):
                continue

            try:
                file_mtime = datetime.fromtimestamp(os.path.getmtime(log_file))

                if file_mtime < cutoff_date:
                    # Compress the file
                    with open(log_file, 'rb') as f_in:
                        with gzip.open(f'{log_file}.gz', 'wb') as f_out:
                            shutil.copyfileobj(f_in, f_out)

                    # Remove the original file
                    os.remove(log_file)
                    logging.getLogger('log_management').info(f"Compressed: {log_file}")

            except Exception as e:
                logging.getLogger('log_management').error(f"Error compressing {log_file}: {e}")

    def aggregate_logs(self):
        """
        Aggregate logs across multiple files into daily summaries
        """
        log_groups = self.group_logs_by_date()
        self.aggregate_and_remove_logs(log_groups)

    def group_logs_by_date(self):
        """
        Group logs by date
        """
        log_groups = {}
        for log_file in self.fetch_log_files():
            try:
                if log_file.endswith('.gz'):
                    continue

                file_mtime = datetime.fromtimestamp(os.path.getmtime(log_file))
                if datetime.now() - file_mtime > timedelta(days=self.aggregation_days):
                    date_key = file_mtime.strftime("%Y-%m-%d")
                    if date_key not in log_groups:
                        log_groups[date_key] = []
                    log_groups[date_key].append(log_file)
            except Exception as e:
                logging.getLogger('log_management').error(f"Error processing {log_file}: {e}")
        return log_groups

    def aggregate_and_remove_logs(self, log_groups):
        """
        Aggregate logs by date and remove original files
        """
        for date, files in log_groups.items():
            try:
                aggregate_filename = os.path.join(self.log_dir, f"aggregate_{date}.json")
                aggregated_logs = self.combine_logs(files)
                self.write_aggregated_logs(aggregate_filename, aggregated_logs)
                self.remove_original_files(files)
                logging.getLogger('log_management').info(f"Aggregated logs for {date}")
            except Exception as e:
                logging.getLogger('log_management').error(f"Error aggregating logs for {date}: {e}")

    def combine_logs(self, files):
        """
        Combine logs from multiple files
        """
        aggregated_logs = []
        for file in files:
            with open(file, 'r') as f:
                for line in f:
                    try:
                        log_entry = json.loads(line.strip())
                        aggregated_logs.append(log_entry)
                    except json.JSONDecodeError:
                        pass
        aggregated_logs.sort(key=lambda x: x.get('timestamp', ''))
        return aggregated_logs

    def write_aggregated_logs(self, filename, logs):
        """
        Write aggregated logs to a file
        """
        with open(filename, 'w') as f:
            json.dump(logs, f, indent=2)

    def remove_original_files(self, files):
        """
        Remove original log files
        """
        for file in files:
            os.remove(file)

    def cleanup_aggregate_logs(self, older_than_days: int):
        """
        Cleanup aggregate logs older than specified days
        """
        cutoff_date = datetime.now() - timedelta(days=older_than_days)

        for log_file in glob.glob(f"{self.log_dir}/aggregate_*.json"):
            try:
                file_mtime = datetime.fromtimestamp(os.path.getmtime(log_file))

                if file_mtime < cutoff_date:
                    os.remove(log_file)
                    logging.getLogger('log_management').info(f"Removed: {log_file}")

            except Exception as e:
                logging.getLogger('log_management').error(f"Error removing {log_file}: {e}")

    def cleanup_compressed_logs(self, older_than_days: int):
        """
        Cleanup compressed logs older than specified days
        """
        cutoff_date = datetime.now() - timedelta(days=older_than_days)

        for log_file in glob.glob(f"{self.log_dir}/*.gz"):
            try:
                file_mtime = datetime.fromtimestamp(os.path.getmtime(log_file))

                if file_mtime < cutoff_date:
                    os.remove(log_file)
                    logging.getLogger('log_management').info(f"Removed: {log_file}")

            except Exception as e:
                logging.getLogger('log_management').error(f"Error removing {log_file}: {e}")

    logger = logging.getLogger('log_management')
