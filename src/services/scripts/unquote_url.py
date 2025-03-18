

try:
    from urllib import unquote
except ImportError:
    from urllib.parse import unquote

print(unquote("%CE%B1%CE%BB%20"))