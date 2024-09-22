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

# get http body
def getBody(metric, value):
	httpBody = json.dumps({
		"itemNo": "",
		"location": "",
		"bin": "",
		"metric": metric,
		"value": value
	})
	return(httpBody)

# initial auth token
token = getToken()
# API endpoint
apiUrl = ""
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
			tempHttpBody = getBody("COLD", result.temperature)
			httpResponse = requests.request(requestType, apiUrl, headers=getHeaders(False), data=tempHttpBody)
			# auth token is invalid
			if httpResponse.status_code == 401:
				httpResponse = requests.request(requestType, apiUrl, headers=getHeaders(True), data=tempHttpBody)
			print("> Temperature API call response status code: " + str(httpResponse.status_code))

			# API call for Humidity measurement
			humidityHttpBody = getBody("HUMID", result.humidity)
			httpResponse = requests.request(requestType, apiUrl, headers=getHeaders(False), data=humidityHttpBody)
			# auth token is invalid
			if httpResponse.status_code == 401:
				httpResponse = requests.request(requestType, apiUrl, headers=getHeaders(True), data=humidityHttpBody)
			print("> Humidity API call response status code: " + str(httpResponse.status_code))
		time.sleep(30)

except KeyboardInterrupt:
    print("Cleanup")
    GPIO.cleanup()