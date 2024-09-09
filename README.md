# Domain Availability Checker

This script checks the availability of domains using `whois` and saves the results into different files for free, occupied, and error domains. It supports multi-threading to speed up the checking process.

## Requirements

Make sure you have Python 3 and the `python-whois` library installed. You can install the required library using:

```bash
pip install python-whois
```

## Usage

To run the script, use the following command:
```bash
python3 whois_check.py -i <input_file> -o <free_domains_file> -b <occupied_domains_file> [-e <errors_file>] [--threads <number_of_threads>]
```

### Arguments:

*   `-i, --input` (required): Path to the input file containing the list of domains to check.
*   `-o, --output-free` (required): Path to the file where free domains will be saved.
*   `-b, --output-busy` (required): Path to the file where occupied domains will be saved.
*   `-e, --output-errors` (optional, default: `errors.list`): Path to the file where any errors during the check will be saved.
*   `--threads` (optional, default: 4): Number of threads to use for the domain checking process.

### Example:

```bash
python3 whois_check.py -i domains.txt -o free_domains.txt -b occupied_domains.txt -e errors.txt --threads 10
```

In this example:

*   The script will check domains listed in `domains.txt`.
*   Free domains will be saved to `free_domains.txt`.
*   Occupied domains will be saved to `occupied_domains.txt`.
*   Any domains that return errors during the check will be saved to `errors.txt`.
*   The script will use 10 threads to perform the checks concurrently.

### Output:

*   **FREE Domains**: The domains that are available will be printed in the format `FREE domain_name` and written to the file specified with `-o`.
*   **OCCUPIED Domains**: The domains that are taken will be printed in the format `OCCUPIED domain_name` and written to the file specified with `-b`.
*   **ERRORS**: Any errors that occur during the domain check will be printed in the format `ERROR domain_name error_message` and saved in the file specified with `-e`.

### Example Input File:

`domains.txt`:
```
example.com
freesite.org
mynewdomain.io
...
```

## License

This project is open-source and available under the MIT License.%