import tkinter as tk
from tkinter import filedialog, messagebox, ttk
import json
import configparser
from sender.sender import senderModelKeldaria


class KeldariaTool:
    def __init__(self, root):
        self.root = root
        self.root.title("Keldaria Model Sender")
        self.sender = senderModelKeldaria()

        self.notebook = ttk.Notebook(root)
        self.notebook.pack(fill=tk.BOTH, expand=True)

        self.auth_frame = ttk.Frame(self.notebook)
        self.obj_frame = ttk.Frame(self.notebook)
        self.json_frame = ttk.Frame(self.notebook)
        self.cache_frame = ttk.Frame(self.notebook)

        self.notebook.add(self.auth_frame, text="Identifiants")
        self.notebook.add(self.obj_frame, text="OBJ")
        self.notebook.add(self.json_frame, text="JSON")
        self.notebook.add(self.cache_frame, text="Cache")

        self.setup_auth_tab()
        self.setup_obj_tab()
        self.setup_json_tab()
        self.setup_cache_tab()

    def setup_auth_tab(self):
        ttk.Label(self.auth_frame, text="Nom d'utilisateur:").pack(pady=5)
        self.login_var = tk.StringVar()
        ttk.Entry(self.auth_frame, textvariable=self.login_var, width=40).pack(pady=5)

        ttk.Label(self.auth_frame, text="Mot de passe:").pack(pady=5)
        self.password_var = tk.StringVar()
        ttk.Entry(self.auth_frame, textvariable=self.password_var, width=40, show="*").pack(pady=5)

        ttk.Button(self.auth_frame, text="Sauvegarder", command=self.save_auth).pack(pady=10)
        self.load_auth()

    def setup_obj_tab(self):
        ttk.Label(self.obj_frame, text="Fichier OBJ:").pack(pady=5)
        self.obj_path = tk.StringVar()
        ttk.Entry(self.obj_frame, textvariable=self.obj_path, width=50).pack(padx=5)
        ttk.Button(self.obj_frame, text="Parcourir", command=self.browse_obj).pack(pady=5)

        ttk.Label(self.obj_frame, text="Texture:").pack(pady=5)
        self.texture_path = tk.StringVar()
        ttk.Entry(self.obj_frame, textvariable=self.texture_path, width=50).pack(padx=5)
        ttk.Button(self.obj_frame, text="Parcourir", command=self.browse_texture).pack(pady=5)

        ttk.Button(self.obj_frame, text="Générer Commande", command=self.generate_obj_command).pack(pady=10)
        self.obj_command_box = tk.Text(self.obj_frame, height=4, width=80)
        self.obj_command_box.pack(padx=5, pady=5)

    def setup_json_tab(self):
        ttk.Label(self.json_frame, text="Coller le contenu JSON:").pack(pady=5)
        self.json_text = tk.Text(self.json_frame, height=10, width=80)
        self.json_text.pack(padx=5)
        ttk.Button(self.json_frame, text="Analyser JSON", command=self.analyze_json).pack(pady=5)

        self.texture_entries_frame = ttk.LabelFrame(self.json_frame, text="Textures")
        self.texture_entries_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        self.canvas = tk.Canvas(self.texture_entries_frame)
        self.scrollbar = ttk.Scrollbar(self.texture_entries_frame, orient="vertical", command=self.canvas.yview)
        self.scrollable_frame = ttk.Frame(self.canvas)

        self.scrollable_frame.bind("<Configure>", lambda e: self.canvas.configure(scrollregion=self.canvas.bbox("all")))
        self.canvas.create_window((0, 0), window=self.scrollable_frame, anchor="nw")
        self.canvas.configure(yscrollcommand=self.scrollbar.set)

        self.canvas.pack(side="left", fill="both", expand=True)
        self.scrollbar.pack(side="right", fill="y")

        ttk.Button(self.json_frame, text="Générer Commande JSON", command=self.generate_json_command).pack(pady=10)
        self.json_command_box = tk.Text(self.json_frame, height=4, width=80)
        self.json_command_box.pack(padx=5, pady=5)

        self.texture_entries = {}

    def setup_cache_tab(self):
        self.cache_text = tk.Text(self.cache_frame, height=20, width=80, state="disabled")
        self.cache_text.pack(padx=5, pady=5)
        ttk.Button(self.cache_frame, text="Recharger le cache", command=self.load_cache).pack(pady=5)
        ttk.Button(self.cache_frame, text="Vider le cache", command=self.clear_cache_gui).pack(pady=5)
        self.load_cache()

    def browse_obj(self):
        path = filedialog.askopenfilename(filetypes=[("OBJ Files", "*.obj")])
        if path:
            self.obj_path.set(path)

    def browse_texture(self):
        path = filedialog.askopenfilename(filetypes=[("Image Files", "*.png;*.jpg;*.jpeg")])
        if path:
            self.texture_path.set(path)

    def browse_texture_for_key(self, var):
        path = filedialog.askopenfilename(filetypes=[("Image Files", "*.png;*.jpg;*.jpeg")])
        if path:
            var.set(path)

    def check_auth(self):
        """Vérifie que login et password sont renseignés avant génération de commande."""
        if not self.login_var.get() or not self.password_var.get():
            messagebox.showerror("Erreur", "Veuillez renseigner votre identifiant et mot de passe dans l'onglet Identifiants avant de générer une commande.")
            return False
        return True

    def generate_obj_command(self):
        if not self.check_auth():
            return
        try:
            command = self.sender.get_command_obj(self.obj_path.get(), self.texture_path.get())
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
                ttk.Entry(frame, textvariable=path_var, width=40).pack(side=tk.LEFT, padx=5)
                ttk.Button(frame, text="Parcourir", command=lambda v=path_var: self.browse_texture_for_key(v)).pack(side=tk.LEFT)
                self.texture_entries[key] = path_var
        except Exception as e:
            messagebox.showerror("Erreur", str(e))

    def generate_json_command(self):
        if not self.check_auth():
            return
        try:
            textures_paths = {k: v.get() for k, v in self.texture_entries.items()}
            uploaded = {k: self.sender.send_texture(v) for k, v in textures_paths.items() if v}
            command = self.sender.get_command_json(self.json_text.get("1.0", tk.END), uploaded)
            self.json_command_box.delete("1.0", tk.END)
            self.json_command_box.insert(tk.END, command)
        except Exception as e:
            messagebox.showerror("Erreur", str(e))

    def load_cache(self):
        try:
            with open(self.sender.cache_filename, "r") as f:
                data = json.load(f)
            self.cache_text.configure(state="normal")
            self.cache_text.delete("1.0", tk.END)
            self.cache_text.insert(tk.END, json.dumps(data, indent=2))
            self.cache_text.configure(state="disabled")
        except Exception as e:
            messagebox.showerror("Erreur", f"Impossible de charger le cache: {e}")

    def clear_cache_gui(self):
        self.sender.clear_cache()
        self.load_cache()
        messagebox.showinfo("Succès", "Le cache a été vidé avec succès.")

    def load_auth(self):
        config = configparser.ConfigParser()
        config.read(self.sender.config_filename)
        self.login_var.set(config.get("user", "login", fallback=""))
        self.password_var.set(config.get("user", "password", fallback=""))

    def save_auth(self):
        config = configparser.ConfigParser()
        config["user"] = {"login": self.login_var.get(), "password": self.password_var.get()}
        try:
            with open(self.sender.config_filename, "w") as f:
                config.write(f)
            self.sender.reload_auth()
            messagebox.showinfo("Succès", "Connexion réussie.")
        except Exception as e:
            messagebox.showerror("Erreur", "Impossible de se connecter.")


if __name__ == "__main__":
    root = tk.Tk()
    app = KeldariaTool(root)
    root.mainloop()
