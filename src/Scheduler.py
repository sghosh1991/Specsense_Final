import thread,time
from SpecsenseDB_ops import SpecsenseDB

CONTROLLER_ASK_DATA_TOPIC = "controller/"

class Scheduler():
    
    algorithm = ""
    controller = ""
    
    dbHandle = SpecsenseDB("localhost","27017")
    
    
    def __init__(self,controller,ip,port):
        
        print "in scheduler init" + str((controller.__class__))
        self.controller = controller
        print ip,port
        #self.dbHandle = SpecsenseDB(ip,port)
        
        
        
        
    
    def getScheduler(self,algorithm):
        
        if (algorithm in "Roundrobin"): 
            return Roundrobin(5,self.controller)
        else:
            return AyonSched(50)
    
    def manual_schedule(self):
        pass
    



class Roundrobin(Scheduler):
    
    periodicity = 60
    
    def __init__(self,periodicity,controller):
        
        self.periodicity = periodicity
        self.controller = controller
    
     
    def manual_schedule(self):

        #Continiously manual_schedule the active UE after every 1 minute
        print "Started roundrobin" + str(self.periodicity)
        print self.dbHandle.__class__
        print self.dbHandle.conn
        
	while 1:
             
        #get a list of online UE
            online_UE_list = self.dbHandle.fetch_online_ue()
             
            for ue in online_UE_list:
                self.controller.publish(CONTROLLER_ASK_DATA_TOPIC + ue, "dummyData", 2, False)
            print online_UE_list
            time.sleep(60)
            

class AyonSched(Scheduler):
    
    periodicity = 50
    
    def __init__(self,periodicity):
        
        self.periodicity = periodicity
    
    def manual_schedule(self):
        
        print "In ayon sched" + str(self.periodicity)\
        
        


if __name__ == "__main__":
    
    s = Scheduler("Roundroin")
    
    s.algorithm.manual_schedule()
