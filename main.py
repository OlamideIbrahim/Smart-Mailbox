import keys
import network # type: ignore
from time import sleep
import time                   # Allows use of time.sleep() for delays
from mqtt import MQTTClient   # For use of MQTT protocol to talk to Adafruit IO
import machine                # type: ignore # Interfaces with hardware components
import micropython            # type: ignore # Needed to run any MicroPython code
from machine import Pin       # type: ignore # Define pin
import wifiConnection         # Contains functions to connect/disconnect from WiFi 


def connect():
  wlan = network.WLAN(network.STA_IF)         # Put modem on Station mode
  if not wlan.isconnected():                  # Check if already connected
    print('connecting to network...')
    wlan.active(True)                       # Activate network interface
    # set power mode to get WiFi power-saving off (if needed)
    wlan.config(pm = 0xa11140)
    wlan.connect(keys.WIFI_SSID, keys.WIFI_PASS)  # Your WiFi Credential
    print('Waiting for connection...', end='')
    # Check if it is connected otherwise wait
    while not wlan.isconnected() and wlan.status() >= 0:
      print('.', end='')
      sleep(1)
  # Print the IP assigned by router
  ip = wlan.ifconfig()[0]
  print('\nConnected on {}'.format(ip))
  return ip

def http_get(url = 'http://detectportal.firefox.com/'):
  import socket                           # Used by HTML get request
  import time                             # Used for delay
  _, _, host, path = url.split('/', 3)    # Separate URL request
  addr = socket.getaddrinfo(host, 80)[0][-1]  # Get IP address of host
  s = socket.socket()                     # Initialise the socket
  s.connect(addr)                         # Try connecting to host address
  # Send HTTP request to the host with specific path
  s.send(bytes('GET /%s HTTP/1.0\r\nHost: %s\r\n\r\n' % (path, host), 'utf8'))    
  time.sleep(1)                           # Sleep for a second
  rec_bytes = s.recv(10000)               # Receve response
  print(rec_bytes)                        # Print the response
  s.close()                               # Close connection

# WiFi Connection
try:
  ip = connect()
except KeyboardInterrupt:
  print("Keyboard interrupt")

# HTTP request
try:
  http_get()
except (Exception, KeyboardInterrupt) as err:
  print("No Internet", err)



# BEGIN SETTINGS
# These need to be change to suit your environment
RANDOMS_INTERVAL = 20000            # milliseconds
opened_mailbox_interval = 120000 # 1.44 * 10**7 # 4 hours interval i.e 4 * 3.6 * 10^6
entry_interval = 120000 # 7.2 * 10**6 # 2 hours interval
last_sent_mail_entry = 0            # number of ms after the last sent message to adafruit
last_sent_open_mailbox_entry = 0    # number of ms after the last sent message to adafruit
new_mail_entry_value = 0            # number delivery entries
open_mailbox_count = 0              # number of times the mailbox was opened
last_random_sent_ticks = 0          # milliseconds
led = Pin("LED", Pin.OUT)           # led pin initialization for Raspberry Pi Pico W

red = Pin(14, Pin.OUT)
green = Pin(15, Pin.OUT)
tilt = Pin(2, Pin.IN)
pir = Pin(10, Pin.IN)
yellow = Pin(13, Pin.OUT)
en_pin = Pin(2, Pin.OUT)

# Callback Function to respond to messages from Adafruit IO
def sub_cb(topic, msg):          # sub_cb means "callback subroutine"
  print((topic, msg))          # Outputs the message that was received. Debugging use.
  if msg == b"ON":             # If message says "ON" ...
    led.on()                 # ... then LED on
  elif msg == b"OFF":          # If message says "OFF" ...
    led.off()                # ... then LED off
  else:                        # If any other message is received ...
    print("Unknown message") # ... do nothing but output that it happened.


# Function to publish the number of mail deliveries to Adafruit IO MQTT server at "entry_interval"
def send_new_mail_entry(counter_value: int):
  global last_sent_mail_entry
  global entry_interval

  if ((time.ticks_ms() - last_sent_mail_entry) < entry_interval):
    return False; # Too soon since last one sent.
  print("Publishing: {0} new mail entry to {1} ... ".format(counter_value, keys.AIO_MAIL_ENTRY_FEED), end='')

  try:
    client.publish(topic=keys.AIO_MAIL_ENTRY_FEED, msg=str(counter_value))
    print("DONE")
  except Exception as e:
    print("FAILED")
  finally:
    last_sent_mail_entry = time.ticks_ms()

# Function to publish the number of times the mail was opened to Adafruit IO MQTT server at "entry_interval"
def send_open_mailbox_entry(counter_value: int):
  global last_sent_open_mailbox_entry
  global opened_mailbox_interval

  if ((time.ticks_ms() - last_sent_open_mailbox_entry) < opened_mailbox_interval):
    return False; # Too soon since last one sent.
  print("Publishing: {0} open mail entry to {1} ... ".format(counter_value, keys.AIO_OPEN_MAIL_FEED), end='')

  try:
    client.publish(topic=keys.AIO_OPEN_MAIL_FEED, msg=str(counter_value))
    print("DONE")
  except Exception as e:
    print("FAILED")
  finally:
    last_sent_open_mailbox_entry = time.ticks_ms()

# Try WiFi Connection
try:
  ip = wifiConnection.connect()
except KeyboardInterrupt:
  print("Keyboard interrupt")

# Use the MQTT protocol to connect to Adafruit IO
client = MQTTClient(keys.AIO_CLIENT_ID, keys.AIO_SERVER, keys.AIO_PORT, keys.AIO_USER, keys.AIO_KEY)

# Subscribed messages will be delivered to this callback
client.set_callback(sub_cb)
client.connect()
client.subscribe(keys.AIO_LIGHTS_FEED)
print("Connected to %s, subscribed to %s topic" % (keys.AIO_SERVER, keys.AIO_LIGHTS_FEED))


# MAIL LOGIC OF THE DEVICE 
try:          # Code between try: and finally: may cause an error
              # so ensure the client disconnects the server if
              # that happens.
  while 1:              
    client.check_msg()  # Action a message if one is received. Non-blocking.

    # Checks if the mail is open i.e the tilt sensor is triggered
    if tilt.value() == 1:
      print("Mail open !")
      print("PIR value: ", pir.value())
      print("Tilt value: ", tilt.value())

      # Led indicators
      green.off()
      red.on()
      
      # Need to place the time.sleep() command strategically to improve accuracy of reading
      pir.value(0)  # intialize the pir sensor which might have been triggered by the tilt action
      print("PIR value before any action: ", pir.value())

      # Added a time sleep to improve accuracy and reduce false positives
      time.sleep(3)
      print("NEW PIR value: ", pir.value())
      print("NEW Tilt value: ", tilt.value())

      # Logic for checking if there is a new mail delivery
      if pir.value() == 1 and (tilt.value() == 1 or tilt.value() == 0):
        # increases the new mail entry counter value by 1
        new_mail_entry_value += 1
        print("New drop in mailbox !")

        # Led indicators
        green.off()
        red.off()
        yellow.on()
        time.sleep(0.5)
      else:
        # counts the amount of time the mail has been opened within a time interval
        open_mailbox_count += 1


      
    else:
      print("...")

      # Led indicators
      red.off()
      yellow.off()
      green.on()
      time.sleep(0.5)
      
    # PUBLISHES THE DATA TO ADAFRUIT AT FIXED INTERVALS 
    # When the following if conditions are met, the counter starts from zero again
    if send_open_mailbox_entry(open_mailbox_count) != False:
      open_mailbox_count = 0
    if send_new_mail_entry(new_mail_entry_value) != False:
      new_mail_entry_value = 0



finally:                  # If an exception is thrown ...
  client.disconnect()   # ... disconnect the client and clean up.
  client = None
  wifiConnection.disconnect()
  print("Disconnected from Adafruit IO.")

















import time

red = Pin(14, Pin.OUT)
green = Pin(15, Pin.OUT)
tilt = Pin(2, Pin.IN)
pir = Pin(10, Pin.IN)
yellow = Pin(13, Pin.OUT)
en_pin = Pin(2, Pin.OUT)

while True:
  print("Tilt value: ", tilt.value())
  print("PIR value: ", pir.value())

  if tilt.value() == 1:
    print("Mail open !")
    print("PIR value: ", pir.value())
    green.off()
    red.on()
  
  # Need to place the time.sleep() command strategically to improve accuracy of reading
  time.sleep(2)
  pir.value(0)
  if tilt.value() == 1 and pir.value() == 0:
    print("Why are you peeking into my mailbox ?")
  elif pir.value() == 1 and tilt.value == 1:
    print("New drop in mailbox !")
    green.off()
    red.off()
    yellow.on()
    time.sleep(0.5)

  
  else:
    print("Nothing in mailbox....")
    red.off()
    yellow.off()
    green.on()
    time.sleep(0.5)
