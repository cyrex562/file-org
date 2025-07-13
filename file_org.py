import click
import os
import csv
import time
import xxhash
import logging
from tqdm import tqdm

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')


@click.group()
def cli():
    pass

@click.command()
@click.argument('directory', type=click.Path(exists=True, file_okay=False, dir_okay=True))
@click.argument('output_csv', type=click.Path())
def create_file_list(directory, output_csv):
    """Scan DIRECTORY and create a CSV file with file details."""
    logging.info(f"Scanning directory: {directory}")

    # Count total files for progress bar
    total_files = sum(len(files) for _, _, files in os.walk(directory))
    logging.info(f"Total files to process: {total_files}")

    with open(output_csv, 'w', newline='', encoding='utf-8') as csvfile:
        fieldnames = ['full_path', 'size', 'creation_time', 'modification_time', 'xxhash']
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()

        with tqdm(total=total_files, desc="Processing files", unit="file") as pbar:
            for root, _, files in os.walk(directory):
                for file in files:
                    full_path = os.path.join(root, file)
                    size = os.path.getsize(full_path)
                    creation_time = time.ctime(os.path.getctime(full_path))
                    modification_time = time.ctime(os.path.getmtime(full_path))

                    # Calculate xxhash
                    hasher = xxhash.xxh64()
                    with open(full_path, 'rb') as f:
                        for chunk in iter(lambda: f.read(4096), b""):
                            hasher.update(chunk)
                    file_hash = hasher.hexdigest()

                    writer.writerow({
                        'full_path': full_path,
                        'size': size,
                        'creation_time': creation_time,
                        'modification_time': modification_time,
                        'xxhash': file_hash
                    })

                    pbar.update(1)
                    logging.debug(f"Processed file: {full_path}")

    logging.info(f"File list saved to: {output_csv}")

cli.add_command(create_file_list)

if __name__ == '__main__':
    cli()