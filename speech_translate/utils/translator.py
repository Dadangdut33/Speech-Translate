from requests import post as r_post
from typing import Dict
from speech_translate.custom_logging import logger
from .helper import get_similar_keys, no_connection_notify
from .language import google_lang, libre_lang, myMemory_lang

# Import the translator
try:
    from deep_translator import GoogleTranslator, MyMemoryTranslator
except Exception as e:
    GoogleTranslator = None
    MyMemoryTranslator = None
    if "HTTPSConnectionPool" in str(e):
        no_connection_notify()
    else:
        no_connection_notify("Uncaught Error", str(e))
        logger.exception(f"Error {str(e)}")


class TranslationConnection:
    """Translate Connections

    Attributes
    ----------
        GoogleTranslator (function): Google Translate
        MyMemoryTranslator (function): MyMemoryTranslator
    """
    def __init__(self, GoogleTranslator, MyMemoryTranslator):
        self.GoogleTranslator = GoogleTranslator
        self.MyMemoryTranslator = MyMemoryTranslator


TlCon = TranslationConnection(GoogleTranslator, MyMemoryTranslator)


def google_tl(text: str, from_lang: str, to_lang: str, proxies: Dict, debug_log: bool = False):
    """Translate Using Google Translate

    Args
    ----
        text (str): Text to translate
        from_lang (str): Language From
        to_lang (str): Language to translate
        proxies (Dict): Proxies. Defaults to None.
        debug_log (bool, optional): Debug Log. Defaults to False.

    Returns
    -------
        is_Success: Success or not
        result: Translation result
    """
    is_Success = False
    result = ""
    # --- Get lang code ---
    try:
        try:
            to_LanguageCode_Google = google_lang[to_lang]
            from_LanguageCode_Google = google_lang[from_lang]
        except KeyError:
            to_LanguageCode_Google = google_lang[get_similar_keys(google_lang, to_lang)[0]]
            from_LanguageCode_Google = google_lang[get_similar_keys(google_lang, from_lang)[0]]
    except KeyError as e:
        logger.exception(e)
        return is_Success, "Error Language Code Undefined"

    # --- Translate ---
    try:
        if TlCon.GoogleTranslator is None:
            try:
                from deep_translator import GoogleTranslator

                TlCon.GoogleTranslator = GoogleTranslator
            except Exception:
                no_connection_notify()
                return is_Success, "Error: Not connected to internet"

        result = TlCon.GoogleTranslator(source=from_LanguageCode_Google, target=to_LanguageCode_Google,
                                        proxies=proxies).translate(text.strip())
        is_Success = True
    except Exception as e:
        logger.exception(str(e))
        result = str(e)
    finally:
        if debug_log:
            logger.info("-" * 50)
            logger.debug("Query: " + text.strip())
            logger.debug("Translation Get: " + result)
        return is_Success, result


def memory_tl(text: str, from_lang: str, to_lang: str, proxies: Dict, debug_log: bool = False):
    """Translate Using MyMemoryTranslator

    Args
    ----
        text (str): Text to translate
        from_lang (str): Language From
        to_lang (str): Language to translate
        proxies (Dict): Proxies. Defaults to None.
        debug_log (bool, optional): Debug Log. Defaults to False.

    Returns
    -------
        is_Success: Success or not
        result: Translation result
    """
    is_Success = False
    result = ""
    # --- Get lang code ---
    try:
        try:
            to_LanguageCode_Memory = myMemory_lang[to_lang]
            from_LanguageCode_Memory = myMemory_lang[from_lang]
        except KeyError:
            to_LanguageCode_Memory = myMemory_lang[get_similar_keys(myMemory_lang, to_lang)[0]]
            from_LanguageCode_Memory = myMemory_lang[get_similar_keys(myMemory_lang, from_lang)[0]]
    except KeyError as e:
        logger.exception(e)
        return is_Success, "Error Language Code Undefined"
    # --- Translate ---
    try:
        if TlCon.MyMemoryTranslator is None:
            try:
                from deep_translator import MyMemoryTranslator

                TlCon.MyMemoryTranslator = MyMemoryTranslator
            except Exception:
                no_connection_notify()
                return is_Success, "Error: Not connected to internet"

        result = str(
            TlCon.MyMemoryTranslator(source=from_LanguageCode_Memory, target=to_LanguageCode_Memory,
                                     proxies=proxies).translate(text.strip())
        )
        is_Success = True
    except Exception as e:
        logger.exception(str(e))
        result = str(e)
    finally:
        if debug_log:
            logger.info("-" * 50)
            logger.debug("Query: " + text.strip())
            logger.debug("Translation Get: " + result)
        return is_Success, result


# LibreTranslator
def libre_tl(
    text: str,
    from_lang: str,
    to_lang: str,
    https: bool,
    host: str,
    port: str,
    apiKeys: str,
    proxies: Dict,
    debug_log: bool = False,
):
    """Translate Using LibreTranslate

    Args
    ----
        text (str): Text to translate
        from_lang (str): Language From
        to_lang (str): Language to translate
        https (bool): Use https
        host (str): Host
        port (str): Port
        apiKeys (str): API Keys
        proxies (Dict): Proxies
        debug_log (bool, optional): Debug Log. Defaults to False.

    Returns
    -------
        is_Success: Success or not
        result: Translation result
    """
    is_Success = False
    result = ""
    # --- Get lang code ---
    try:
        try:
            to_LanguageCode_Libre = libre_lang[to_lang]
            from_LanguageCode_Libre = libre_lang[from_lang]
        except KeyError:
            to_LanguageCode_Libre = libre_lang[get_similar_keys(libre_lang, to_lang)[0]]
            from_LanguageCode_Libre = libre_lang[get_similar_keys(libre_lang, from_lang)[0]]
    except KeyError as e:
        logger.exception(e)
        return is_Success, "Error Language Code Undefined"
    # --- Translate ---
    try:
        request = {
            "q": text,
            "source": from_LanguageCode_Libre,
            "target": to_LanguageCode_Libre,
            "format": "text",
            "api_key": apiKeys,
        }
        httpStr = "https" if https else "http"

        if port != "":
            adr = httpStr + "://" + host + ":" + port + "/translate"
        else:
            adr = httpStr + "://" + host + "/translate"

        response = r_post(adr, json=request, proxies=proxies).json()
        if "error" in response:
            result = response["error"]
        else:
            result = response["translatedText"]
            is_Success = True
    except Exception as e:
        result = str(e)
        logger.exception(str(e))
        if "NewConnectionError" in str(e):
            result = "Error: Could not connect. Please make sure that the server is running and the port is correct."
            " If you are not hosting it yourself, please try again with an internet connection."
        if "request expecting value" in str(e):
            result = "Error: Invalid parameter value. Check for https, host, port, and apiKeys. If you use external server, "
            "make sure https is set to True."
    finally:
        if debug_log:
            logger.info("-" * 50)
            logger.debug("Query: " + text.strip())
            logger.debug("Translation Get: " + result)
        return is_Success, result
