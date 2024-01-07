# pylint: disable=protected-access, redefined-outer-name, import-outside-toplevel, invalid-name
from typing import Dict, List

import requests
from loguru import logger
from tqdm.auto import tqdm

from ..helper import get_similar_keys, no_connection_notify
from .language import GOOGLE_KEY_VAL, LIBRE_KEY_VAL, MYMEMORY_KEY_VAL


def tl_batch_with_tqdm(self, batch: List[str], **kwargs) -> list:
    """Translate a batch of texts

    Args:
        batch (list): List of text to translate

    Returns:
        list: List of translated text
    """
    if not batch:
        raise Exception("Enter your text list that you want to translate")
    arr = []
    with_tqdm = kwargs.pop("with_tqdm", True)

    def _inner_tl(text: str):
        if text.isdigit():
            text += " "  # add a space in the end to prevent error
        return self.translate(text, **kwargs)

    if with_tqdm:
        for text in tqdm(batch, desc="Translating"):
            arr.append(_inner_tl(text))
    else:
        for text in batch:
            arr.append(_inner_tl(text))

    return arr


# Import the translator
try:
    from deep_translator import GoogleTranslator, MyMemoryTranslator
    GoogleTranslator._translate_batch = tl_batch_with_tqdm
    MyMemoryTranslator._translate_batch = tl_batch_with_tqdm
except Exception as e:
    GoogleTranslator = None
    MyMemoryTranslator = None
    if "HTTPSConnectionPool" in str(e):
        logger.error("No Internet Connection! / Host might be down")
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


def google_tl(text: List[str], from_lang: str, to_lang: str, proxies: Dict, debug_log: bool = False, **kwargs):
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
        is_success: Success or not
        result: Translation result
    """
    is_success = False
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
        return is_success, "Error Language Code Undefined"

    # using deep_translator v 1.11.1
    # --- Translate ---
    try:
        if TlCon.GoogleTranslator is None:
            try:
                from deep_translator import GoogleTranslator

                TlCon.GoogleTranslator = GoogleTranslator
                TlCon.GoogleTranslator._translate_batch = tl_batch_with_tqdm
            except Exception:
                no_connection_notify()
                return is_success, "Error: Not connected to internet"

        tl_kwargs = {}
        if kwargs.pop("live_input", False):
            tl_kwargs["with_tqdm"] = False

        result = TlCon.GoogleTranslator(source=LCODE_FROM, target=LCODE_TO,
                                        proxies=proxies).translate_batch(text, **tl_kwargs)
        is_success = True
    except Exception as e:
        logger.exception(e)
        result = str(e)
    finally:
        if debug_log:
            logger.info("-" * 50)
            logger.debug("Query: " + str(text))
            logger.debug("Translation Get: " + str(result))

    return is_success, result


def memory_tl(text: List[str], from_lang: str, to_lang: str, proxies: Dict, debug_log: bool = False, **kwargs):
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
        is_success: Success or not
        result: Translation result
    """
    is_success = False
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
        return is_success, "Error Language Code Undefined"

    # using deep_translator v 1.11.1
    # --- Translate ---
    try:
        if TlCon.MyMemoryTranslator is None:
            try:
                from deep_translator import MyMemoryTranslator

                TlCon.MyMemoryTranslator = MyMemoryTranslator
                TlCon.MyMemoryTranslator._translate_batch = tl_batch_with_tqdm
            except Exception:
                no_connection_notify()
                return is_success, "Error: Not connected to internet"

        tl_kwargs = {}
        if kwargs.pop("live_input", False):
            tl_kwargs["with_tqdm"] = False

        result = TlCon.MyMemoryTranslator(source=LCODE_FROM, target=LCODE_TO,
                                          proxies=proxies).translate_batch(text, **tl_kwargs)
        is_success = True
    except Exception as e:
        result = str(e)
        logger.exception(e)
    finally:
        if debug_log:
            logger.info("-" * 50)
            logger.debug("Query: " + str(text))
            logger.debug("Translation Get: " + str(result))
    return is_success, result


# LibreTranslator
def libre_tl(
    text: List[str],
    from_lang: str,
    to_lang: str,
    proxies: Dict,
    debug_log: bool,
    libre_link: str,
    libre_api_key: str,
    **kwargs,
):
    """Translate Using LibreTranslate

    Args
    ----
        text (List[str]): Text to translate
        from_lang (str): Language From
        to_lang (str): Language to translate
        proxies (Dict): Proxies. Defaults to None.
        debug_log (bool): Debug Log. Defaults to False.
        libre_link (str): LibreTranslate Link
        libre_api_key (str): LibreTranslate API Key

    Returns
    -------
        is_success: Success or not
        result: Translation result
    """
    is_success = False
    result = ""
    # --- Get lang code ---
    try:
        try:
            LCODE_FROM = LIBRE_KEY_VAL[from_lang]
            LCODE_TO = LIBRE_KEY_VAL[to_lang]
        except KeyError:
            try:
                LCODE_FROM = LIBRE_KEY_VAL[get_similar_keys(LIBRE_KEY_VAL, from_lang)[0]]
                logger.debug(f"Got similar key for LIBRE LANG {from_lang}: {LCODE_FROM}")
            except KeyError:
                logger.warning("Source Language Code Undefined. Using auto")
                LCODE_FROM = "auto"
            LCODE_TO = LIBRE_KEY_VAL[get_similar_keys(LIBRE_KEY_VAL, to_lang)[0]]
    except KeyError as e:
        logger.exception(e)
        return is_success, "Error Language Code Undefined"

    # shoot from API directly using requests
    # --- Translate ---
    try:
        req = {"q": text, "source": LCODE_FROM, "target": LCODE_TO, "format": "text"}
        libre_link += "/translate"

        if libre_api_key != "":
            req["api_key"] = libre_api_key

        arr = []
        if kwargs.pop("live_input", False):
            for q in text:
                req["q"] = q
                response = requests.post(libre_link, json=req, proxies=proxies, timeout=5).json()
                if "error" in response:
                    raise Exception(response["error"])
                translated = response["translatedText"]
                arr.append(translated)
        else:
            for q in tqdm(text, desc="Translating"):
                req["q"] = q
                response = requests.post(libre_link, json=req, proxies=proxies, timeout=5).json()
                if "error" in response:
                    raise Exception(response["error"])
                translated = response["translatedText"]
                arr.append(translated)

        result = arr
        is_success = True
    except Exception as e:
        result = str(e)
        logger.exception(e)
        if "NewConnectionError" in str(e):
            result = "Error: Could not connect. Please make sure that the server is running and the port is correct." \
            " If you are not hosting it yourself, please try again with an internet connection."
        if "request expecting value" in str(e):
            result = "Error: Invalid parameter value. Check for https, host, port, and apiKeys. " \
                "If you use external server, make sure https is set to True."
    finally:
        if debug_log:
            logger.info("-" * 50)
            logger.debug("Query: " + str(text))
            logger.debug("Translation Get: " + str(result))
    return is_success, result


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
        is_success: Success or not
        result: Translation result
    """
    if engine not in tl_dict:
        raise ValueError(f"Invalid engine. Engine {engine} not found")

    # making sure that it is in lower case
    from_lang = from_lang.lower()
    to_lang = to_lang.lower()

    return tl_dict[engine](text, from_lang, to_lang, proxies, debug_log, **kwargs)
