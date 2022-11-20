import pm4py
from pm4py.objects.petri_net.obj import PetriNet, Marking
from pm4py.objects.petri_net.utils import petri_utils
import graphviz
import numpy as np

class G2_AlphaAlgorithm:

    def __init__(self):
        self.rawDataPath = ""
        self.dataLog = 0
        self.net = PetriNet()
        self.startEvents = []
        self.endEvents = []
        self.start = PetriNet.Place("start")
        self.end = PetriNet.Place("end")
        self.initialMarking = Marking()
        self.finalMarking = Marking()
        self.activityToTransition = dict()
        self.activityIsKey = dict()
        self.indexIsKey = dict()
        self.footprintMatrix = np.empty(1)
        self.setDict = dict()

    def createPetriNet(self, rawDataPath, numberStartTokens, numberEndTokens):
        self.rawDataPath = rawDataPath
        self.net = PetriNet("Petri Net of " + self.rawDataPath)
        self.__createLog()
        self.__getStartAndEndEvents()
        self.__addTransitions()
        self.__addPlacesAndArcs()
        self.__initialiseMarkings(numberStartTokens, numberEndTokens)
        print("I've run!")
        return self.net, self.initialMarking, self.finalMarking
    
    ####  GETTERS AND SETTERS  ###################################################################
    
    def getDataLog(self):
        return self.dataLog
   
    def getStartEvents(self):
        return self.startEvents
    
    def getEndEvents(self):
        return self.endEvents    
    
    def getInitialMarking(self):
        return self.initialMarking
    
    def getFinalMarking(self):
        return self.finalMarking
       
    def getFootprintMatrix(self):
        return self.footprintMatrix
    
    def getActivityToTransition(self):
        return self.activityToTransition
    
    def getActivityIsKey(self):
        return self.activityIsKey    
    
    def getIndexIsKey(self):
        return self.indexIsKey    
    
    def getSetDict(self):
        return self.setDict   
    
    ####  PRIVATE FUNCTIONS    ###################################################################
            
    def __createLog(self):
        self.dataLog = pm4py.read_xes(self.rawDataPath)
        
    def __addTransitions(self):
        log_activities = pm4py.get_event_attribute_values(self.dataLog, "concept:name")
        index = 0
        for key in sorted(log_activities.keys()):
            transition = PetriNet.Transition(key, key)
            self.activityToTransition[index] = transition
            self.net.transitions.add(transition)
            index += 1
            
    def __getStartAndEndEvents(self):
        startEventsFromLog = pm4py.get_start_activities(self.dataLog).keys()
        for key in startEventsFromLog:
            self.startEvents.append(PetriNet.Transition(key, key))
        endEventsFromLog = pm4py.get_end_activities(self.dataLog).keys()
        for key in endEventsFromLog:
            self.endEvents.append(PetriNet.Transition(key, key))

    def __addPlacesAndArcs(self):
        self.__createFootPrintMatrixDicts()
        self.__createFootPrintMatrix()
        self.__getPlacesAndArcs()
   
    def __createFootPrintMatrixDicts(self):
        log_activities = list(pm4py.get_event_attribute_values(self.dataLog, "concept:name").keys())
        log_activities.sort()
        index = 0
        for event in log_activities:
            self.activityIsKey[event] = index
            self.indexIsKey[index] = event
            index+=1
     
    def __createFootPrintMatrix(self):
        variants = pm4py.get_variants_as_tuples(self.dataLog)
        self.footprintMatrix = np.zeros((len(self.activityIsKey),len(self.activityIsKey)))
        for variant in variants:
            for eventnr in range(len(variant)):
                if eventnr != (len(variant)-1):
                    if (self.footprintMatrix[self.activityIsKey[variant[eventnr]]][self.activityIsKey[variant[eventnr+1]]] != 2):
                        if (self.footprintMatrix[self.activityIsKey[variant[eventnr]]][self.activityIsKey[variant[eventnr+1]]] == -1):
                            self.footprintMatrix[self.activityIsKey[variant[eventnr]]][self.activityIsKey[variant[eventnr+1]]] = 2 
                        else:
                            self.footprintMatrix[self.activityIsKey[variant[eventnr]]][self.activityIsKey[variant[eventnr+1]]] = 1 
                if eventnr != 0:
                    if (self.footprintMatrix[self.activityIsKey[variant[eventnr]]][self.activityIsKey[variant[eventnr-1]]] != 2):
                        if (self.footprintMatrix[self.activityIsKey[variant[eventnr]]][self.activityIsKey[variant[eventnr-1]]] == 1):
                            self.footprintMatrix[self.activityIsKey[variant[eventnr]]][self.activityIsKey[variant[eventnr-1]]] = 2 
                        else:
                            self.footprintMatrix[self.activityIsKey[variant[eventnr]]][self.activityIsKey[variant[eventnr-1]]] = -1
            
    def __getPlacesAndArcs(self):
        self.__fillSetDict()
        self.__findSuperSets()
        self.__createPlacesAndArcs()
        self.__getStartAndEndPlacesAndArcs()
        
    def __independenceCheck(self, taskANumber, taskBNumber):
        if (self.footprintMatrix[taskANumber][taskBNumber] != 2):
            return True
        else:
            return False
        
    def __fillSetDict(self):
        row = 0
        self.setDict = dict()
        for row in range(len(self.footprintMatrix)):
            column = 0
            for column in range(len(self.footprintMatrix)): 
                if (self.footprintMatrix[row][column]) == 1:
                    self.setDict[str(row) + str(column)] = "start"
                    column2 = (column + 1)
                    while column2 < len(self.footprintMatrix):
                        if (self.footprintMatrix[row][column2]) == 1:
                            if self.__independenceCheck(column, column2) == True:
                                self.setDict[str(row) + str(column) + str(column2)] = "start"
                        column2 += 1
        for column in range(len(self.footprintMatrix)):
            row = 0
            for row in range(len(self.footprintMatrix)): 
                if (self.footprintMatrix[row][column]) == 1:
                    row2 = (row + 1)
                    while row2 < len(self.footprintMatrix):
                        if (self.footprintMatrix[row2][column]) == 1:
                            if self.__independenceCheck(row, row2):
                                self.setDict[str(row) + str(row2) + str(column)] = "end"
                        row2 += 1    
    
    def __findSuperSets(self):
        keys = []
        for relation in self.setDict.keys():
            if len(relation) > 2:
                for relation2 in self.setDict.keys():
                    if (relation == relation2):
                        continue
                    if set(relation).issuperset(set(relation2)):
                        keys.append(relation2)
        for relation in set(keys):
            self.setDict.pop(relation)
    
    def __createPlacesAndArcs(self):
        for place in self.getSetDict():
            if ((self.getSetDict()[place]) == "start"):
                newPlace = self.__makeStartPlace(place)
                self.net.places.add(newPlace)
                self.__addArcsStart(place, newPlace)
            elif ((self.getSetDict()[place]) == "end"):
                newPlace = self.__makeEndPlace(place)
                self.net.places.add(newPlace)
                self.__addArcsEnd(place, newPlace)

    def __makeStartPlace(self, place):
        placeString = "({'" + self.getIndexIsKey()[int(place[0])] + "'}, {'"
        for task in range(1, len(place)):
            if (task != 1):
                placeString += "', '"
            placeString += self.getIndexIsKey()[int(place[task])]
        placeString += "'})"
        newPlace = self.net.Place(placeString)
        return newPlace

    def __makeEndPlace(self, place):
        placeString = "({'"
        for task in range(0, (len(place)-1)):
            if (task != 0):
                placeString += "', '"
            placeString += self.getIndexIsKey()[int(place[task])]    
        placeString += "'}, {'" + self.getIndexIsKey()[int(place[-1])] + "'})" 
        newPlace = self.net.Place(placeString)
        return newPlace    

    def __addArcsStart(self, placeString, Place):
        petri_utils.add_arc_from_to(self.getActivityToTransition()[int(placeString[0])], Place, self.net)
        for task in range(1, len(placeString)):
             petri_utils.add_arc_from_to(Place, self.getActivityToTransition()[int(placeString[task])], self.net)

    def __addArcsEnd(self, placeString, Place):
        for task in range(0, (len(placeString)-1)):
                petri_utils.add_arc_from_to(self.getActivityToTransition()[int(placeString[task])], Place, self.net) 
        petri_utils.add_arc_from_to(Place, self.getActivityToTransition()[int(placeString[len(placeString)-1])], self.net)

    def __getStartAndEndPlacesAndArcs(self):
        self.net.places.add(self.start)
        self.__addStartArcs()
        self.net.places.add(self.end)  
        self.__addEndArcs()

    def __addStartArcs(self):
        for startEvent in self.startEvents:
            for transition in self.activityToTransition.values():
                if (str(startEvent) == str(transition)):
                    petri_utils.add_arc_from_to(self.start, transition, self.net)             

    def __addEndArcs(self):
        for endEvent in self.endEvents:
            for transition in self.activityToTransition.values():
                if (str(endEvent) == str(transition)):
                    petri_utils.add_arc_from_to(transition, self.end, self.net)

    def __initialiseMarkings(self, numberStartTokens, numberEndTokens):
        self.initialMarking[self.start] = numberStartTokens
        self.finalMarking[self.end] = numberEndTokens
    

    
    
    
    
    
    
    
    
    
    
    

