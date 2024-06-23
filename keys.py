import ubinascii              # type: ignore # Conversions between binary data and various encodings
import machine                # type: ignore # To Generate a unique id from processor

# Wireless network
WIFI_SSID = 'YOUR_WIFI_SSID'
WIFI_PASS = 'WIFI_PASSWORD'

# Adafruit IO (AIO) configuration
AIO_SERVER = "io.adafruit.com"
AIO_PORT = 1883
AIO_USER = "USERNAME"
AIO_KEY = "KEY"
AIO_CLIENT_ID = ubinascii.hexlify(machine.unique_id())  # Can be anything
AIO_LIGHTS_FEED = "USER/feeds/lights"
AIO_MAIL_ENTRY_FEED = "USER/feeds/mailboxentries"
AIO_OPEN_MAIL_FEED = "USER/feeds/opened-mailbox"