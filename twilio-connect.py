TWILIO_ACCOUNT = "X" # Your Account SID from www.twilio.com/console
TWILIO_TOKEN  = "X"  # Your Auth Token from www.twilio.com/console
TWILIO_PHONE = "" # Your phone

import sopel.module
from twilio.rest import TwilioRestClient
from twilio.rest.lookups import TwilioLookupsClient
from twilio.rest.exceptions import TwilioRestException
import urllib

@sopel.module.commands('listphone')
def listphone(bot, trigger):
  if not trigger.group(3):
      bot.reply("No username given.")
      return

  nick = trigger.group(3)
  phone = bot.db.get_nick_value(nick, 'twilio_info')

  if phone:
    bot.reply('Phone number for ' + nick + ' is ' + phone)
  else:
    bot.reply(nick + " doesn't have a phone associated")

@sopel.module.commands('setphone')
def setphone(bot, trigger):
  if not trigger.group(3):
      bot.reply("No username given.")
      return

  if not trigger.group(4):
      bot.reply("No phone given.")
      return

  phone = trigger.group(4)
  nick = trigger.group(3)

  if is_valid_number(phone):
    bot.db.set_nick_value(nick, 'twilio_info', phone)
    bot.reply('Thanks! Phone added for ' + nick)
  else:
    bot.reply('The phone number is not valid, please check it ')

@sopel.module.commands('sms', 'trigger')
def sms(bot, trigger):

  if not trigger.group(3):
    bot.reply("No username given.")
    return

  user = trigger.group(3)
  phone = bot.db.get_nick_value(user, 'twilio_info')

  if not phone:
    bot.reply("That username doesn't have a phone associated")
    return

  raw_args = trigger.group(2)
  command_parts = raw_args.split(' ', 1)

  if len(command_parts) < 2:
    bot.reply('You need to add a message.')
    return
  else:
    message = command_parts[1]

  message = send_sms(bot, phone, message, trigger.nick)
  bot.reply('Cool. I just sent the SMS and Twilio will do the magic.')
  bot.reply('FYI. SMS id is: ' + message.sid)

@sopel.module.commands('call', 'trigger')
def call(bot, trigger):

  if not trigger.group(3):
    bot.reply("No username given.")
    return

  user = trigger.group(3)
  phone = bot.db.get_nick_value(user, 'twilio_info')

  if not phone:
    bot.reply("That username doesn't have a phone associated")
    return

  raw_args = trigger.group(2)
  command_parts = raw_args.split(' ', 1)

  if len(command_parts) < 2:
    bot.reply('You need to add a message.')
    return
  else:
    message = command_parts[1]

  call = call_user(bot, phone, message)
  bot.reply('Cool. I just made the call and Twilio will do the magic.')
  bot.reply('FYI. Call id is: ' + call.sid)

@sopel.module.commands('smsstatus', 'trigger')
def smsstatus(bot, trigger):

  if not trigger.group(3):
    bot.reply("No SMS id given.")
    return

  sms_id = trigger.group(3)

  status = get_sms_status(sms_id)

  if status:
    bot.reply("Your message status is: " + status.status)
  else:
    bot.reply("I can't find anything about that SMS. Please double check your id")

@sopel.module.commands('callstatus', 'trigger')
def callstatus(bot, trigger):

  if not trigger.group(3):
    bot.reply("No Call id given.")
    return

  call_id = trigger.group(3)

  status = get_call_status(call_id)

  if status:
    bot.reply("Your call status is: " + status.status)
  else:
    bot.reply("I can't find anything about that call. Please double check your id")

def get_phone_username(args, db_nick):
  if args and len(args.strip()) > 0:
      return args
  if db_nick:
      return db_nick
  return None

def send_sms(bot, phone, message, nick_from):
  client = TwilioRestClient(TWILIO_ACCOUNT, TWILIO_TOKEN)

  message = client.messages.create(body='(IRC) ' + nick_from + ": " + message,
      to=phone,
      from_=TWILIO_PHONE)

  return message

def get_sms_status(sms_id):
  client = TwilioRestClient(TWILIO_ACCOUNT, TWILIO_TOKEN)

  message = client.messages.get(sms_id)

  return message

def get_call_status(call_id):
  client = TwilioRestClient(TWILIO_ACCOUNT, TWILIO_TOKEN)

  call = client.calls.get(call_id)

  return call

def call_user(bot, phone, message):
  client = TwilioRestClient(TWILIO_ACCOUNT, TWILIO_TOKEN)

  twiml_url = create_file(message)

  call = client.calls.create(url=twiml_url,
      to=phone,
      from_=TWILIO_PHONE,
      method="GET")

  return call

def create_file(message):
  return "http://twimlets.com/message?Message%5B0%5D=" + urllib.quote_plus("Hi, this is a message from IRC") + "&Message%5B1%5D=" + urllib.quote_plus(message) + "&"

def is_valid_number(number):
  client = TwilioLookupsClient(TWILIO_ACCOUNT, TWILIO_TOKEN)
  try:
      response = client.phone_numbers.get(number, include_carrier_info=True)
      response.phone_number  # If invalid, throws an exception.
      return True
  except TwilioRestException as e:
      if e.code == 20404:
          return False
      else:
          raise e
