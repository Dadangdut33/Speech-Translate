from notifypy import Notify
import requests
from .LangCode import google_Lang, libre_Lang

try:
    from deep_translator import GoogleTranslator
except Exception as e:
    GoogleTranslator = None
    if "HTTPSConnectionPool" in str(e):
        notification = Notify()
        notification.application_name = "Speech Translate"
        notification.title = "Not connected to internet"
        notification.message = "Translation for language other than English will not work until you reconnect to the internet."
        notification.send()
    else:
        print("Error", str(e))


class tl_cons:
    """Translate Connections
    Attributes:
        google_tl (function): Google Translate
        memory_tl (function): MyMemoryTranslator
        pons_tl (function): PonsTranslator
    """

    def __init__(self, GoogleTranslator):
        self.GoogleTranslator = GoogleTranslator

        if self.GoogleTranslator is None:
            self.connected = False
        else:
            self.connected = True


tlCons = tl_cons(GoogleTranslator)


def google_tl(text, from_lang, to_lang, oldMethod=False):
    """Translate Using Google Translate
    Args:
        text ([str]): Text to translate
        from_lang (str, optional): [Language From]. Defaults to "auto".
        to_lang ([type]): Language to translate
        oldMethod (bool, optional): Use old method. Defaults to False.
    Returns:
        is_Success: Success or not
        result: Translation result
    """
    is_Success = False
    result = ""
    # --- Get lang code ---
    try:
        to_LanguageCode_Google = google_Lang[to_lang]
        from_LanguageCode_Google = google_Lang[from_lang]
    except KeyError as e:
        print("Error: " + str(e))
        return is_Success, "Error Language Code Undefined"

    # --- Translate ---
    try:
        if tlCons.GoogleTranslator is None:  # type: ignore
            try:
                from deep_translator import GoogleTranslator

                tlCons.GoogleTranslator = GoogleTranslator
            except Exception as e:
                notification = Notify()
                notification.application_name = "Speech Translate"
                notification.title = "Not connected to internet"
                notification.message = "Translation for language other than English will not work until you reconnect to the internet."
                notification.send()

                return is_Success, "Error: Not connected to internet"

        if not oldMethod:
            result = tlCons.GoogleTranslator(source=from_LanguageCode_Google, target=to_LanguageCode_Google).translate(text.strip())  # type: ignore
        else:
            url = "https://translate.googleapis.com/translate_a/single?client=gtx&sl={}&tl={}&dt=t&q={}".format(from_LanguageCode_Google, to_LanguageCode_Google, text.replace("\n", " ").replace(" ", "%20").strip())
            result = requests.get(url).json()[0][0][0]

        is_Success = True
    except Exception as e:
        print(str(e))
        result = str(e)
    finally:
        print("-" * 50)
        print("Query: " + text.strip())
        print("-" * 50)
        print("Translation Get: " + result)
        return is_Success, result


# LibreTranslator
def libre_tl(text, from_lang, to_lang, https=False, host="libretranslate.de", port="", apiKeys=""):
    """Translate Using LibreTranslate
    Args:
        text ([str]): Text to translate
        from_lang (str, optional): [Language From]. Defaults to "auto".
        to_lang ([type]): Language to translate
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
        to_LanguageCode_Libre = libre_Lang[to_lang]
        from_LanguageCode_Libre = libre_Lang[from_lang]
    except KeyError as e:
        print("Error: " + str(e))
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
        print(str(e))
        if "NewConnectionError" in str(e):
            result = "Error: Could not connect. Please make sure that the server is running and the port is correct. If you are not hosting it yourself, please try again with an internet connection."
        if "request expecting value" in str(e):
            result = "Error: Invalid parameter value. Check for https, host, port, and apiKeys. If you use external server, make sure https is set to True."
    finally:
        print("-" * 50)
        print("Query: " + text.strip())
        print("-" * 50)
        print("Translation Get: " + result)
        return is_Success, result
