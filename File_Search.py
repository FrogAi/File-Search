import chardet
import os
import sys
import threading
import tkinter as tk
import tkinter.ttk as ttk
from tkinter import filedialog

ALLOWED_EXTENSIONS = ('.0', '.c', '.capnp', '.cc', '.cfg', '.cl', '.cpp', '.dbc', '.doc', '.docx', '.h',
                      '.hpp', '.html', '.in', '.ld', '.md', '.m', '.pdf', '.pxd', '.py', '.pyx', '.qml',
                      '.qrc', '.pub', '.json', '.s', '.sample', '.sh', '.svg', '.txt', '.ts', '.xlsx', '.yaml')
ENCODINGS = ('utf-8', 'cp1252', 'gbk', 'iso-8859-1', 'utf-16', 'utf-16-be', 'utf-16-le', 'utf-32', 'utf-32-be', 'utf-32-le', 'Shift_JIS', 'EUC-JP', 'ISO-8859-2')

def search_files(folder, phrase):
    results = []
    for root, dirs, files in os.walk(folder):
        for file in files:
            if not file.endswith(ALLOWED_EXTENSIONS):
                continue
            file_path = os.path.join(root, file)
            decoded_content = None
            for encoding in ENCODINGS:
                try:
                    with open(file_path, 'r', encoding=encoding) as f:
                        content = f.read()
                    decoded_content = content
                    break
                except UnicodeDecodeError:
                    continue
            if decoded_content is None:
                print(f"Unable to decode file {file_path}", file=sys.stderr)
                continue
            if phrase.lower() in decoded_content.lower():
                results.append(file_path)
    return results

def save_results(results, output_folder, output_file_name):
    os.makedirs(output_folder, exist_ok=True)
    with open(os.path.join(output_folder, f"{output_file_name}.txt"), 'w', encoding="utf-8") as f:
        f.write('\n'.join(results))

def choose_folder():
    root = tk.Tk()
    root.withdraw()
    return filedialog.askdirectory()

class SearchGUI(tk.Tk):
    ALLOWED_EXTENSIONS = (".txt", ".md", ".py")

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.title("File Search")
        self.geometry("525x250")

        self.search_folder_var = tk.StringVar(value="")
        self.output_folder_var = tk.StringVar(value="")
        self.search_phrase_var = tk.StringVar()
        self.output_file_name_var = tk.StringVar()
        self.progress_text = tk.StringVar(value="Idle")

        self.protocol("WM_DELETE_WINDOW", self.on_closing)
        self.init_widgets()

    def init_widgets(self):
        tk.Label(self, text="Search Folder:").grid(row=0, column=0, padx=10, pady=10, sticky='W')
        tk.Entry(self, textvariable=self.search_folder_var, state="readonly", width=50).grid(row=0, column=1, padx=10, pady=10)
        tk.Button(self, text="Browse", command=self.select_search_folder).grid(row=0, column=2, padx=10, pady=10)

        tk.Label(self, text="Output Folder:").grid(row=1, column=0, padx=10, pady=10, sticky='W')
        tk.Entry(self, textvariable=self.output_folder_var, state="readonly", width=50).grid(row=1, column=1, padx=10, pady=10)
        tk.Button(self, text="Browse", command=self.choose_output_folder).grid(row=1, column=2, padx=10, pady=10)

        tk.Label(self, text="Search Phrase:").grid(row=2, column=0, padx=10, pady=10, sticky='W')
        tk.Entry(self, textvariable=self.search_phrase_var, width=50).grid(row=2, column=1, padx=10, pady=10)

        tk.Label(self, text="Output File Name:").grid(row=3, column=0, padx=10, pady=10, sticky='W')
        tk.Entry(self, textvariable=self.output_file_name_var, width=50).grid(row=3, column=1, padx=10, pady=10)

        tk.Button(self, text="Search", command=self.search).grid(row=4, column=1, padx=10, pady=10, sticky='NSEW')

        tk.Label(self, textvariable=self.progress_text).grid(row=5, column=1, padx=10, pady=10, sticky='NSEW')

    def select_search_folder(self):
        search_folder = choose_folder()
        if search_folder:
            self.search_folder_var.set(search_folder)

    def choose_output_folder(self):
        output_folder = choose_folder()
        if output_folder:
            self.output_folder_var.set(output_folder)

    def set_search_results(self, results):
        self.search_results = results
        self.progress_text.set("Found {} file(s)".format(len(results)))

    def search(self):
        thread = threading.Thread(target=self._search)
        thread.start()

    def _search(self):
        search_folder = self.search_folder_var.get()
        output_folder = self.output_folder_var.get()
        search_phrase = self.search_phrase_var.get()
        output_file_name = self.output_file_name_var.get()

        if not search_folder or not output_folder or not search_phrase:
            return

        self.progress_text.set("Searching... 0/0")
        self.update()

        total_files = 0
        for root, dirs, files in os.walk(search_folder):
            total_files += len(files)

        files_searched = 0
        results = []
        for root, dirs, files in os.walk(search_folder):
            for file in files:
                if not file.endswith(ALLOWED_EXTENSIONS):
                    continue
                file_path = os.path.join(root, file)
                try:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        content = f.read()
                    if search_phrase.lower() in content.lower():
                        results.append(file_path)
                except UnicodeDecodeError:
                    detected_encoding = None
                    # Detect the encoding using the chardet library
                    with open(file_path, 'rb') as f:
                        detected_encoding = chardet.detect(f.read())['encoding']
                    if detected_encoding:
                        with open(file_path, 'r', encoding=detected_encoding) as f:
                            content = f.read()
                        if search_phrase.lower() in content.lower():
                            results.append(file_path)
                files_searched += 1
                self.progress_text.set(f"Searching... {files_searched}/{total_files}")
                self.update()
        save_results(results, output_folder, output_file_name)
        self.progress_text.set(f"Found {len(results)} file(s)")

    def search_in_thread(self, search_folder, output_folder, search_phrase):
        results = search_files(search_folder, search_phrase)
        self.set_search_results(results)
        save_results(results, output_folder)
        self.progress_text.set("Search completed.")

    def on_closing(self):
        self.quit()

if __name__ == "__main__":
    app = SearchGUI()
    app.mainloop()
