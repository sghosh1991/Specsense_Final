import paho.mqtt.client as mqtt
import time
import thread,socket
from BaseHTTPServer import BaseHTTPRequestHandler,HTTPServer
from urlparse import urlparse, parse_qs
import sqlite3, dbTest
from SpecsenseDB_ops import SpecsenseDB
import datetime
import cmd
from Scheduler import Scheduler
from ConfigParser import SafeConfigParser

MANUAL_COM_LOCK = False
MANUAL_CMD = ""

PORT_NUMBER = 1234
HOST_NAME= "130.245.68.129"      

#dbConn = sqlite3.connect("/home/santosh/PycharmProjects/mysite/db.sqlite3")


(CLIENT_ID, BROKER_IP, BROKER_PORT, MONGO_IP, MONGO_PORT, ALGORITHM, PERIODICITY) = (0,1,2,3,4,5,6)


CLIENT_DISCONNECT_TOPIC = "client/+/bye"
CLIENT_CONNECT_TOPIC = "client/+/hello"
CLIENT_DATA_TOPIC = "data/+"
CLIENT_PERIODIC_UPDATE_TOPIC = "periodicUpdate/+"

CONTROLLER_ASK_DATA_TOPIC = "controller/"
CONTROLLER_ASK_DATA_CHANNEL = "channel number"
MAC = ""

class Controller():
    
    connectedClients = set()
    controller = ""
    dbHandle = SpecsenseDB("localhost","27017")
    
    def __init__(self,connect_params):
        
        #print("Starting controller")
        
        global MANUAL_COM_LOCK
        global MANUAL_CMD
        global MAC
        global CONTROLLER_ASK_DATA_CHANNEL
        global HOST_NAME
        
        
        #Set up the initial connection to the broker
        self.controller = mqtt.Client(connect_params[CLIENT_ID],clean_session=False , userdata=None)
        self.controller.max_inflight_messages_set(300)
        
        #Set up callbacks:
        #This part sets up custom callbacks for different topics
        
        #Connect the client to the broker
        self.controller.connect(connect_params[BROKER_IP], connect_params[BROKER_PORT], 60) 
        
        
        #controller connect callback
        self.controller.on_connect = self.on_connect
        
        #Client connect callback
        self.controller.subscribe(CLIENT_CONNECT_TOPIC, 0)
        self.controller.message_callback_add(CLIENT_CONNECT_TOPIC, self.on_client_connect)
        
        #Client disconnect callback
        self.controller.subscribe(CLIENT_DISCONNECT_TOPIC, 2)
        self.controller.message_callback_add(CLIENT_DISCONNECT_TOPIC, self.on_client_disconnect)
        
        #client data received callback
        self.controller.subscribe(CLIENT_DATA_TOPIC, 2)
        self.controller.message_callback_add(CLIENT_DATA_TOPIC, self.on_client_data_receive)
        
        #client periodic data received callback
        self.controller.subscribe(CLIENT_PERIODIC_UPDATE_TOPIC, 2)
        self.controller.message_callback_add(CLIENT_PERIODIC_UPDATE_TOPIC, self.on_client_periodic_data_received)

	
	
	
        
        
        self.controller.loop_start()
        
        print "Started paho client n/w loop"
        
        
        #Start the server that listens for manual command
        #thread.start_new_thread(self.CMS_server, ())

        #get a scheduler
        scheduler = Scheduler(self.controller,connect_params[MONGO_IP],connect_params[MONGO_PORT]).getScheduler("Roundrobin")
        thread.start_new_thread(scheduler.manual_schedule,())

        while 1:
            
            #pass
            #poll the command lock
            if(MANUAL_COM_LOCK):
                 
                cmd = MANUAL_CMD
                MANUAL_COM_LOCK = False 
                print "received manual command"
                self.manual_schedule()
            else:
                 #print "nothing to do"
                pass
	    time.sleep(0.05)
	    
    def CMS_server(self):
        
        try:
            #Create a web server and define the handler to manage the
            #incoming request
            #myh = myHandler() 
            server = HTTPServer((HOST_NAME, PORT_NUMBER),myHandler )
            print 'Started httpserver on port ' , PORT_NUMBER
            
            #Wait forever for incoming htto requests
            server.serve_forever()
        
        except KeyboardInterrupt:
            print '^C received, shutting down the web server'
            server.socket.close()
    
    
    
    def on_connect(self,a,b,c,d):
        #print("Successfully connected to broker")
        pass
        
    
    
    def on_publish(self):
        pass
    
    
    def on_subscribe(self):
        print("subscribe")
    
    
    def on_message(self):
        print("got message")
    
    
    def on_client_connect(self,client, userdata, message):
        print("Hi from " + message.topic)
        self.connectedClients.add(message.topic.split("/")[1])
        deviceMac = message.topic.split("/")[1]
        data = message.payload.split(",")
        #print(self.connectedClients)

	print "in connect" + str(data)
	lat = float(data[0])
	lon = float(data[1])
	deviceModel = data[2]
	battery = data[3]
        
        dataToInsert = {}
        dataToInsert['mac'] = deviceMac
        dataToInsert['ue_model'] = deviceModel
        dataToInsert['ue_state'] = "ONLINE"
	#dataToInsert['ue_gps_lat'] = float(lat)
	#dataToInsert['ue_gps_lon'] = float(lon)
	
	#GeoJSOn format lat-lon
	dataToInsert['loc'] = { "type" : "Point" , "coordinates" : [lon, lat] }
	
	dataToInsert['ue_battery_power'] = battery
        
        #dbTest.insert_in_activeue(dataToInsert)
        self.dbHandle.insert_in_registered_ue(dataToInsert)
        
        
    
    def on_client_disconnect(self,client, userdata, message):
        
        try:
            print("Bye from" + message.topic)
            self.connectedClients.remove(message.topic.split("/")[1])
            
            mac  =  message.topic.split("/")[1]
            #dataToDelete = {}
            #dataToDelete['mac'] = mac
            
            #dbTest.delete_ue(dataToDelete)
            self.dbHandle.update_registered_ue(mac)

        except Exception as KeyError:
            pass
    
    
    
    def on_client_data_receive(self,client,userdata,message):
        print("Got data: " + str(message.payload))
        measurement = self.createDataToInsert(message)
        print measurement
        #dbTest.insert_in_measurements(measurement)
        self.dbHandle.insert_in_measurements(measurement)

    
    def on_client_periodic_data_received(self,client,userdata,message):
        
        #This function will send the dummy data to the database
        print("Got data: " + str(message.payload) + " with topic " + str(message.topic))
        measurement = self.createPeriodicDataToInsert(message)
        print measurement
        #dbTest.insert_in_measurements(measurement)
        self.dbHandle.update_online_ue_location(measurement)
        
    
    def on_disconnect(self,a,b,c,d):
        print "client disconnecting"
        print a
        print b


    def manual_schedule(self):
        
        #Simple Round Robin Scheduler for connected clients
        print "scheduling manually"
#         for clients in self.connectedClients:
        print ("asking for data from " + CONTROLLER_ASK_DATA_TOPIC + MAC)
        self.controller.publish(CONTROLLER_ASK_DATA_TOPIC + MAC, CONTROLLER_ASK_DATA_CHANNEL, 2, False)
        pass
     


    def createPeriodicDataToInsert(self,message):
	
	dataToInsert = {}
	data = message.payload.split(",")
	dataToInsert['mac'] = message.topic.split("/")[1]
	#dataToInsert["ue_gps_lat"] = data[0]
	#dataToInsert["ue_gps_lon"] = data[1]
	
	#GeoJSOn format lat-lon
	dataToInsert['loc'] = { "type" : "Point" , "coordinates" : [float(data[1]), float(data[0])] }

	dataToInsert["ue_battery_power"] = data[2]
	
	return dataToInsert
	
       
    
    def createDataToInsert(self,message):
        
        format = "%Y-%m-%d %H:%M:%S"
        
        global CONTROLLER_ASK_DATA_CHANNEL
        
        mac = message.topic.split("/")[1]
        data = message.payload.split(",")
	print  data
        ue_gps_lat = float(data[0])
        ue_gps_long = float(data[1])
        ue_battery_power = data[2]
	
        avgPower = data[3]#sum([float(pow) for pow in data[3:]])/(len(data[3:]))

        ue_channel_scanned_power = float(avgPower)

	#check for wifi. if wifi replace with a random #.

	if data[4] == "WIFI":
		ue_channel_scanned = 16
	else:
        	ue_channel_scanned = data[4]
        last_scanned = datetime.datetime.today().strftime(format)
        
        measurement = {}
        
        measurement['mac'] = mac
        #measurement['ue_gps_lat'] = float(ue_gps_lat)
        #measurement['ue_gps_long'] = float(ue_gps_long)
        measurement['ue_battery_power'] = ue_battery_power
        measurement['ue_channel_scanned_power'] = ue_channel_scanned_power
        measurement['ue_channel_scanned'] = ue_channel_scanned

	#GeoJSOn format lat-lon
	measurement['loc'] = { "type" : "Point" , "coordinates" : [ue_gps_long, ue_gps_lat] }
	
        measurement['last_scanned'] = last_scanned
        
        return measurement
    
    
          
class myHandler(BaseHTTPRequestHandler):
    
    #def __init__(self):
        
    #Handler for the GET requests
    def do_GET(self,):
        
        #Controller.manual_schedule()
        global MANUAL_COM_LOCK
        global MANUAL_CMD
        global CONTROLLER_ASK_DATA_CHANNEL
        global MAC
        cmd = urlparse(self.path).query
        
        if("favicon.ico" in self.path ):
            return
        
        print cmd
       
        params = cmd.split("&")
        
        CONTROLLER_ASK_DATA_CHANNEL = params[1].split("=")[1].rstrip()
        MAC = params[0].split("=")[1].rstrip()
        MAC = MAC.replace("%3A", ":")
        
        print CONTROLLER_ASK_DATA_CHANNEL, MAC
        
        MANUAL_COM_LOCK  = True
        MANUAL_CMD = cmd
        self.send_response(200)
        self.send_header('Content-type','text/html')
        self.end_headers()
        # Send the html message
        self.wfile.write("Hello World !")
        return

if __name__ == "__main__":
    
    params = []
    
    parser = SafeConfigParser()
    parser.read('/home/wings/Project_Specsense_sourceFiles/SpecsenseController/config')
    
    #print parser.sections()
    
    brokerIP = parser.get('BROKER' , 'ip')
    brokerPort = parser.get('BROKER' , 'port')
    mongoIP = parser.get('MONGODB', 'ip')
    mongoPort = parser.get('MONGODB' , 'port')
    algorithm = parser.get('SCHEDULER', 'algorithm')
    periodiocity = parser.get('SCHEDULER' , 'periodicity')
    
    params.append("SpectreController")
    params.append(brokerIP)
    params.append(brokerPort)
    params.append(mongoIP)
    params.append(mongoPort)
    params.append(algorithm)
    params.append(periodiocity)
    
    
    print params
    
    controller = Controller(params)
    
    
        
    
    
    
    
        
    
