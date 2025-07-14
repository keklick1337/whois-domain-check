# Domain Availability Checker

This project provides tools to check the availability of domain names using the `whois` protocol. It includes a command-line interface (CLI) and a graphical user interface (GUI) for checking multiple domains concurrently with multi-threading support. Results are categorized into free, occupied, and error domains, with configurable retries for handling connection issues.

## Features

- **Multi-threaded Checking**: Speeds up the process by checking domains in parallel.
- **Error Handling with Retries**: Automatically retries on connection errors (e.g., timeouts, resets) with exponential backoff and optional jitter.
- **Auto-Retry for Errors**: Optionally retries failed domains after a delay.
- **CLI Mode**: Scriptable for batch processing.
- **GUI Mode**: User-friendly interface with real-time progress, pause/resume, cancel, and result saving.
- **Duplicate Detection**: In GUI, ignores duplicate domains when loading files.
- **Output Files**: Saves free, occupied, errors, and all results to separate files.

## Requirements

- Python 3.8 or higher.
- Required libraries:
  - `python-whois` for domain checking.
  - Tkinter (usually included with Python) for the GUI.

Install the required library:

```bash
pip install python-whois
```

## Files

- `domain_checker.py`: Core logic for domain checking.
- `cli.py`: Command-line interface.
- `gui.py`: Graphical user interface.

## CLI Usage

Run the CLI with:

```bash
./cli.py -i <input_file> [options]
```

If no input file is provided, it reads from stdin.

### Arguments

- `-i, --input`: Path to the file with the list of domains (one per line). If omitted, reads from stdin.
- `-o, --output-free` (default: `free_domains.txt`): File to save free domains.
- `-b, --output-occupied` (default: `occupied_domains.txt`): File to save occupied domains.
- `-e, --output-errors` (default: `errors.txt`): File to save domains with errors (format: `domain\tstatus`).
- `-a, --output-all` (default: `all_domains.txt`): File to save all domains with statuses (format: `domain\tstatus`).
- `-t, --threads` (default: 10): Number of threads to use.
- `-r, --retries` (default: 10): Max retries for connection errors.
- `--backoff` (default: 2): Base backoff time (seconds) for exponential retry.
- `--no-jitter`: Disable jitter in backoff (enabled by default).
- `--auto-retry-delay` (default: 60): Delay (seconds) before auto-retrying errors (0 to disable).
- `--verbose`: Print detailed output during checking.

### Example

```bash
./cli.py -i domains.txt -o free.txt -b occupied.txt -e errors.txt --threads 20 --retries 15 --verbose
```

This checks domains from `domains.txt` using 20 threads, retries up to 15 times on errors, and prints verbose output.

## GUI Usage

Run the GUI with:

```bash
./gui.py
```

### Features in GUI

- **Load Domain List**: Select a TXT file to load domains (duplicates are ignored with a notification).
- **Check Domains**: Start checking with configurable threads, retries, backoff, jitter, and auto-retry delay.
- **Pause/Resume**: Toggle checking process.
- **Cancel**: Stop the process and mark remaining as "Cancelled".
- **Recheck Errors**: Re-check only errored domains.
- **Save Results**: Save free, occupied, errors, and all to separate files.
- **Clear**: Reset the table.
- **Real-time Updates**: Progress bar, counters for free/occupied/errors, and status label.
- **Scrollable Table**: Displays domains and statuses with vertical/horizontal scrollbars (trackpad support on Mac).

### Configuration

- Threads (default: 10)
- Retries (default: 10)
- Backoff (default: 2)
- Jitter (enabled by default)
- Auto-Retry Delay (default: 60 seconds)

## Example Input File

`domains.txt`:

```
example.com
freesite.org
mynewdomain.io
```

## Output

- **Free Domains**: Available domains.
- **Occupied Domains**: Registered domains.
- **Errors**: Domains with check failures (e.g., connection issues), saved with error messages.
- **All**: Complete list with statuses.

In CLI, verbose mode prints `FREE/OCCUPIED/ERROR` lines.

In GUI, results are shown in a table and counters.

## Notes

- The tool handles common errors like connection resets (error 54) with increased retries.
- For large lists, adjust threads/retries based on system resources to avoid rate limiting.

## License

This project is open-source and available under the MIT License.