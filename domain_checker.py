import whois
import whois.parser
import concurrent.futures
from typing import List, Tuple, Callable
import threading
import queue
import time
import socket
import random

class DomainChecker:
    def __init__(self, max_threads: int = 10, max_retries: int = 5, base_backoff: int = 2, jitter: bool = True):
        self.max_threads = max_threads
        self.max_retries = max_retries
        self.base_backoff = base_backoff
        self.jitter = jitter

    def check_domain(self, domain: str) -> Tuple[str, str]:
        """
        Check if a domain is free or occupied with enhanced retries on connection errors,
        including specific handling for error 54 (Connection reset by peer on Mac).
        Uses exponential backoff with optional jitter.
        Returns (domain, status) where status is 'free', 'occupied', or 'error: message'
        """
        for attempt in range(self.max_retries):
            try:
                info = whois.whois(domain)
                if info.domain_name:  # If whois returns info, it's likely occupied
                    return domain, 'occupied'
                else:
                    return domain, 'free'
            except whois.parser.PywhoisError:
                return domain, 'free'
            except (ConnectionResetError, socket.timeout, socket.error) as e:
                if e.errno == 54:  # Specific handling for error 54
                    error_msg = f'error 54: Connection reset by peer - {str(e)}'
                else:
                    error_msg = f'error: {str(e)}'
                if attempt < self.max_retries - 1:
                    backoff = self.base_backoff ** attempt
                    if self.jitter:
                        backoff += random.uniform(0, backoff)  # Add jitter for better distribution
                    time.sleep(backoff)
                    continue
                else:
                    return domain, error_msg
            except Exception as e:
                return domain, f'error: {str(e)}'
        return domain, 'error: max retries exceeded'

    def check_domains(self, domains: List[str], callback: Callable[[str, str], None] = None) -> List[Tuple[str, str]]:
        """
        Check multiple domains concurrently.
        If callback is provided, it will be called for each result as it completes.
        Returns list of (domain, status)
        """
        results = []
        with concurrent.futures.ThreadPoolExecutor(max_workers=self.max_threads) as executor:
            future_to_domain = {executor.submit(self.check_domain, domain): domain for domain in domains}
            for future in concurrent.futures.as_completed(future_to_domain):
                domain, status = future.result()
                if callback:
                    callback(domain, status)
                results.append((domain, status))
        return results

    def check_domains_async(self, domains: List[str], result_queue: queue.Queue, progress_callback: Callable[[int, int], None] = None):
        """
        Asynchronous version for GUI, puts results into a queue.
        Calls progress_callback(current, total) if provided.
        """
        total = len(domains)
        completed = 0
        lock = threading.Lock()

        def callback_wrapper(future):
            nonlocal completed
            domain = future_to_domain[future]
            try:
                _, status = future.result()
            except Exception as e:
                status = f'error: {str(e)}'
            result_queue.put((domain, status))
            with lock:
                completed += 1
                if progress_callback:
                    progress_callback(completed, total)

        with concurrent.futures.ThreadPoolExecutor(max_workers=self.max_threads) as executor:
            future_to_domain = {executor.submit(self.check_domain, domain): domain for domain in domains}
            for future in future_to_domain:
                future.add_done_callback(callback_wrapper)