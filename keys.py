import ubinascii              # type: ignore # Conversions between binary data and various encodings
import machine                # type: ignore # To Generate a unique id from processor

# Wireless network
WIFI_SSID = 'YOUR_WIFI_NAME'
WIFI_PASS = 'YOUR_WIFI_PASSWORD'

# Adafruit IO (AIO) configuration
AIO_SERVER = "io.adafruit.com"
AIO_PORT = 1883
AIO_USER = "YOUR_AIO_USERNAME"
AIO_KEY = "YOUR_AIO_KEY"
AIO_CLIENT_ID = ubinascii.hexlify(machine.unique_id())  # Can be anything
AIO_MAIL_ENTRY_FEED = "YOUR_AIO_USERNAME/feeds/mailboxentries"
AIO_OPEN_MAIL_FEED = "YOUR_AIO_USERNAME/feeds/opened-mailbox"
AIO_SLEEP_FEED = "YOUR_AIO_USERNAME/feeds/sleep-feed"