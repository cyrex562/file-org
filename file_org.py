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
import shutil
from collections import defaultdict

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
            TextColumn("{task.completed}/{task.total} files"),
            TextColumn("| {task.fields[throughput]:.2f} files/sec"),
            TimeElapsedColumn(),
            TimeRemainingColumn(),
            transient=True
        ) as progress:
            task = progress.add_task(
                "Processing files", total=total_files, throughput=0.0
            )
            start_time = time.time()
            processed = 0
            with ThreadPoolExecutor(max_workers=workers) as executor:
                future_to_path = {executor.submit(process_file, path): path for path in file_paths}
                for future in as_completed(future_to_path):
                    result = future.result()
                    processed += 1
                    elapsed = time.time() - start_time
                    throughput = processed / elapsed if elapsed > 0 else 0.0
                    if result:
                        writer.writerow(result)
                    progress.update(task, advance=1, throughput=throughput)

    logging.info(f"File list saved to: {output_csv}")

cli.add_command(create_file_list)

@click.command()
@click.argument('csv_file', type=click.Path(exists=True, dir_okay=False))
@click.argument('duplicates_dir', type=click.Path())
def move_duplicates(csv_file, duplicates_dir):
    """Find duplicate xxhash values in CSV_FILE and move those files to DUPLICATES_DIR."""
    os.makedirs(duplicates_dir, exist_ok=True)

    # Read CSV and group by xxhash
    hash_to_files = defaultdict(list)
    with open(csv_file, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            hash_to_files[row['xxhash']].append(row['full_path'])

    # Find and move duplicates
    moved_count = 0
    for file_hash, files in hash_to_files.items():
        if len(files) > 1:
            # Keep the first file, move the rest
            for i, file_path in enumerate(files[1:], start=1):
                if not os.path.exists(file_path):
                    logging.warning(f"File not found: {file_path}")
                    continue
                base_name = os.path.basename(file_path)
                name, ext = os.path.splitext(base_name)
                dest_name = base_name
                dest_path = os.path.join(duplicates_dir, dest_name)
                n = 1
                # Append a number if file exists
                while os.path.exists(dest_path):
                    dest_name = f"{name}_{n}{ext}"
                    dest_path = os.path.join(duplicates_dir, dest_name)
                    n += 1
                shutil.move(file_path, dest_path)
                logging.info(f"Moved duplicate: {file_path} -> {dest_path}")
                moved_count += 1
    logging.info(f"Total duplicates moved: {moved_count}")

cli.add_command(move_duplicates)

if __name__ == '__main__':
    cli()