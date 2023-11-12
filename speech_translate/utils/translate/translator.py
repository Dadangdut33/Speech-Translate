from typing import Dict, List
from speech_translate._logging import logger
from ..helper import get_similar_keys, no_connection_notify
from .language import GOOGLE_KEY_VAL, LIBRE_KEY_VAL, MYMEMORY_KEY_VAL

import requests

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
        assert isinstance(GOOGLE_KEY_VAL, Dict)
        try:
            LCODE_FROM = GOOGLE_KEY_VAL[from_lang]
            LCODE_TO = GOOGLE_KEY_VAL[to_lang]
        except KeyError:
            logger.warning("Language Code Undefined. Trying to get similar keys")
            try:
                LCODE_FROM = GOOGLE_KEY_VAL[get_similar_keys(GOOGLE_KEY_VAL, from_lang)[0]]
                logger.debug(f"Got similar key for GOOGLE LANG {from_lang}: {LCODE_FROM}")
            except KeyError:
                logger.warning("Source Language Code Undefined. Using auto")
                LCODE_FROM = "auto"
            LCODE_TO = GOOGLE_KEY_VAL[get_similar_keys(GOOGLE_KEY_VAL, to_lang)[0]]
    except KeyError as e:
        logger.exception(e)
        return is_Success, "Error Language Code Undefined"

    # using deep_translator v 1.11.1
    # --- Translate ---
    try:
        if TlCon.GoogleTranslator is None:
            try:
                from deep_translator import GoogleTranslator

                TlCon.GoogleTranslator = GoogleTranslator
            except Exception:
                no_connection_notify()
                return is_Success, "Error: Not connected to internet"

        result = TlCon.GoogleTranslator(source=LCODE_FROM, target=LCODE_TO, proxies=proxies).translate_batch(text)
        is_Success = True
    except Exception as e:
        logger.exception(e)
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
        assert isinstance(MYMEMORY_KEY_VAL, Dict)
        try:
            LCODE_FROM = MYMEMORY_KEY_VAL[from_lang]
            LCODE_TO = MYMEMORY_KEY_VAL[to_lang]
        except KeyError:
            logger.warning("Language Code Undefined. Trying to get similar keys")
            try:
                LCODE_FROM = MYMEMORY_KEY_VAL[get_similar_keys(MYMEMORY_KEY_VAL, from_lang)[0]]
                logger.debug(f"Got similar key for GOOGLE LANG {from_lang}: {LCODE_FROM}")
            except KeyError:
                logger.warning("Source Language Code Undefined. Using auto")
                LCODE_FROM = "auto"
            LCODE_TO = MYMEMORY_KEY_VAL[get_similar_keys(MYMEMORY_KEY_VAL, to_lang)[0]]
    except KeyError as e:
        logger.exception(e)
        return is_Success, "Error Language Code Undefined"

    # using deep_translator v 1.11.1
    # --- Translate ---
    try:
        if TlCon.MyMemoryTranslator is None:
            try:
                from deep_translator import MyMemoryTranslator

                TlCon.MyMemoryTranslator = MyMemoryTranslator
            except Exception:
                no_connection_notify()
                return is_Success, "Error: Not connected to internet"

        result = TlCon.MyMemoryTranslator(source=LCODE_FROM, target=LCODE_TO, proxies=proxies).translate_batch(text)
        is_Success = True
    except Exception as e:
        result = str(e)
        logger.exception(e)
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
            from_lang_code = LIBRE_KEY_VAL[from_lang]
            to_LanguageCode_Libre = LIBRE_KEY_VAL[to_lang]
        except KeyError:
            try:
                from_lang_code = LIBRE_KEY_VAL[get_similar_keys(LIBRE_KEY_VAL, from_lang)[0]]
                logger.debug(f"Got similar key for LIBRE LANG {from_lang}: {from_lang_code}")
            except KeyError:
                logger.warning("Source Language Code Undefined. Using auto")
                from_lang_code = "auto"
            to_LanguageCode_Libre = LIBRE_KEY_VAL[get_similar_keys(LIBRE_KEY_VAL, to_lang)[0]]
    except KeyError as e:
        logger.exception(e)
        return is_Success, "Error Language Code Undefined"

    # shoot from API directly using requests
    # --- Translate ---
    try:
        req = {"q": text, "source": from_lang_code, "target": to_LanguageCode_Libre, "format": "text"}
        httpStr = "https" if libre_https else "http"

        if libre_port != "":
            adr = httpStr + "://" + libre_host + ":" + libre_port + "/translate"
        else:
            adr = httpStr + "://" + libre_host + "/translate"

        if libre_api_key != "":
            req["api_key"] = libre_api_key

        arr = []
        for q in text:
            req["q"] = q
            response = requests.post(adr, json=req, proxies=proxies).json()
            if "error" in response:
                raise Exception(response["error"])

            translated = response["translatedText"]
            arr.append(translated)

        result = arr
        is_Success = True
    except Exception as e:
        result = str(e)
        logger.exception(e)
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

    # making sure that it is in lower case
    from_lang = from_lang.lower()
    to_lang = to_lang.lower()

    return tl_dict[engine](text, from_lang, to_lang, proxies, debug_log, **kwargs)
