import os
import asyncio
from azure.iot.device import X509
from azure.iot.device.aio import ProvisioningDeviceClient
from azure.iot.device.aio import IoTHubDeviceClient
from azure.iot.device import Message
import uuid

# import package for sensors

import RPi.GPIO as GPIO
import time

# change these as desired - they're the pins connected from the
# SPI port on the ADC to the Cobbler
SPICLK = 11
SPIMISO = 9
SPIMOSI = 10
SPICS = 8
mq7_dpin = 26
mq7_apin = 0

provisioning_host = os.getenv("PROVISIONING_HOST")
id_scope = os.getenv("PROVISIONING_IDSCOPE")
registration_id = os.getenv("DPS_X509_REGISTRATION_ID")
messages_to_send = 10 #This needs to be chcecked and i will edit it later

def intit():
	GPIO.setwarnings(False)
	GPIO.cleanup()
	GPIO.setmode(GPIO.BCM)
	#set up the interface
	GPIO.setup(SPIMOSI, GPIO.OUT)
	GPIO.setup(SPIMISO, GPIO.IN)
	GPIO.setup(SPICLK, GPIO.OUT)
	GPIO.setup(SPICS, GPIO.OUT)
	GPIO.setup(mq7_dpin,GPIO.IN,pull_up_down=GPIO.PUD_DOWN)
#This is for reading data from sensors through MCP3008
def readadc(adcnum, clockpin, mosipin, misopin, cspin):
	if ((adcnum > 7) or (adcnum < 0)):
		return -1
		GPIO.output(cspin, True)	
		GPIO.output(clockpin, False)  # start clock low
		GPIO.output(cspin, False)     # bring CS low
		commandout = adcnum
		commandout |= 0x18  # start bit + single-ended bit
		commandout <<= 3    # we only need to send 5 bits here
		for i in range(5):
			if (commandout & 0x80):
				GPIO.output(mosipin, True)
			else:
				GPIO.output(mosipin, False)
				commandout <<=1
				GPIO.output(clockpin,True)
				GPIO.output(clockpin, False)
			adcout = 0
			# read in one empty bit, one null bit and 10 ADC bits
			for i in range(12):
				GPIO.output(clockpin, True)
				GPIO.output(clockpin, False)
				adcout <<=1
				if (GPIO.input(misopin)):
					adcout |=0x1
			GPIO.output(cspin, True)
			adcout >>=1
			return adcout
async def main():
	x509 = x509(
		cert_file=os.getenv("X509_CERT_FILE"),
		key_file=os.getenv("X509_KEY_FILE"),
		pass_phrase=os.getenv("PASS_PHRASE"),
		)

	provisioning_device_client = ProvisioningDeviceClient.create_from_x509_certificate(
		provisioning_host=provisioning_host,
		registration_id=registration_id,
		id_scope=id_scope,
		x509=x509,
		)
	registration_result = await provisioning_device_client.register()
	print(registration_result.registration_state)

	if registration_result.status == "assigned":
		print("Will send telemetry from the provisioned device")
		device_client = IoTHubDeviceClient.create_from_x509_certificate(x509=x509,hostname=registration_result.registration_state.assigned_hub,device_id=registration_result.registration_state.device_id)
		await device_client.connect()
		init()
		print("Starting the sensor takes 20sex to clean and get value")
		time.sleep(20)
		while True:
			COlevel=readadc(mq7_apin, SPICLK, SPIMOSI, SPIMISO, SPICS)
			if GPIO.input(mq7_dpin):
				print("CO not leak")
				time.sleep(0.5)
			else:
				print("CO is detected")
				value = str((COlevel/1024)*5)
				density = str((COlevel/1024)*100)
				data = value+" "+density
				await device_client.send_message(data)
				time.sleep(20)
				#await device_client_disconnect()
	else:
		print("Data Push error")
if __name__ == '__main__':
	asyncio.run(main())
