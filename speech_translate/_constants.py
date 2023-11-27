APP_NAME: str = "Speech Translate"
SUBTITLE_PLACEHOLDER = " " * 100
PREVIEW_WORDS = "1234567 Preview Hello مرحبًا プレビュー こんにちは 预习 你好 привет"
WHISPER_SR = 16_000
MIN_THRESHOLD = -61
MAX_THRESHOLD = 1
LOG_FORMAT = '<green>{time:YYYY-MM-DD HH:mm:ss.SSS}</green> | <level>{level: <7}</level> | <cyan>{file}</cyan>:<cyan>{line}</cyan> [{thread.name}] - <level>{message}</level>'
HACKY_SPACE = "‎"  # a empty character that is not empty # can be used when needing to replace a character with a space or something alike
