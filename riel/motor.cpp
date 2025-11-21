#include "config.h"
#include "motor.h"

extern Motor motor;

void Motor::init()
{
	pinMode(M_PWM, OUTPUT);
	pinMode(M_CW, OUTPUT);
	pinMode(M_CCW, OUTPUT);
}

void Motor::set(double VOLTS)
{
	short PWM = VOLTS * 256 / 12;
	Serial.println(PWM);
	if (PWM != 0)
	{
		digitalWrite(M_CW,  PWM > 0 ? HIGH :  LOW);
		digitalWrite(M_CCW, PWM < 0 ? HIGH :  LOW);
		analogWrite(M_PWM,  PWM > 0 ? PWM  : -PWM);
	}
	else
	{
		digitalWrite(M_CW,  LOW);
		digitalWrite(M_CCW, LOW);
		analogWrite(M_PWM,  0);
	}
}
