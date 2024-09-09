#!/usr/bin/env python3
import argparse
import whois
import whois.parser
import concurrent.futures

def check_domain(domain):
    try:
        whois.whois(domain)
        return domain, 'occupied'
    except whois.parser.PywhoisError:
        return domain, 'free'
    except Exception as e:
        return domain, f'error: {e}'

def process_domains(domains, threads, free_file, occupied_file, errors_file):

    with open(free_file, 'a') as ff, open(occupied_file, 'a') as fo:
        with concurrent.futures.ThreadPoolExecutor(max_workers=threads) as executor:
            future_to_domain = {executor.submit(check_domain, domain): domain for domain in domains}
            for future in concurrent.futures.as_completed(future_to_domain):
                domain, status = future.result()
                if status == 'free':
                    print(f'FREE\t{domain}')
                    ff.write(f'{domain}\n')
                elif status == 'occupied':
                    print(f'OCCUPIED\t{domain}')
                    fo.write(f'{domain}\n')
                else:
                    print(f"ERROR\t{domain}\t{status}")
                    with open(errors_file, 'a') as fe:
                        fe.write(f'{domain}\t{status}\n')
    print('Done')

def main():
    parser = argparse.ArgumentParser(description="Check domain availability using whois.")
    parser.add_argument("-i", "--input", required=True, help="Path to the file with the list of domains.")
    parser.add_argument("-o", "--output-free", required=True, help="File to save free domains.")
    parser.add_argument("-b", "--output-busy", required=True, help="File to save occupied domains.")
    parser.add_argument("-e", "--output-errors", default="errors.list", help="File to save occupied domains.")
    parser.add_argument("--threads", type=int, default=4, help="Number of threads to use.")
    args = parser.parse_args()

    with open(args.input, 'r') as f:
        domains = [line.strip() for line in f if line.strip()]

    process_domains(domains, args.threads, args.output_free, args.output_busy, args.output_errors)

if __name__ == "__main__":
    main()
