"""Simple Tkinter GUI for GPT Engineer."""
from pathlib import Path
import tkinter as tk
from tkinter import filedialog, messagebox

from gpt_engineer.applications.service_generator.api_automator import generate_microservice


def run():
    root = tk.Tk()
    root.title("GPT Engineer GUI")

    tk.Label(root, text="Prompt:").pack()
    prompt_box = tk.Text(root, width=60, height=10)
    prompt_box.pack()

    def handle_microservice():
        prompt = prompt_box.get("1.0", tk.END).strip()
        if not prompt:
            messagebox.showerror("Error", "Prompt cannot be empty")
            return
        directory = filedialog.askdirectory(title="Select Output Directory")
        if directory:
            generate_microservice(Path(directory), prompt)
            messagebox.showinfo("Done", f"Microservice generated in {directory}")

    tk.Button(root, text="Generate Microservice", command=handle_microservice).pack()

    root.mainloop()


if __name__ == "__main__":
    run()
