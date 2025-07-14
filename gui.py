#!/usr/bin/env python3
import tkinter as tk
from tkinter import filedialog, messagebox, ttk
import queue
import threading
from domain_checker import DomainChecker
import time
import concurrent.futures

class DomainCheckerGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("Domain Availability Checker by Keklick1337")
        self.root.geometry("800x600")
        self.root.minsize(800, 600)  # Set minimum window size to prevent elements from hiding on resize
        self.result_queue = queue.Queue()
        self.domains = []
        self.running = False
        self.paused = False
        self.cancelled = False
        self.domain_to_item = {}  # Map domain to Treeview item ID
        self.results = {}  # Domain to status
        self.executor = None  # For pausing/resuming
        self.future_to_domain = {}
        self.completed = 0
        self.total = 0
        self.auto_retry_delay = 60  # Seconds before auto-retrying errors

        # Main frame
        self.main_frame = ttk.Frame(root, padding="10")
        self.main_frame.pack(fill=tk.BOTH, expand=True)

        # Buttons frame
        self.buttons_frame = ttk.Frame(self.main_frame)
        self.buttons_frame.pack(fill=tk.X, pady=5)

        self.load_button = ttk.Button(self.buttons_frame, text="Load Domain List", command=self.load_file)
        self.load_button.pack(side=tk.LEFT, padx=5)

        self.check_button = ttk.Button(self.buttons_frame, text="Check Domains", command=self.start_check)
        self.check_button.pack(side=tk.LEFT, padx=5)

        self.control_button = ttk.Button(self.buttons_frame, text="Pause", command=self.toggle_pause_resume, state=tk.DISABLED)
        self.control_button.pack(side=tk.LEFT, padx=5)

        self.cancel_button = ttk.Button(self.buttons_frame, text="Cancel", command=self.cancel_check, state=tk.DISABLED)
        self.cancel_button.pack(side=tk.LEFT, padx=5)

        self.recheck_button = ttk.Button(self.buttons_frame, text="Recheck Errors", command=self.recheck_errors, state=tk.DISABLED)
        self.recheck_button.pack(side=tk.LEFT, padx=5)

        self.save_button = ttk.Button(self.buttons_frame, text="Save Results", command=self.save_results, state=tk.DISABLED)
        self.save_button.pack(side=tk.LEFT, padx=5)

        self.clear_button = ttk.Button(self.buttons_frame, text="Clear", command=self.clear_table)
        self.clear_button.pack(side=tk.LEFT, padx=5)

        # Progress frame
        self.progress_frame = ttk.Frame(self.main_frame)
        self.progress_frame.pack(fill=tk.X, pady=10)

        self.progress = ttk.Progressbar(self.progress_frame, orient="horizontal", length=300, mode="determinate")
        self.progress.pack(side=tk.LEFT, fill=tk.X, expand=True)

        self.progress_label = ttk.Label(self.progress_frame, text="0/0 domains checked")
        self.progress_label.pack(side=tk.LEFT, padx=10)

        # Counters frame
        self.counters_frame = ttk.Frame(self.main_frame)
        self.counters_frame.pack(fill=tk.X, pady=5)

        self.free_label = ttk.Label(self.counters_frame, text="Free: 0")
        self.free_label.pack(side=tk.LEFT, padx=10)

        self.occupied_label = ttk.Label(self.counters_frame, text="Occupied: 0")
        self.occupied_label.pack(side=tk.LEFT, padx=10)

        self.errors_label = ttk.Label(self.counters_frame, text="Errors: 0")
        self.errors_label.pack(side=tk.LEFT, padx=10)

        self.status_label = ttk.Label(self.main_frame, text="Ready")
        self.status_label.pack(pady=5)

        # Treeview frame for scrollbars
        self.tree_frame = ttk.Frame(self.main_frame)
        self.tree_frame.pack(fill=tk.BOTH, expand=True, pady=5)

        self.tree = ttk.Treeview(self.tree_frame, columns=("Domain", "Status"), show="headings", height=20)
        self.tree.heading("Domain", text="Domain")
        self.tree.heading("Status", text="Status")
        self.tree.column("Domain", width=400)
        self.tree.column("Status", width=200)
        self.tree.grid(row=0, column=0, sticky="nsew")

        # Vertical scrollbar
        scrollbar_y = ttk.Scrollbar(self.tree_frame, orient=tk.VERTICAL, command=self.tree.yview)
        scrollbar_y.grid(row=0, column=1, sticky="ns")
        self.tree.configure(yscrollcommand=scrollbar_y.set)

        # Horizontal scrollbar
        scrollbar_x = ttk.Scrollbar(self.tree_frame, orient=tk.HORIZONTAL, command=self.tree.xview)
        scrollbar_x.grid(row=1, column=0, sticky="ew")
        self.tree.configure(xscrollcommand=scrollbar_x.set)

        # Enable trackpad scrolling on Mac by binding mouse wheel
        self.tree.bind("<MouseWheel>", self.on_mouse_wheel)  # For vertical
        self.tree.bind("<Shift-MouseWheel>", self.on_shift_mouse_wheel)  # For horizontal on Mac

        self.tree_frame.rowconfigure(0, weight=1)
        self.tree_frame.columnconfigure(0, weight=1)

        # Bottom frame for threads and retries
        self.bottom_frame = ttk.Frame(self.main_frame)
        self.bottom_frame.pack(fill=tk.X, pady=5)

        self.threads_label = ttk.Label(self.bottom_frame, text="Threads:")
        self.threads_label.pack(side=tk.LEFT, padx=5)

        self.threads_var = tk.StringVar(value="10")
        self.threads_entry = ttk.Entry(self.bottom_frame, textvariable=self.threads_var, width=5)
        self.threads_entry.pack(side=tk.LEFT, padx=5)

        self.retries_label = ttk.Label(self.bottom_frame, text="Retries:")
        self.retries_label.pack(side=tk.LEFT, padx=5)

        self.retries_var = tk.StringVar(value="10")
        self.retries_entry = ttk.Entry(self.bottom_frame, textvariable=self.retries_var, width=5)
        self.retries_entry.pack(side=tk.LEFT, padx=5)

        self.backoff_label = ttk.Label(self.bottom_frame, text="Backoff:")
        self.backoff_label.pack(side=tk.LEFT, padx=5)

        self.backoff_var = tk.StringVar(value="2")
        self.backoff_entry = ttk.Entry(self.bottom_frame, textvariable=self.backoff_var, width=5)
        self.backoff_entry.pack(side=tk.LEFT, padx=5)

        self.jitter_var = tk.BooleanVar(value=True)
        self.jitter_check = ttk.Checkbutton(self.bottom_frame, text="Jitter", variable=self.jitter_var)
        self.jitter_check.pack(side=tk.LEFT, padx=5)

        self.retry_delay_label = ttk.Label(self.bottom_frame, text="Auto-Retry Delay (s):")
        self.retry_delay_label.pack(side=tk.LEFT, padx=5)

        self.retry_delay_var = tk.StringVar(value="60")
        self.retry_delay_entry = ttk.Entry(self.bottom_frame, textvariable=self.retry_delay_var, width=5)
        self.retry_delay_entry.pack(side=tk.LEFT, padx=5)

    def on_mouse_wheel(self, event):
        self.tree.yview_scroll(int(-1 * (event.delta / 120)), "units")

    def on_shift_mouse_wheel(self, event):
        self.tree.xview_scroll(int(-1 * (event.delta / 120)), "units")

    def load_file(self):
        file_path = filedialog.askopenfilename(filetypes=[("Text files", "*.txt")])
        if file_path:
            with open(file_path, 'r') as f:
                domains_text = f.read()
            new_domains = [d.strip() for d in domains_text.split('\n') if d.strip()]
            added_count = len(new_domains)
            self.domains.extend([d for d in new_domains if d not in self.domains])
            duplicates = added_count - (len(self.domains) - (added_count - len(new_domains)))
            if duplicates > 0:
                messagebox.showinfo("Duplicates", f"{duplicates} duplicate domains were ignored.")
            self.populate_table()

    def populate_table(self):
        # Clear existing
        for item in self.tree.get_children():
            self.tree.delete(item)
        self.domain_to_item = {}
        for domain in self.domains:
            item = self.tree.insert("", tk.END, values=(domain, "Pending"))
            self.domain_to_item[domain] = item
            self.results[domain] = "Pending"
        self.progress_label.config(text=f"0/{len(self.domains)} domains checked")
        self.update_counters()

    def clear_table(self):
        self.domains = []
        self.results = {}
        self.domain_to_item = {}
        self.tree.delete(*self.tree.get_children())
        self.status_label.config(text="Ready")
        self.progress["value"] = 0
        self.progress_label.config(text="0/0 domains checked")
        self.save_button.config(state=tk.DISABLED)
        self.recheck_button.config(state=tk.DISABLED)
        self.update_counters()

    def start_check(self, domains=None):
        if self.running:
            messagebox.showwarning("Warning", "Checking is already in progress.")
            return

        check_domains = domains or self.domains

        if not check_domains:
            messagebox.showerror("Error", "No domains to check.")
            return

        # Set pending for the domains being checked
        for domain in check_domains:
            if domain in self.domain_to_item:
                self.tree.item(self.domain_to_item[domain], values=(domain, "Pending"))
                self.results[domain] = "Pending"

        try:
            max_threads = int(self.threads_var.get())
            max_retries = int(self.retries_var.get())
            base_backoff = int(self.backoff_var.get())
            jitter = self.jitter_var.get()
            self.auto_retry_delay = int(self.retry_delay_var.get())
        except ValueError:
            max_threads = 10
            max_retries = 10
            base_backoff = 2
            jitter = True
            self.auto_retry_delay = 60
            messagebox.showwarning("Warning", "Invalid input values, using defaults.")

        self.checker = DomainChecker(max_threads=max_threads, max_retries=max_retries, base_backoff=base_backoff, jitter=jitter)

        self.progress["value"] = 0
        self.progress["maximum"] = len(check_domains)
        self.progress_label.config(text=f"0/{len(check_domains)} domains checked")
        self.status_label.config(text="Checking...")
        self.running = True
        self.paused = False
        self.cancelled = False
        self.completed = 0
        self.total = len(check_domains)
        self.disable_buttons_during_check()
        self.control_button.config(state=tk.NORMAL, text="Pause")
        self.cancel_button.config(state=tk.NORMAL)

        threading.Thread(target=self.run_check, args=(check_domains,), daemon=True).start()
        self.root.after(50, self.process_queue)  # Faster polling for real-time feel

    def disable_buttons_during_check(self):
        self.load_button.config(state=tk.DISABLED)
        self.check_button.config(state=tk.DISABLED)
        self.recheck_button.config(state=tk.DISABLED)
        self.save_button.config(state=tk.DISABLED)
        self.clear_button.config(state=tk.DISABLED)

    def enable_buttons_after_check(self):
        self.load_button.config(state=tk.NORMAL)
        self.check_button.config(state=tk.NORMAL)
        self.clear_button.config(state=tk.NORMAL)
        self.control_button.config(state=tk.DISABLED, text="Pause")
        self.cancel_button.config(state=tk.DISABLED)
        self.save_button.config(state=tk.NORMAL)
        # Enable recheck if there are errors
        has_errors = any(status.startswith('error:') for status in self.results.values())
        if has_errors:
            self.recheck_button.config(state=tk.NORMAL)
        else:
            self.recheck_button.config(state=tk.DISABLED)

    def run_check(self, check_domains):
        self.executor = concurrent.futures.ThreadPoolExecutor(max_workers=self.checker.max_threads)
        self.future_to_domain = {self.executor.submit(self.checker.check_domain, domain): domain for domain in check_domains}
        for future in self.future_to_domain:
            future.add_done_callback(self.callback_wrapper)

    def callback_wrapper(self, future):
        if self.cancelled or not self.running:
            return
        while self.paused:
            time.sleep(0.1)
            if self.cancelled or not self.running:
                return
        domain = self.future_to_domain[future]
        try:
            _, status = future.result()
        except Exception as e:
            status = f'error: {str(e)}'
        self.result_queue.put((domain, status))

    def process_queue(self):
        updated = False
        count = 0
        try:
            while True:
                domain, status = self.result_queue.get_nowait()
                if domain in self.domain_to_item:
                    item = self.domain_to_item[domain]
                    self.tree.item(item, values=(domain, status))
                    self.results[domain] = status
                    updated = True
                    count += 1
        except queue.Empty:
            pass

        if updated:
            self.completed += count
            self.progress.config(value=self.completed)
            self.progress_label.config(text=f"{self.completed}/{self.total} domains checked")
            self.tree.update_idletasks()
            self.update_counters()

        if self.completed < self.total and not self.cancelled:
            self.root.after(50, self.process_queue)
        elif not self.cancelled:
            self.finish_check()

    def update_counters(self):
        free = sum(1 for s in self.results.values() if s == "free")
        occupied = sum(1 for s in self.results.values() if s == "occupied")
        errors = sum(1 for s in self.results.values() if s.startswith("error:"))
        self.free_label.config(text=f"Free: {free}")
        self.occupied_label.config(text=f"Occupied: {occupied}")
        self.errors_label.config(text=f"Errors: {errors}")

    def finish_check(self):
        # Auto-retry errors if delay > 0 and there are errors
        error_domains = [domain for domain, status in self.results.items() if status.startswith('error:')]
        if self.auto_retry_delay > 0 and error_domains:
            self.status_label.config(text=f"Found {len(error_domains)} errors. Retrying after {self.auto_retry_delay} seconds...")
            self.root.after(self.auto_retry_delay * 1000, lambda: self.start_check(error_domains))
        else:
            self.status_label.config(text="Checking complete.")
            self.running = False
            self.enable_buttons_after_check()

    def toggle_pause_resume(self):
        if self.paused:
            self.paused = False
            self.control_button.config(text="Pause")
            self.status_label.config(text="Checking...")
        else:
            self.paused = True
            self.control_button.config(text="Resume")
            self.status_label.config(text="Paused")

    def cancel_check(self):
        self.cancelled = True
        self.running = False
        if self.executor:
            self.executor.shutdown(wait=False, cancel_futures=True)
        self.status_label.config(text="Cancelled.")
        self.enable_buttons_after_check()
        # Mark remaining as cancelled
        pending_domains = [d for d, s in self.results.items() if s == "Pending"]
        for domain in pending_domains:
            if domain in self.domain_to_item:
                self.tree.item(self.domain_to_item[domain], values=(domain, "Cancelled"))
                self.results[domain] = "Cancelled"
        self.update_counters()

    def recheck_errors(self):
        error_domains = [domain for domain, status in self.results.items() if status.startswith('error:')]
        if not error_domains:
            messagebox.showinfo("Info", "No errors to recheck.")
            return
        self.start_check(domains=error_domains)

    def save_results(self):
        free_file = filedialog.asksaveasfilename(defaultextension=".txt", title="Save Free Domains", initialfile="free_domains.txt")
        if not free_file:
            return
        occupied_file = filedialog.asksaveasfilename(defaultextension=".txt", title="Save Occupied Domains", initialfile="occupied_domains.txt")
        if not occupied_file:
            return
        errors_file = filedialog.asksaveasfilename(defaultextension=".txt", title="Save Errors", initialfile="errors.txt")
        if not errors_file:
            return
        all_file = filedialog.asksaveasfilename(defaultextension=".txt", title="Save All Domains", initialfile="all_domains.txt")
        if not all_file:
            return

        with open(free_file, 'w') as ff, open(occupied_file, 'w') as fo, open(errors_file, 'w') as fe, open(all_file, 'w') as fa:
            for domain, status in self.results.items():
                fa.write(f"{domain}\t{status}\n")
                if status == 'free':
                    ff.write(f"{domain}\n")
                elif status == 'occupied':
                    fo.write(f"{domain}\n")
                elif status.startswith('error:') or status == "Cancelled":
                    fe.write(f"{domain}\t{status}\n")

        messagebox.showinfo("Success", "Results saved successfully.")

if __name__ == "__main__":
    root = tk.Tk()
    app = DomainCheckerGUI(root)
    root.mainloop()