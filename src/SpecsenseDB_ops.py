#This file is for managing the MongoDB operations

import pymongo
import datetime

class SpecsenseDB():
    
    conn = "" #would contain the mongodb connenction handle
    specsenseDB = "" #handle to the Specsense database
    measurementsTable = "" #handle to the measurements table
    registeredUETable = "" #handle to the registered ue table
    
    
    
    def __init__(self,ip,port):
        
        print "In specsense db init"
        self.conn = pymongo.MongoClient('mongodb://' + str(ip) + ":" + str(port) + "/")
        self.specsenseDB = self.conn.SpecsenseDB
        self.registeredUETable = self.specsenseDB.Registered_UE
        self.measurementsTable = self.specsenseDB.UE_Measurements
        
        
    
    def insert_in_measurements(self,dataToInsert):
        
        #This function inserts data in the measurements table
        # @param dataToInsert => the python dict containing all data
        
        #Tag this data with the current time stamp. This is the last time the UE scanned
        format = "%Y-%m-%d %H:%M:%S"
        last_scanned = datetime.datetime.today().strftime(format)
        dataToInsert['last_scanned'] = last_scanned
        
        try:
            
            self.measurementsTable.insert_one(dataToInsert)
        
        except Exception as e:
            print("Error Occured " + str(type(e)) + ":" + str(e))
    
    def insert_in_registered_ue(self,dataToInsert):
        
        #This function inserts data in the registered ue table
        # @param dataToInsert => the python dict containning all data
        try:
            
            self.registeredUETable.update_one({'_id':dataToInsert['mac']} , { '$set' : { 'ue_model': dataToInsert['ue_model'], 'ue_status': 'ONLINE', 'ue_battery_power': dataToInsert['ue_battery_power'], 'loc' : dataToInsert['loc']}, '$inc': {'count':1}}, True)
            
            #self.registeredUETable.insert_one(dataToInsert)
        
        except Exception as e:
            print("Error Occured in insert" + str(type(e)) + ":" + str(e))
    
    def update_registered_ue(self,mac):
        
        try:
            
            #updates the registered ue table to change the state of the ue to offline
            self.registeredUETable.update({'_id':mac},{ '$set' :{'ue_status':"OFFLINE"}})
           
        except Exception as e:
            print("Error Occured in update" + str(type(e)) + ":" + str(e))
        
    

    def update_online_ue_location(self,dataToInsert):
        try:
            
	    self.registeredUETable.update({'_id':dataToInsert['mac']}, { '$set' : {'loc': dataToInsert['loc'], 'ue_battery_power': dataToInsert['ue_battery_power']}})
        
        except Exception as e:
            
            print "Got exception in doing periodic update to db" + str(e)
        
    
    
    def fetch_online_ue(self):
        
        online_ues = []
        
        try:
            for online_ue in self.registeredUETable.find({"ue_status":"ONLINE"}):
                
                online_ues.append(online_ue['_id'])
        
        except Exception as e:
            
            print "Got exception in reading from DB"
            
        return online_ues       
               
