#!/usr/bin/python2.7

import json
import socket
import logging
import sys
import getopt
import time
import urllib2
import paho.mqtt.publish as publish
from ConfigParser import SafeConfigParser
import os

log = None

def initLogger(name):
    global log
    logging.basicConfig(filename=os.path.dirname(os.path.realpath(__file__)) +"NeohubInterface"+name+".log", level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
    log = logging.getLogger(__name__)
    soh = logging.StreamHandler(sys.stdout)
    soh.setFormatter(logging.Formatter("%(asctime)s [%(levelname)s] %(message)s"))
    log.addHandler(soh)
    log.setLevel(logging.INFO)

class HeatmiserNeostat:
    """ Represents a Heatmiser Neostat thermostat. """
    def __init__(self,  host, port, name):
        self._name = name
        self._host = host
        self._port = port
        self._operation = "Null"

    @property
    def standby(self):
        return self._standby

    @property
    def deviceResponse(self):
        return self._deviceResponse

    @property
    def should_poll(self):
        """ No polling needed for a demo thermostat. """
        return True

    @property
    def name(self):
        """ Returns the name. """
        return self._name

    @property
    def operation(self):
        """ Returns current operation. heat, cool idle """
        return self._operation

    @property
    def unit_of_measurement(self):
        """ Returns the unit of measurement. """
        return self._unit_of_measurement

    @property
    def current_temperature(self):
        """ Returns the current temperature. """
        return self._current_temperature

    @property
    def target_temperature(self):
        """ Returns the temperature we try to reach. """
        return self._target_temperature

    @property
    def is_away_mode_on(self):
        """ Returns if away mode is on. """
        return self._away

    def set_temperature(self, temperature):
        """ Set new target temperature. """
        response = self.json_request({"SET_TEMP": [int(temperature), self._name]})
        if response:
            log.info("set_temperature response: %s " % response)
            # Need check for sucsess here
            # {'result': 'temperature was set'}

    def turn_away_mode_on(self):
        """ Turns away mode on. """
        log.debug("Entered turn_away_mode_on for device: %s" % self._name)
        response = self.json_request({"AWAY_ON":self._name})
        if response:
            log.info("turn_away_mode_on request: %s " % response)
            # Need check for success here
            # {"result":"away on"}
            # {"error":"Could not complete away on"}
            # {"error":"Invalid argument to AWAY_OFF, should be a valid device array of valid devices"}

    def turn_away_mode_off(self):
        """ Turns away mode off. """
        log.info("Entered turn_away_mode_off for device: %s" % self._name)
        response = self.json_request({"AWAY_OFF":self._name})
        if response:
            log.info("turn_away_mode_off response: %s " % response)
            # Need check for success here
            # {"result":"away off"}
            # {"error":"Could not complete away off"}
            # {"error":"Invalid argument to AWAY_OFF, should be a valid device or


    def turn_frost_mode_off(self):
        """ Turns frost mode off. """
        log.info("Entered turn_away_mode_off for device: %s" % self._name)
        response = self.json_request({"FROST_OFF":self._name})
        if response:
            log.info("turn_frost_mode_off response: %s " % response)
            # Need check for success here
            # {"result":"frost off"}
            # {"error":"Could not complete frost off"}
            # {"error":"Invalid argument to FROST_OFF, should be a valid device or


    def turn_frost_mode_on(self):
        """ Turns frost mode om. """
        log.info("Entered turn_frost_mode_on for device: %s" % self._name)
        response = self.json_request({"FROST_ON":self._name})
        if response:
            log.info("turn_frost_mode_on response: %s " % response)
            # Need check for success here
            # {"result":"frost on"}
            # {"error":"Could not complete frost on"}
            # {"error":"Invalid argument to FROST_ON, should be a valid device or

    def update(self):
        """ Get Updated Info. """
        log.debug("Entered update(self)")
        response = self.json_request({"INFO": "0"})
        if response:
            # Add handling for multiple thermostats here
            log.debug("update() json response: %s " % response)

            counter = 0
            deviceResponse = ""

            log.debug("Neostats Found:")
            for devices in response['devices']:
                deviceName = devices['device']
                log.debug(str(counter) + ": " + deviceName)
                if (deviceName == self.name):
                    deviceResponse = devices
                counter += 1


            if (deviceResponse):
                #self._name = device['device']
                log.info("Neostat Found = " + self.name)
                tmptempfmt = deviceResponse["TEMPERATURE_FORMAT"]

                if (tmptempfmt is False) or (tmptempfmt.upper() == "C"):
                    self._unit_of_measurement = "TEMP_CELCIUS"
                else:
                    self._unit_of_measurement = "TEMP_FAHRENHEIT"

                log.debug("Temperature Format = " + self.unit_of_measurement)

                self.standby = deviceResponse["STANDBY"]
                self._away = deviceResponse['AWAY']
                self._target_temperature = round(float(deviceResponse["CURRENT_SET_TEMPERATURE"]), 2)
                self._current_temperature = round(float(deviceResponse["CURRENT_TEMPERATURE"]), 2)

                if (deviceResponse["HEATING"]):
                    self._operation = "Heating"
                elif (deviceResponse["COOLING"]):
                    self._operation = "Cooling"
                else:
                    self._operation = "Idle"

        return False

    def printThermostatStatus(self):
        log.info("Printing Thermostat Status")
        log.info("Name: " + self.name)
        log.info("Temperature Format: " + str(self.unit_of_measurement))
        log.info("Away: " + str(self.is_away_mode_on))
        log.info("Target Temperature: " + str(self.target_temperature))
        log.info("Current Temperature: " + str(self.current_temperature))
        log.info("Standby: " + str(self.standby))
        log.info("Operation: " + self.operation)

    def json_request(self, request=None, wait_for_response=False):
        """ Communicate with the json server. """
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(5)

        try:
            sock.connect((self._host, self._port))
        except OSError:
            log.error("Error connecting to Neohub")
            sock.close()
            return False

        if not request:
            # no communication needed, simple presence detection returns True
            sock.close()
            return True

        log.debug("json_request: %s " % request)

        sock.send(bytearray(json.dumps(request) + "\0\r", "utf-8"))
        try:
            buf = sock.recv(4096)
        except socket.timeout:
            # something is wrong, assume it's offline
            log.error("Timeout error")
            sock.close()
            return False

        # read until a newline or timeout
        buffering = True
        while buffering:
            if "\n" in str(buf):
                response = str(buf).split("\n")[0]
                buffering = False
            else:
                try:
                    more = sock.recv(4096)
                except socket.timeout:
                    more = None
                if not more:
                    buffering = False
                    response = str(buf)
                else:
                    buf += more

        sock.close()

        response = response.rstrip('\0')

        log.debug("json_response: %s " % response)

        return json.loads(response, strict=False)

def updateDomoticzHttp(domoticzUrl, switchidx, tempidx, NeoStat, updateInterval):
    while True:
        NeoStat.update()
        time.sleep(updateInterval)
        try:
            url = domoticzUrl + "/json.htm?type=command&param=udevice&idx=" + str(tempidx) + "&nvalue=0&svalue=" + str(
                NeoStat.current_temperature)
            urllib2.urlopen(url)
            log.info("Temperature updated: " + url)
            switchUrl = domoticzUrl + "/json.htm?type=devices&rid=" + switchidx
            log.debug("SwitchURL: " + switchUrl)
            status = json.load(urllib2.urlopen(switchUrl))['result'][0]['Status']
            log.debug("Switch Status: " + status + " - NeoStat Status: " + NeoStat.operation)
            if status == "Off" and NeoStat.operation == "Heating":
                switchOnUrl = domoticzUrl + "/json.htm?type=command&param=switchlight&idx=" + str(switchidx) + "&switchcmd=On"
                log.info("Turn Switch " + str(switchidx) + " On")
                urllib2.urlopen(switchOnUrl)
            elif status == "On" and NeoStat.operation == "Idle":
                switchOffUrl = domoticzUrl + "/json.htm?type=command&param=switchlight&idx=" + str(
                    switchidx) + "&switchcmd=Off"
                log.info("Turn Switch " + str(switchidx) + " Off")
                urllib2.urlopen(switchOffUrl)
            if (updateInterval == 0):
                break
        except socket.timeout, e:
            log.error("Timeout error occurred retrieving NeoStat data...")
        except urllib2.HTTPError, e:
            log.error("HTTP error - " + e)
        except urllib2.URLError, e:
            log.error("URL Error - " + e)
        except:
            log.error("Error Occurred...")

def updateMqtt(NeoStat, updateInterval):
    cfg = SafeConfigParser()
    cfg.optionxform = str
    cfg.read(os.path.dirname(os.path.realpath(__file__)) + "\\neohub.conf")
    host = cfg.get("mqtt", "hostname")
    port = eval(cfg.get("mqtt", "port"))
    topic = cfg.get("mqtt", "topic")
    qos = eval(cfg.get("mqtt", "qos"))
    retain = eval(cfg.get("mqtt", "retain"))
    client_id =  "neohub" + NeoStat.name  + str(os.getpid())
    if eval(cfg.get("mqtt", "auth")):
        auth = {"username": cfg.get("mqtt", "user"), "password": cfg.get("mqtt", "password")}
    else:
        auth = None

    while True:
        NeoStat.update()
        time.sleep(updateInterval)

        msgs = [{"topic": topic + NeoStat.name, "payload": """{ "temperature" : """ + str(NeoStat.current_temperature)
        + """, "status" : """ + NeoStat.operation + "\"" "  "
        + "}", "qos": qos, "retain": retain}]

        log.debug("msgs = " + str(msgs))

        publish.multiple(msgs, hostname=host, port=port, client_id=client_id, auth=auth)


def main(argv):
    try:
        opts, args = getopt.getopt(argv, "hsfi:", ["StatName=", "Mode=", "TempIDX", "SwitchIDX"])
    except getopt.GetoptError:
        print("NeoHubInterface.py -h -s -f -i --StatName --Mode --TempIDX --SwitchIDX")
        sys.exit(1)

    updateMode = True
    updateInterval = 0

    for opt, arg in opts:
        if opt in '-h':
            print("NeoHubInterface.py -h -s -f -i --StatName --Mode --TempIDX --SwitchIDX")
            sys.exit(2)
        elif (opt == "--StatName"):
            statName = arg
        elif (opt == "--TempIDX"):
            tempidx = int(arg)
        elif (opt == "--SwitchIDX"):
            switchidx = arg
        elif (opt == "--Mode"):
            mode = arg
        elif (opt == "-i"):
            updateInterval = float(arg)
        elif (opt == "-s"):
            updateMode = False
        elif (opt == "-f"):
            away = True

    cfg = SafeConfigParser()
    cfg.optionxform = str
    filepath = os.path.dirname(os.path.realpath(__file__)) + "\\"
    cfg.read(filepath + "neohub.conf")
    host = cfg.get("neohub", "host")
    port = cfg.get("neohub", "port")
    domoticz = cfg.get("domoticz", "url")

    initLogger(statName)

    log.info("NeoHub connection: " + host + ":" + str(port))

    NeoStat = HeatmiserNeostat(host, int(port), statName)

    if updateMode:
        if mode == "http":
            log.debug("HTTP Mode")
            updateDomoticzHttp(domoticz, switchidx, tempidx, NeoStat, updateInterval)
        elif mode == "mqtt":
            log.debug("MQTT Mode")
            updateMqtt(NeoStat, updateInterval)
        else:
            log.warning("No Update Mode selected")

    elif not updateMode:
        if (not away):
            NeoStat.turn_frost_mode_off()
        elif (away):
            NeoStat.turn_frost_mode_on()
    log.info("Exiting...")

main(sys.argv[1:])