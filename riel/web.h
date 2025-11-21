#include <WiFi.h>
#include <HTTPClient.h>
#include <ArduinoJson.h>

struct Service {
	char* ssid;
	char* pass;
	String postURI = "enc_status",
		request    = "",
		response   = "";
	short times    = 10;
	byte id        = 0, 
		 code      = 0;
	double pos     = 0.0;

	void init(byte ID);
	void verify();
};
