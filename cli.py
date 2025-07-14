#!/usr/bin/env python3
import argparse
import sys
from domain_checker import DomainChecker
import time

def main():
    parser = argparse.ArgumentParser(description="Check domain availability using whois.")
    parser.add_argument("-i", "--input", help="Path to the file with the list of domains. If not provided, read from stdin.")
    parser.add_argument("-o", "--output-free", default="free_domains.txt", help="File to save free domains.")
    parser.add_argument("-b", "--output-occupied", default="occupied_domains.txt", help="File to save occupied domains.")
    parser.add_argument("-e", "--output-errors", default="errors.txt", help="File to save errors.")
    parser.add_argument("-a", "--output-all", default="all_domains.txt", help="File to save all domains with statuses.")
    parser.add_argument("-t", "--threads", type=int, default=10, help="Number of threads to use.")
    parser.add_argument("-r", "--retries", type=int, default=5, help="Max retries for connection errors.")
    parser.add_argument("--backoff", type=int, default=2, help="Base backoff for exponential retry (seconds).")
    parser.add_argument("--no-jitter", action="store_false", dest="jitter", help="Disable jitter in backoff.")
    parser.add_argument("--auto-retry-delay", type=int, default=60, help="Delay in seconds before auto-retrying errors (0 to disable).")
    parser.add_argument("--verbose", action="store_true", help="Print verbose output.")
    args = parser.parse_args()

    # Read domains
    if args.input:
        with open(args.input, 'r') as f:
            domains = [line.strip() for line in f if line.strip()]
    else:
        if sys.stdin.isatty():
            parser.print_help()
            print("\nNote: If no --input is provided, domains are read from stdin. Use pipe or redirect input.")
            sys.exit(0)
        else:
            print("Reading domains from stdin...")
            domains = [line.strip() for line in sys.stdin if line.strip()]

    if not domains:
        print("No domains provided.")
        sys.exit(1)

    checker = DomainChecker(max_threads=args.threads, max_retries=args.retries, base_backoff=args.backoff, jitter=args.jitter)

    def callback(domain, status):
        if args.verbose:
            if status == 'free':
                print(f"FREE\t{domain}")
            elif status == 'occupied':
                print(f"OCCUPIED\t{domain}")
            else:
                print(f"ERROR\t{domain}\t{status}")

    results = checker.check_domains(domains, callback=callback)

    # Auto-retry errors if enabled
    if args.auto_retry_delay > 0:
        error_domains = [domain for domain, status in results if status.startswith('error:')]
        if error_domains:
            print(f"Found {len(error_domains)} errors. Retrying after {args.auto_retry_delay} seconds...")
            time.sleep(args.auto_retry_delay)
            retry_results = checker.check_domains(error_domains, callback=callback)
            # Update original results
            retry_dict = dict(retry_results)
            results = [(domain, retry_dict.get(domain, status)) for domain, status in results]

    # Write to files
    with open(args.output_free, 'w') as ff, open(args.output_occupied, 'w') as fo, open(args.output_errors, 'w') as fe, open(args.output_all, 'w') as fa:
        for domain, status in results:
            fa.write(f"{domain}\t{status}\n")
            if status == 'free':
                ff.write(f"{domain}\n")
            elif status == 'occupied':
                fo.write(f"{domain}\n")
            else:
                fe.write(f"{domain}\t{status}\n")

    print("Checking complete. Results saved to files.")

if __name__ == "__main__":
    main()