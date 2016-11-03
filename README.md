# RaspberryPi_FireFly_DB



========================================================
Request/response command description:
with this message you can request data from a node
and you will get sensor data as return once

in the inject node below first 3 places are ID
of the node you want data from,
fourth is the command number request/response is command 0

so message structure for FF-K12 node would be
K120


========================================================
Continous response command description:
with this message you can request data from a node
and you will get sensor data as return continuously
with interval you've written

in the inject node below first 3 places are ID
of the node you want data from,
fourth is the command number request/response is command 1

fifth is what unit of measurement you want:
    4 meaning miliseconds
    3 meaning seconds
    2 meaning minutes
    1 meaning hours

and the last 2 are the time in meaning
05 would mean 5 units of measurement

and 305 at the end would mean 5 seconds

so message structure for FF-K12 node would be
K121305
which means node K12 will respond every 5 seconds


========================================================
Turn on/off sensors command description:
with this message you can turn on/off sensors on a node

open function node set sensors ON/OFF
in which you will see described in comments which parameters you can change

NOTE here, if the value you select here specifies only humidity sensor
to be turned on, any other sensor that is currently turned on, will be turned off when
you send this command


========================================================
Kill continuous response command description:
with this message you can kill continuous response you've started 
with command 1

in the inject node below first 3 places are ID
of the node you want data from,¸
fourth is the command number kill continuous response is command 2

so message structure for FF-K12 node would be
K122


========================================================
Set outputs command description:
Open function node called "set outputs"
parameters you can change are:

node
LED1 //turns LED1 ON or OFF
LED2 //turns LED2 ON or OFF
LED3 //turns LED3 ON or OFF
p0_15 //writes value to pin p0-15
p0_27 //writes value to pin p0-27


========================================================
Set sensors ON/OFF:
/*NOTE here, if the value you select here specifies only humidity sensor
to be turned on, any other sensor that is currently turned on, will be turned off when
you send this command*/

var node = "K12";  //this is the node the command is being sent to

var lux     = 1; // set to 1 if you want sensor to be on 0 for it to be off
var Rh      = 1; // set to 1 if you want sensor to be on 0 for it to be off
var temp    = 1; // set to 1 if you want sensor to be on 0 for it to be off
var mag     = 1; // set to 1 if you want sensor to be on 0 for it to be off
var accel   = 1; // set to 1 if you want sensor to be on 0 for it to be off
var gyro    = 1; // set to 1 if you want sensor to be on 0 for it to be off

var sensors;

sensors = sensors  | (lux   << 0);
sensors = sensors  | (Rh    << 1);
sensors = sensors  | (temp  << 2);
sensors =  sensors | (mag   << 3);
sensors = sensors  | (accel << 4);
sensors = sensors  | (gyro  << 5);
sensors = sensors  | (1  << 6);

var char = String.fromCharCode(sensors);

msg.payload = "{\"cmd\":\"" + node + "4" + char + "\"}";
return msg;


========================================================
Set outputs:
var node = "K12";  //this is the node the command is being sent to
                  //if the node is called FF-K12 only write K12

var LED1    = 0; // set to 0 if you want LED1 to be on 1 for it to be off
var LED2    = 0; // set to 0 if you want LED2 to be on 1 for it to be off
var LED3    = 0; // set to 0 if you want LED3 to be on 1 for it to be off
var p0_15   = 0; // set to 1 if you want output p0_15 to be on 0 for it to be off
var p0_27   = 0; // set to 1 if you want output p0_27 to be on 0 for it to be off

var output;

output = output  | (LED1   << 0);
output = output  | (LED2   << 1);
output = output  | (LED3   << 2);
output = output  | (p0_15  << 3);
output = output  | (p0_27  << 4);
output = output  | (1  << 6);


//var char = String.fromCharCode(output + 33);
var char = String.fromCharCode(output);

msg.payload = "{\"cmd\":\"" + node + "3" + char + "\"}";
return msg;
//return char;
