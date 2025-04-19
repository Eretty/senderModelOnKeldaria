import urllib.parse
import requests
from bs4 import BeautifulSoup
import urllib
import logging
import json


class senderModelKeldaria:
    """Object qui se connecte et envoie les données aux sites Keldaria."""

    def __init__(self) -> None:
        self.base_url: str = "http://keldaria.fr"
        self.login: str = "sender"
        self.password: str = "azerty1234"

        self.cookies: dict = self.__login()

    def __login(self) -> str:
        """Se connecte au site internet et récupères les cookies pour se connecter à son compte."""

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
            self.cookies = self.__login()
            return self.__send_and_get_url_texture(path=path)
        return image.find("input").get("value")

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
            self.cookies = self.__login()
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
