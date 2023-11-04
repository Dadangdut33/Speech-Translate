from typing import Dict, List
from speech_translate._logging import logger
from ..helper import get_similar_keys, no_connection_notify
from .language import google_lang, libre_lang, myMemory_lang

# Import the translator
try:
    from deep_translator import GoogleTranslator, MyMemoryTranslator, LibreTranslator
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
        self.LibreTranslator = LibreTranslator


TlCon = TranslationConnection(GoogleTranslator, MyMemoryTranslator)


def google_tl(text: List[str], from_lang: str, to_lang: str, proxies: Dict, debug_log: bool = False):
    """Translate Using Google Translate

    Args
    ----
        text (List[str]): Text to translate
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
                                        proxies=proxies).translate_batch(text)
        is_Success = True
    except Exception as e:
        logger.exception(str(e))
        result = str(e)
    finally:
        if debug_log:
            logger.info("-" * 50)
            logger.debug("Query: " + str(text))
            logger.debug("Translation Get: " + str(result))
        return is_Success, result


def memory_tl(text: List[str], from_lang: str, to_lang: str, proxies: Dict, debug_log: bool = False):
    """Translate Using MyMemoryTranslator

    Args
    ----
        text (List[str]): Text to translate
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

        result = TlCon.MyMemoryTranslator(source=from_LanguageCode_Memory, target=to_LanguageCode_Memory,
                                          proxies=proxies).translate_batch(text)
        is_Success = True
    except Exception as e:
        logger.exception(str(e))
        result = str(e)
    finally:
        if debug_log:
            logger.info("-" * 50)
            logger.debug("Query: " + str(text))
            logger.debug("Translation Get: " + str(result))
        return is_Success, result


# LibreTranslator
def libre_tl(
    text: List[str],
    from_lang: str,
    to_lang: str,
    proxies: Dict,
    debug_log: bool,
    libre_https: bool,
    libre_host: str,
    libre_port: str,
    libre_api_key: str,
):
    """Translate Using LibreTranslate

    Args
    ----
        text (List[str]): Text to translate
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
        args = {}
        if libre_host != "":
            httpStr = "https" if libre_https else "http"
            libre_port = ":" + libre_port if libre_port != "" else ""
            args["custom_url"] = httpStr + "://" + libre_host + libre_port + "/translate"
            args["use_free_api"] = False

        if libre_api_key != "":
            args["api_key"] = libre_api_key
            args["use_free_api"] = False
        else:
            args["api_key"] = "-"  # need to pass something to avoid error
            args["use_free_api"] = True

        #     is_Success = True
        if TlCon.LibreTranslator is None:
            try:
                from deep_translator import LibreTranslator

                TlCon.LibreTranslator = LibreTranslator
            except Exception:
                no_connection_notify()
                return is_Success, "Error: Not connected to internet"

        result = TlCon.LibreTranslator(
            source=from_LanguageCode_Libre,
            target=to_LanguageCode_Libre,
            proxies=proxies,
            **args,
        ).translate_batch(text)
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
            logger.debug("Query: " + str(text))
            logger.debug("Translation Get: " + str(result))
        return is_Success, result


tl_dict = {
    "Google Translate": google_tl,
    "MyMemoryTranslator": memory_tl,
    "LibreTranslate": libre_tl,
}


def translate(engine: str, text: List[str], from_lang: str, to_lang: str, proxies: Dict, debug_log: bool = False, **kwargs):
    """Translate

    Args
    ----
        engine (str): Engine to use
        text (str): Text to translate
        from_lang (str): Language From
        to_lang (str): Language to translate
        proxies (Dict): Proxies. Defaults to None.
        debug_log (bool, optional): Debug Log. Defaults to False.
        **libre_kwargs: LibreTranslate kwargs

    Returns
    -------
        is_Success: Success or not
        result: Translation result
    """
    if engine not in tl_dict:
        raise ValueError(f"Invalid engine. Engine {engine} not found")

    return tl_dict[engine](text, from_lang, to_lang, proxies, debug_log, **kwargs)
