import RPi.GPIO as GPIO
import dht11
import time
import datetime
import requests
import json

# initialize GPIO
GPIO.setwarnings(True)
GPIO.setmode(GPIO.BCM)

# read data using pin 4
instance = dht11.DHT11(pin=4)

# get auth token from D365 BC
def getToken():
	clientId = ""
	tenantId = ""
	clientSecret = ""
	grantType = "client_credentials"
	callbackUrl = "https://businesscentral.dynamics.com/OAuthLanding.htm"
	scope = "https://api.businesscentral.dynamics.com/.default"
	tokenEndpoint = "https://login.microsoftonline.com/" + tenantId + "/oauth2/v2.0/token"

	requestData = {
		"client_id": clientId,
		"callback_url": callbackUrl,
		"client_secret": clientSecret,
		"scope": scope,
		"grant_type": grantType
	}

	token = requests.get(tokenEndpoint, data = requestData)
	return(token.json().get("access_token"))

# get http headers
def getHeaders(doGetToken):
	global token

	if doGetToken:
		token = getToken()

	headers = {
		"Content-Type": "application/json",
		"Authorization": "Bearer " + token
	}
	return(headers)

# get wmm entry http body
def getWmmEntryBody(metric, value):
	httpBody = json.dumps({
		"itemNo": "",
		"location": "",
		"bin": "",
		"metric": metric,
		"value": value
	})
	return(httpBody)

# get sensor status http body
def getSensorStatusBody(serial, status):
	httpBody = json.dumps({
		"serialNo": serial,
		"status": status
	})
	return(httpBody)

# initial auth token
token = getToken()
# API endpoint
wmmEntryApiUrl = ""
wmmSensorStatusApiUrl = ""
requestType = "POST"

try:
	while True:
		result = instance.read()
		if result.is_valid():
			# Console outputs
			print("+-----------------------------------------------------------+")
			print("> Last valid input: " + str(datetime.datetime.now()))
			print("> Temperature: %-3.1f C" % result.temperature)
			print("> Humidity: %-3.1f %%" % result.humidity)
			print("+-----------------------------------------------------------+")

			# API call for Temperature measurement
			tempHttpBody = getWmmEntryBody("COLD", result.temperature)
			httpResponse = requests.request(requestType, wmmEntryApiUrl, headers=getHeaders(False), data=tempHttpBody)
			# auth token is invalid
			if httpResponse.status_code == 401:
				httpResponse = requests.request(requestType, wmmEntryApiUrl, headers=getHeaders(True), data=tempHttpBody)
			print("> Temperature API call response status code: " + str(httpResponse.status_code))

			# API call for Humidity measurement
			humidityHttpBody = getWmmEntryBody("HUMID", result.humidity)
			httpResponse = requests.request(requestType, wmmEntryApiUrl, headers=getHeaders(False), data=humidityHttpBody)
			# auth token is invalid
			if httpResponse.status_code == 401:
				httpResponse = requests.request(requestType, wmmEntryApiUrl, headers=getHeaders(True), data=humidityHttpBody)
			print("> Humidity API call response status code: " + str(httpResponse.status_code))
		else:
			if result.is_missing_data():
				sensorStatusHttpBody = getSensorStatusBody("KY096559634985", 'Missing data')
			if result.is_crc_error():
				sensorStatusHttpBody = getSensorStatusBody("KY096559634985", 'CRC error')
			httpResponse = requests.request(requestType, wmmSensorStatusApiUrl, headers=getHeaders(True), data=sensorStatusHttpBody)
		time.sleep(30)

except KeyboardInterrupt:
    print("Cleanup")
    GPIO.cleanup()