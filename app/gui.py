import tkinter as tk
from tkinter import filedialog, messagebox, ttk

from sender import senderModelKeldaria


class KeldariaTool:
    def __init__(self, root):
        self.root = root
        self.root.title("Keldaria Model Sender")
        self.sender = senderModelKeldaria()

        self.notebook = ttk.Notebook(root)
        self.notebook.pack(fill=tk.BOTH, expand=True)

        self.obj_frame = ttk.Frame(self.notebook)
        self.json_frame = ttk.Frame(self.notebook)

        self.notebook.add(self.obj_frame, text="OBJ")
        self.notebook.add(self.json_frame, text="JSON")

        self.setup_obj_tab()
        self.setup_json_tab()

    def setup_obj_tab(self):
        ttk.Label(self.obj_frame, text="Fichier OBJ:").pack(pady=5)
        self.obj_path = tk.StringVar()
        ttk.Entry(self.obj_frame, textvariable=self.obj_path, width=50).pack(padx=5)
        ttk.Button(self.obj_frame, text="Parcourir", command=self.browse_obj).pack(
            pady=5
        )

        ttk.Label(self.obj_frame, text="Texture:").pack(pady=5)
        self.texture_path = tk.StringVar()
        ttk.Entry(self.obj_frame, textvariable=self.texture_path, width=50).pack(padx=5)
        ttk.Button(self.obj_frame, text="Parcourir", command=self.browse_texture).pack(
            pady=5
        )

        ttk.Button(
            self.obj_frame, text="Générer Commande", command=self.generate_obj_command
        ).pack(pady=10)
        self.obj_command_box = tk.Text(self.obj_frame, height=4, width=80)
        self.obj_command_box.pack(padx=5, pady=5)

    def setup_json_tab(self):
        ttk.Label(self.json_frame, text="Coller le contenu JSON:").pack(pady=5)
        self.json_text = tk.Text(self.json_frame, height=10, width=80)
        self.json_text.pack(padx=5)
        ttk.Button(
            self.json_frame, text="Analyser JSON", command=self.analyze_json
        ).pack(pady=5)

        self.texture_entries_frame = ttk.LabelFrame(self.json_frame, text="Textures")
        self.texture_entries_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        self.canvas = tk.Canvas(self.texture_entries_frame)
        self.scrollbar = ttk.Scrollbar(
            self.texture_entries_frame, orient="vertical", command=self.canvas.yview
        )
        self.scrollable_frame = ttk.Frame(self.canvas)

        self.scrollable_frame.bind(
            "<Configure>",
            lambda e: self.canvas.configure(scrollregion=self.canvas.bbox("all")),
        )

        self.canvas.create_window((0, 0), window=self.scrollable_frame, anchor="nw")
        self.canvas.configure(yscrollcommand=self.scrollbar.set)

        self.canvas.pack(side="left", fill="both", expand=True)
        self.scrollbar.pack(side="right", fill="y")

        ttk.Button(
            self.json_frame,
            text="Générer Commande JSON",
            command=self.generate_json_command,
        ).pack(pady=10)
        self.json_command_box = tk.Text(self.json_frame, height=4, width=80)
        self.json_command_box.pack(padx=5, pady=5)

        self.texture_entries = {}

    def browse_obj(self):
        path = filedialog.askopenfilename(filetypes=[("OBJ Files", "*.obj")])
        if path:
            self.obj_path.set(path)

    def browse_texture(self):
        path = filedialog.askopenfilename(
            filetypes=[("Image Files", "*.png;*.jpg;*.jpeg")]
        )
        if path:
            self.texture_path.set(path)

    def generate_obj_command(self):
        try:
            command = self.sender.get_command_obj(
                path_obj=self.obj_path.get(),
                path_texture=self.texture_path.get(),
            )
            self.obj_command_box.delete("1.0", tk.END)
            self.obj_command_box.insert(tk.END, command)
        except Exception as e:
            messagebox.showerror("Erreur", str(e))

    def analyze_json(self):
        for widget in self.scrollable_frame.winfo_children():
            widget.destroy()

        try:
            data = self.json_text.get("1.0", tk.END)
            textures = self.sender.get_textures_from_json(data)
            if not textures:
                raise Exception("Aucune clé de texture trouvée.")
            self.texture_entries = {}
            for key in textures:
                frame = ttk.Frame(self.scrollable_frame)
                frame.pack(fill=tk.X, pady=2, padx=5)

                ttk.Label(frame, text=key).pack(side=tk.LEFT)
                path_var = tk.StringVar()
                ttk.Entry(frame, textvariable=path_var, width=40).pack(
                    side=tk.LEFT, padx=5
                )
                ttk.Button(
                    frame,
                    text="Parcourir",
                    command=lambda v=path_var: self.browse_texture_for_key(v),
                ).pack(side=tk.LEFT)
                self.texture_entries[key] = path_var
        except Exception as e:
            messagebox.showerror("Erreur", str(e))

    def browse_texture_for_key(self, var):
        path = filedialog.askopenfilename(
            filetypes=[("Image Files", "*.png;*.jpg;*.jpeg")]
        )
        if path:
            var.set(path)

    def generate_json_command(self):
        try:
            textures_paths = {k: v.get() for k, v in self.texture_entries.items()}
            uploaded = {
                k: self.sender.send_texture(v) for k, v in textures_paths.items() if v
            }
            command = self.sender.get_command_json(
                data=self.json_text.get("1.0", tk.END), textures=uploaded
            )
            self.json_command_box.delete("1.0", tk.END)
            self.json_command_box.insert(tk.END, command)
        except Exception as e:
            messagebox.showerror("Erreur", str(e))


if __name__ == "__main__":
    root = tk.Tk()
    app = KeldariaTool(root)
    root.mainloop()
