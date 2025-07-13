import click
import os
import csv
import time
import xxhash
import logging
from tqdm import tqdm
from rich.logging import RichHandler
from rich.progress import Progress, SpinnerColumn, BarColumn, TextColumn, TimeElapsedColumn, TimeRemainingColumn, TaskProgressColumn, TransferSpeedColumn
from concurrent.futures import ThreadPoolExecutor, as_completed

# Configure rich logging
logging.basicConfig(
    level=logging.INFO,
    format='%(message)s',
    datefmt='%Y-%m-%d %H:%M:%S',
    handlers=[RichHandler()]
)


@click.group()
def cli():
    pass

@click.command()
@click.argument('directory', type=click.Path(exists=True, file_okay=False, dir_okay=True))
@click.argument('output_csv', type=click.Path())
@click.option('--workers', default=4, show_default=True, help='Number of worker threads for scanning files.')
def create_file_list(directory, output_csv, workers):
    """Scan DIRECTORY and create a CSV file with file details."""
    logging.info(f"Scanning directory: {directory}")

    # Collect all file paths first
    file_paths = []
    for root, _, files in os.walk(directory):
        for file in files:
            file_paths.append(os.path.join(root, file))
    total_files = len(file_paths)
    logging.info(f"Total files to process: {total_files}")

    def process_file(full_path):
        try:
            size = os.path.getsize(full_path)
            creation_time = time.ctime(os.path.getctime(full_path))
            modification_time = time.ctime(os.path.getmtime(full_path))
            hasher = xxhash.xxh64()
            with open(full_path, 'rb') as f:
                for chunk in iter(lambda: f.read(4096), b""):
                    hasher.update(chunk)
            file_hash = hasher.hexdigest()
            return {
                'full_path': full_path,
                'size': size,
                'creation_time': creation_time,
                'modification_time': modification_time,
                'xxhash': file_hash
            }
        except Exception as e:
            logging.error(f"Error processing {full_path}: {e}")
            return None

    with open(output_csv, 'w', newline='', encoding='utf-8') as csvfile:
        fieldnames = ['full_path', 'size', 'creation_time', 'modification_time', 'xxhash']
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()

        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            BarColumn(),
            TaskProgressColumn(),
            TransferSpeedColumn(),
            TimeElapsedColumn(),
            TimeRemainingColumn(),
            transient=True
        ) as progress:
            task = progress.add_task("Processing files", total=total_files)
            results = []
            with ThreadPoolExecutor(max_workers=workers) as executor:
                future_to_path = {executor.submit(process_file, path): path for path in file_paths}
                for future in as_completed(future_to_path):
                    result = future.result()
                    if result:
                        writer.writerow(result)
                    progress.update(task, advance=1)

    logging.info(f"File list saved to: {output_csv}")

cli.add_command(create_file_list)

if __name__ == '__main__':
    cli()