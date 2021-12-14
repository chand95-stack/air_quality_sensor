import os
import time
import busio
import digitalio
import board
import adafruit_mcp3xxx.mcp3008 as MCP
from adafruit_mcp3xxx.analog_in import AnalogIn

cs = digitalio.DigitalInOut(board.D22)

spi = busio.SPI(clock=board.SCK, MISO=board.MISO, MOSI=board.MOSI)

mcp = MCP.MCP3008(spi,cs)
try:
    channel0 = AnalogIn(mcp, MCP.P0)
    channel1 = AnalogIn(mcp, MCP.P0)
    print("Sensor 1 Data")
    print("Raw ADC Value:{}".format(channel0.value))
    print("ADC Voltage: {:.2f}V".format(channel0.voltage))
    print("\n")
    print("Sensor 2 Data")
    print("Raw ADC Value:{}".format(str(channel1.value)))
except Exception as e:
    raise e
else:
    pass

