import sys

import requests
from notifypy import Notify, exceptions

sys.path.append("..")

from Globals import app_icon, app_name
from Logging import logger

from .LangCode import google_lang, libre_lang, myMemory_lang


def no_connection_notify(customTitle: str = "No Internet Connection", customMessage: str = "Translation for engine other than Whisper or your local LibreTranslate Deployment (If you have one) will not work until you reconnect to the internet."):
    notification = Notify()
    notification.title = customTitle
    notification.message = customMessage
    notification.application_name = app_name
    try:
        notification.icon = app_icon
    except exceptions.InvalidIconPath:
        pass
    notification.send()


# Import the translator
try:
    from deep_translator import GoogleTranslator, MyMemoryTranslator, PonsTranslator
except Exception as e:
    GoogleTranslator = None
    MyMemoryTranslator = None
    PonsTranslator = None
    if "HTTPSConnectionPool" in str(e):
        no_connection_notify()
    else:
        no_connection_notify("Uncaught Error", str(e))
        logger.exception(f"Error {str(e)}")


class tl_cons:
    """Translate Connections
    Attributes:
        GoogleTranslator (function): Google Translate
        MyMemoryTranslator (function): MyMemoryTranslator
        PonsTranslator (function): PonsTranslator
    """

    def __init__(self, GoogleTranslator, MyMemoryTranslator, PonsTranslator):
        self.GoogleTranslator = GoogleTranslator
        self.MyMemoryTranslator = MyMemoryTranslator
        self.PonsTranslator = PonsTranslator


tlCons = tl_cons(GoogleTranslator, MyMemoryTranslator, PonsTranslator)


def google_tl(text: str, from_lang: str, to_lang: str, oldMethod: bool = False):
    """Translate Using Google Translate
    Args:
        text (str): Text to translate
        from_lang (str): Language From
        to_lang (str): Language to translate
        oldMethod (bool, optional): Use old method. Defaults to False.
    Returns:
        is_Success: Success or not
        result: Translation result
    """
    is_Success = False
    result = ""
    # --- Get lang code ---
    try:
        to_LanguageCode_Google = google_lang[to_lang]
        from_LanguageCode_Google = google_lang[from_lang]
    except KeyError as e:
        logger.exception("Error: " + str(e))
        return is_Success, "Error Language Code Undefined"

    # --- Translate ---
    try:
        if tlCons.GoogleTranslator is None:  # type: ignore
            try:
                from deep_translator import GoogleTranslator

                tlCons.GoogleTranslator = GoogleTranslator
            except Exception as e:
                no_connection_notify()
                return is_Success, "Error: Not connected to internet"

        if not oldMethod:
            result = tlCons.GoogleTranslator(source=from_LanguageCode_Google, target=to_LanguageCode_Google).translate(text.strip())  # type: ignore
        else:
            url = "https://translate.googleapis.com/translate_a/single?client=gtx&sl={}&tl={}&dt=t&q={}".format(from_LanguageCode_Google, to_LanguageCode_Google, text.replace("\n", " ").replace(" ", "%20").strip())
            result = requests.get(url).json()[0][0][0]

        is_Success = True
    except Exception as e:
        logger.exception(str(e))
        result = str(e)
    finally:
        logger.info("-" * 50)
        logger.info("Query: " + text.strip())
        logger.info("Translation Get: " + result)
        return is_Success, result


def memory_tl(text: str, from_lang: str, to_lang: str):
    """Translate Using MyMemoryTranslator
    Args:
        text (str): Text to translate
        from_lang (str): Language From
        to_lang (str): Language to translate
    Returns:
        [type]: Translation result
    """
    is_Success = False
    result = ""
    # --- Get lang code ---
    try:
        to_LanguageCode_Memory = myMemory_lang[to_lang]
        from_LanguageCode_Memory = myMemory_lang[from_lang]
    except KeyError as e:
        logger.exception("Error: " + str(e))
        return is_Success, "Error Language Code Undefined"
    # --- Translate ---
    try:
        if tlCons.MyMemoryTranslator is None:
            try:
                from deep_translator import MyMemoryTranslator

                tlCons.MyMemoryTranslator = MyMemoryTranslator
            except Exception as e:
                no_connection_notify()
                return is_Success, "Error: Not connected to internet"

        result = tlCons.MyMemoryTranslator(source=from_LanguageCode_Memory, target=to_LanguageCode_Memory).translate(text.strip())
        is_Success = True
    except Exception as e:
        logger.exception(str(e))
        result = str(e)
    finally:
        logger.info("-" * 50)
        logger.info("Query: " + text.strip())
        logger.info("Translation Get: " + result)  # type: ignore
        return is_Success, result


# LibreTranslator
def libre_tl(text: str, from_lang: str, to_lang: str, https: bool = False, host: str = "libretranslate.de", port: str = "", apiKeys: str = ""):
    """Translate Using LibreTranslate
    Args:
        text (str): Text to translate
        from_lang (str): Language From
        to_lang (str): Language to translate
        https (bool, optional): Use https. Defaults to False.
        host (str, optional): Host. Defaults to "libretranslate.de".
        port (str, optional): Port. Defaults to "".
        apiKeys (str, optional): API Keys. Defaults to "".
    Returns:
        [type]: Translation result
    """
    is_Success = False
    result = ""
    # --- Get lang code ---
    try:
        to_LanguageCode_Libre = libre_lang[to_lang]
        from_LanguageCode_Libre = libre_lang[from_lang]
    except KeyError as e:
        logger.exception("Error: " + str(e))
        return is_Success, "Error Language Code Undefined"
    # --- Translate ---
    try:
        request = {"q": text, "source": from_LanguageCode_Libre, "target": to_LanguageCode_Libre, "format": "text", "api_key": apiKeys}
        httpStr = "https" if https else "http"

        if port != "":
            adr = httpStr + "://" + host + ":" + port + "/translate"
        else:
            adr = httpStr + "://" + host + "/translate"

        response = requests.post(adr, json=request).json()
        if "error" in response:
            result = response["error"]
        else:
            result = response["translatedText"]
            is_Success = True
    except Exception as e:
        result = str(e)
        logger.exception(str(e))
        if "NewConnectionError" in str(e):
            result = "Error: Could not connect. Please make sure that the server is running and the port is correct. If you are not hosting it yourself, please try again with an internet connection."
        if "request expecting value" in str(e):
            result = "Error: Invalid parameter value. Check for https, host, port, and apiKeys. If you use external server, make sure https is set to True."
    finally:
        logger.info("-" * 50)
        logger.info("Query: " + text.strip())
        logger.info("Translation Get: " + result)
        return is_Success, result
