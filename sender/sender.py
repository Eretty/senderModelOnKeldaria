import urllib.parse
import requests
from bs4 import BeautifulSoup
import urllib
import logging
import json
import configparser
import os
import hashlib


class senderModelKeldaria:
    """Object qui se connecte et envoie les données aux sites Keldaria."""

    def __init__(self) -> None:
        self.base_url: str = "http://keldaria.fr"
        self.login: str = ""
        self.password: str = ""

        # Chemin vers le fichier
        self.config_filename: str = "config.ini"

        # Chemin vers le cache
        self.cache_filename: str = ".cache.json"

        self.__generate_cache_file()
        self.__generate_config_file()

        self.cookies: dict = self.reload_auth()

    def reload_auth(self):
        """Recharge les identifiants depuis le fichier config et relance la connexion."""
        self.cookies = self.login_to_website()

    def login_to_website(self) -> str:
        """Se connecte au site internet et récupères les cookies pour se connecter à son compte."""

        self.get_identifiant_by_config()
        if not self.login or not self.password:
            logging.info("Aucun nom d'utilisateur ou de mot de passe n'a été trouvé.")
            return

        # Envoye les identifiants du compte.
        res = requests.post(
            url=urllib.parse.urljoin(self.base_url, "/index.php"),
            params={"page": "login"},
            data={
                "pseudo": self.login,
                "password": self.password,
                "signIn": "Se connecter",
            },
        )
        res.raise_for_status()
        self.cookies = res.cookies

        # Récupères le token de connexion.
        res = requests.get(
            url=urllib.parse.urljoin(self.base_url, "/index.php"),
            params={"page": "home", "rememberMe": ""},
            cookies=self.cookies,
        )
        res.raise_for_status()

        # Vérifie que le token de connexion est bien obtenu.
        if not res.cookies.get("kelda_session_token"):
            raise Exception("Impossible de pouvoir se connecter.")
        return res.cookies

    def get_identifiant_by_config(self):
        """ " Récupères l'identifiant et le mot de passe depuis le fichier de congifuration."""

        config = configparser.ConfigParser()
        config.read(self.config_filename)
        self.login = config.get("user", "login", fallback="")
        self.password = config.get("user", "password", fallback="")

    def clear_cache(self):
        with open(self.cache_filename, "w") as f:
            f.write("{}")

    def __generate_cache_file(self) -> None:
        if not os.path.exists(self.cache_filename):
            with open(self.cache_filename, "w") as f:
                f.write("{}")  # Fichier JSON vide valide

    def __generate_config_file(self) -> None:
        """Vérifie l'existance du fichier de configuration."""
        if not os.path.exists(self.config_filename):
            config = configparser.ConfigParser()

            # Ajoute des sections et des options
            config["user"] = {"login": "", "password": ""}

            # Sauvegarder le fichier de configuration
            config.write(open(self.config_filename, "w"))

    def __get_hash_md5_path(self, path: str) -> str:
        hash_md5 = hashlib.md5()
        with open(path, "rb") as f:
            for bloc in iter(lambda: f.read(4096), b""):
                hash_md5.update(bloc)
        return hash_md5.hexdigest()

    def __check_and_get_url_file(self, path: str) -> str:
        """ """

        # Génère une fichier contenant les caches.
        self.__generate_cache_file()

        # Vérifie si le chemin du document est dans le cache
        with open(self.cache_filename, "r") as f:
            cache: dict = json.load(f)

            # Retourne l'url de la texture si tout les documents sont
            if cache.get(path) and self.__get_hash_md5_path(path) == cache[path]["md5"]:
                return cache[path]["url"]
        return None

    def __save_url_file(self, path: str, url_texture: str) -> None:
        """ """

        # Génère une fichier contenant les caches.
        self.__generate_cache_file()

        # Vérifie si le chemin du document est dans le cache
        try:
            with open(self.cache_filename, "r") as f:
                cache = json.load(f)
        except Exception:
            cache = {}
        cache.update(
            {path: {"url": url_texture, "md5": self.__get_hash_md5_path(path)}}
        )
        open(self.cache_filename, "w+").write(json.dumps(cache))

    def __send_and_get_url_texture(self, path: str) -> str:
        """Envoyes une image au site et récupères l'url de la texture."""

        # Récupères le contenu de l'image en binaire.
        try:
            image_byte: bytes = open(path, "rb").read()
        except Exception as exc:
            logging.error(exc, exc_info=True)
            raise exc

        # Récupères l'extension de l'image.
        image_extension: str = None
        if ".png" in path.lower():
            image_extension = "image/png"
        elif ".jpg" in path.lower() or ".jpeg" in path.lower():
            image_extension = "image/jpeg"
        else:
            raise Exception("Le type du document n'est pas reconnu.")

        url_texture: str = None
        url_texture = self.__check_and_get_url_file(path=path)
        if url_texture:
            return url_texture

        # Envoye l'image au site.
        res = requests.post(
            url=urllib.parse.urljoin(self.base_url, "/index.php"),
            params={"page": "skinhosting"},
            files={"file": ("image.png", image_byte, image_extension)},
            cookies=self.cookies,
        )
        res.raise_for_status()

        # Récupères l'url.
        soup = BeautifulSoup(res.content, "html5lib")
        image = soup.find("div", {"id": "image"})
        if not image:
            logging.error("Impossible de charger l'image")
            self.cookies = self.login_to_website()
            return self.__send_and_get_url_texture(path=path)

        url_texture = image.find("input").get("value")
        self.__save_url_file(path=path, url_texture=url_texture)
        return url_texture

    def __send_and_get_url_model(self, text: str) -> str:
        """ """

        # Envoye le texte
        res = requests.post(
            url=urllib.parse.urljoin(self.base_url, "/index.php"),
            params={"page": "pastebin"},
            data={"text": text},
            cookies=self.cookies,
        )
        res.raise_for_status()

        # Récupères l'url.
        soup = BeautifulSoup(res.content, "html5lib")
        editor = soup.find("input", {"type": "text"})
        if not editor:
            logging.error("Impossible de charger l'url du model")
            self.cookies = self.login_to_website()
            return self.__send_and_get_url_model(text=text)
        return editor.get("value")

    def get_command_obj(self, path_obj: str, path_texture: str) -> str:
        """Obtiens la commande pour mettre à jour les modèles."""

        # Vérifie l'extension du fichier
        if ".obj" not in path_obj.lower():
            raise Exception("Ce n'est pas un fichier json.")

        # Récupères l'extension du fichier
        texture_url: str = self.__send_and_get_url_texture(path=path_texture)

        # Appliques l'url de la texture dans le code du fichier obj
        obj_text: str = f"# texture {texture_url}\n"
        obj_text += open(path_obj, "r").read()

        # Envoye et retourne l'url du pastebin.
        url_model: str = self.__send_and_get_url_model(text=obj_text)
        return f"/customizeblock setModel {url_model} OBJ"

    def get_textures_from_json(self, data: str) -> dict:
        # Charge le fichier json
        try:
            data: dict = json.loads(data)
        except:
            raise Exception("Impossible de charger le fichier json.")

        return data.get("textures")

    def get_command_json(self, data: dict | str, textures: dict) -> str:
        """Obtiens la commande pour mettre à jour les modèles."""

        # Charge le fichier json
        try:
            if type(data) is dict:
                data: dict = data
            elif type(data) is str:
                data: dict = json.loads(data)
            else:
                raise
        except:
            raise Exception("Impossible de charger le fichier json.")

        # remplaces les textures par défaut avec ceux envoyés sur Keldaria
        data.update({"textures": textures})

        url_model: str = self.__send_and_get_url_model(text=json.dumps(data))
        return f"/customizeblock setModel {url_model} JSON"

    def send_texture(self, path: str) -> str:
        return self.__send_and_get_url_texture(path)
