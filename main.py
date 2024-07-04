from machine import Pin     
import machine           
import keys                   # imports the required credentials for wifi and adafruit io
import time                   # Allows use of time.sleep() for delays
from mqtt import MQTTClient   # For use of MQTT protocol to talk to Adafruit IO
import wifiConnection         # Contains functions to connect/disconnect from WiFi 
import ntptime                # Used to set up the rtc time in the pico device in utc (doesnt account for time zones)




# Configure time intervals and counters
publish_message_interval = 1.2 * 10**6  # publish data to adafruit every 20 minutes
last_sent_mail_entry = 0                # number of ms after the last sent message to adafruit
last_sent_open_mailbox_entry = 0        # number of ms after the last sent message to adafruit
new_mail_entry_count = 0                # delivery entries counter
open_mailbox_count = 0                  # number of times the mailbox was opened
last_random_sent_ticks = 0              # milliseconds

# Led lights
red = Pin(14, Pin.OUT)
green = Pin(15, Pin.OUT)
yellow = Pin(13, Pin.OUT)
led = Pin("LED", Pin.OUT) 

# Tilt and PIR sensor
tilt = Pin(22, Pin.IN)
pir = Pin(26, Pin.IN)



# Function to publish the number of mail deliveries to Adafruit IO MQTT server at "publish_message_interval"
def send_new_mail_entry(counter_value: int):
  global last_sent_mail_entry
  global publish_message_interval

  if ((time.ticks_ms() - last_sent_mail_entry) < publish_message_interval):
    return False; # Too soon since last one sent.
  print("Publishing: {0} new mail entry to {1} ... ".format(counter_value, keys.AIO_MAIL_ENTRY_FEED), end='')

  try:
    client.publish(topic=keys.AIO_MAIL_ENTRY_FEED, msg=str(counter_value))
    print("DONE")
  except Exception as e:
    print("FAILED")
  finally:
    last_sent_mail_entry = time.ticks_ms()



# Function to publish the number of times the mail was opened to Adafruit IO MQTT server at "publish_message_interval"
def send_open_mailbox_entry(counter_value: int):
  global last_sent_open_mailbox_entry
  global publish_message_interval

  if ((time.ticks_ms() - last_sent_open_mailbox_entry) < publish_message_interval):
    return False; # Too soon since last one sent.
  print("Publishing: {0} open mail entry to {1} ... ".format(counter_value, keys.AIO_OPEN_MAIL_FEED), end='')

  try:
    client.publish(topic=keys.AIO_OPEN_MAIL_FEED, msg=str(counter_value))
    print("DONE")
  except Exception as e:
    print("FAILED")
  finally:
    last_sent_open_mailbox_entry = time.ticks_ms()


# Function to set the indicator on the Adafruit IO dashboard
# Red means the device is asleep and Green means the device is awake and active
def send_mailbox_activity(value):
  if value == 1:
    print("Publishing: {0} Mailbox is still active ... ".format(keys.AIO_SLEEP_FEED), end='')
  else:
    print("Publishing: {0} Mailbox is going to sleep ... ".format(keys.AIO_SLEEP_FEED), end='')

  try:
    client.publish(topic=keys.AIO_SLEEP_FEED, msg=str(value))
    print("DONE")
  except Exception as e:
    print("FAILED")


# WiFi Connection
try:
  ip = wifiConnection.connect()
except KeyboardInterrupt:
  print("Keyboard interrupt")


# Use the MQTT protocol to connect to Adafruit IO
client = MQTTClient(keys.AIO_CLIENT_ID, keys.AIO_SERVER, keys.AIO_PORT, keys.AIO_USER, keys.AIO_KEY)


# Connect to the MQTT server
client.connect()
print("Connected to %s" % (keys.AIO_SERVER))

# Configure the date and time of the pico using the ntp library
# (yrs, mths, day, wkday, hrs, m, s, subseconds) format
rtc = machine.RTC()
ntptime.settime()

# Check if the date and time is configure correctly on the device 
print("Current time: ", rtc.datetime())

# Enter time offset (ntp doesn't account for timezones)
time_offset = 2   # +2 hours




print("Mailbox waking up.................")
# Publish data to the sleep feed that the device is now awake
send_mailbox_activity(1)
# A short wait period to make sure the data was published
time.sleep(3)

# MAIN LOGIC OF THE DEVICE IN A WHILE LOOP
try:          # Code between try: and finally: may cause an error
              # so ensure the client disconnects the server if
              # that happens.
  # Send to Adafruit that the device is awake
  while True:   
    # Checks if the mail is open i.e the tilt sensor is triggered
    if tilt.value() == 1:
      print("Mail open !")

      # Led indicators
      green.off()
      red.on()

      pir.value(0)  # intialize the pir sensor which might have been triggered by the tilt action

      # Added a time sleep to improve accuracy and reduce false positives
      time.sleep(1.5)

      # Logic for checking if there is a new mail delivery
      if pir.value() == 1 and (tilt.value() == 1 or tilt.value() == 0):
        # increases the new mail entry counter value by 1
        new_mail_entry_count += 1
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
      print("...", end='')
      # Led indicators
      red.off()
      yellow.off()
      green.on()
      time.sleep(0.5) 
    
    # PUBLISHES THE DATA TO ADAFRUIT AT FIXED INTERVALS 
    # Whenever the following if conditions are met, the counter starts from zero again
    if send_open_mailbox_entry(open_mailbox_count) != False:
      open_mailbox_count = 0
    if send_new_mail_entry(new_mail_entry_count) != False:
      new_mail_entry_count = 0
    
    # Checks if the current hour is between the 07:00 and 17:00 (common delivery hours)
    current_time =  rtc.datetime()  # used to get time in (yrs, mths, day, wkday, hrs, m, s, subseconds) format
    current_hour = tuple(current_time)[4]   # gets the current hour from the current_time
    current_hour += time_offset

    # The hour interval in which the pico w device is active is 7-17
    sleep_hour = 24 - (17-7)
    sleep_hour_ms = sleep_hour * 3600000
    if (7 <= current_hour < 17) is False:
      # Changes the indicator in the dashboard to red i.e 
      send_mailbox_activity(0)
      print("Mailbox going to sleep............")
      led.on()
      time.sleep(3)
      machine.deepsleep(sleep_hour_ms)
      # machine.deepsleep(900000)    # deep sleeps for 15 minutes can be changed to suit your preference





finally:                  # If an exception is thrown ...
  client.disconnect()   # ... disconnect the client and clean up.
  client = None
  wifiConnection.disconnect()
  print("Disconnected from Adafruit IO.")

