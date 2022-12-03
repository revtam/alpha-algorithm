import graphviz
import numpy as np
import pm4py
from pm4py.objects.log.obj import EventLog
from pm4py.objects.petri_net.obj import PetriNet, Marking
from pm4py.objects.petri_net.utils import petri_utils
from sortedcontainers import SortedSet


class G2_AlphaAlgorithm:

    def __init__(self, numberStartTokens, numberEndTokens):
        self.numberStartTokens = numberStartTokens
        self.numberEndTokens = numberEndTokens
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
        self.setDict: dict[tuple[int], str] = dict()

    def createPetriNet(self, log: EventLog):
        self.net = PetriNet("Petri Net of G2 Alpha")
        self.__init__(self.numberStartTokens, self.numberEndTokens)
        self.__createLog(log)
        self.__getStartAndEndEvents()
        self.__addTransitions()
        self.__addPlacesAndArcs()
        self.__initialiseMarkings()
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
            
    def __createLog(self, log: EventLog):
        self.dataLog = log
        
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
        self.footprintMatrix = np.zeros((len(self.activityIsKey), len(self.activityIsKey)))
        for variant in variants.keys():
            for eventnr in range(len(variant)):
                activityNr = self.activityIsKey[variant[eventnr]]
                if eventnr != (len(variant)-1):
                    followingActivityNr = self.activityIsKey[variant[eventnr+1]]
                    if self.footprintMatrix[activityNr][followingActivityNr] != 2:
                        if (self.footprintMatrix[activityNr][followingActivityNr] == -1):
                            self.footprintMatrix[activityNr][followingActivityNr] = 2 
                        else:
                            self.footprintMatrix[activityNr][followingActivityNr] = 1 
                if eventnr != 0:
                    previousActivityNr = self.activityIsKey[variant[eventnr-1]]
                    if self.footprintMatrix[activityNr][previousActivityNr] != 2:
                        if (self.footprintMatrix[activityNr][previousActivityNr] == 1):
                            self.footprintMatrix[activityNr][previousActivityNr] = 2 
                        else:
                            self.footprintMatrix[activityNr][previousActivityNr] = -1
            
    def __getPlacesAndArcs(self):
        self.__fillSetDict()
        self.__findSuperSets()
        self.__createPlacesAndArcs()
        self.__getStartAndEndPlacesAndArcs()
        
    def __isParallel(self, taskANumber, taskBNumber):
        matrixValue = self.footprintMatrix[taskANumber][taskBNumber]
        if (matrixValue != 2):
            return True
        return False
        
    def __fillSetDict(self):
        startRelations = self.__createRelationDict(1, "start")
        endRelations = self.__createRelationDict(-1, "end")
        self.setDict.update(startRelations)
        self.setDict.update(endRelations)           
 
    def __createRelationDict(self, matrixValue: int, relationRole: str):
        relationDict = dict()        
        for rowNr in range(len(self.footprintMatrix)):
            baseRelationSet: set[tuple] = set()
            for columnNr in range(len(self.footprintMatrix)): 
                if self.footprintMatrix[rowNr][columnNr] == matrixValue:
                    baseRelationSet.add((columnNr,))
            # in each row, get all possible relations of activity numbers in the column that are eligible for combination
            rowRelationSet = self.__buildOrderedRelationSet(baseRelationSet)
            for orderedRelation in rowRelationSet:
                # depending on the role of the relation, append the row (activity) number to the beginning or to the end of the relation
                if relationRole == "start":
                    fromActivities = (rowNr,)
                    toActivities = orderedRelation
                else:
                    fromActivities = orderedRelation
                    toActivities = (rowNr,)
                relationKey = fromActivities + toActivities
                relationDict[relationKey] = relationRole
        return relationDict
    
    def __buildOrderedRelationSet(self, baseRelationSet: set[tuple[int]]) -> set[tuple[int]]:
            baseRelationList = list(baseRelationSet)
            createdRelationSet: set[tuple[int]] = set()        
            # try to merge every relation of the base relationset with every other relation in the set
            for i, baseRelation in enumerate(baseRelationList):
                for mergeRelation in baseRelationList[(i + 1):]:
                    containsDependentPair = False
                    # check every two relations if they can be merged;
                    # if there is an activity of one relation that is in a parallel relation to an activity
                    # of the other relation, the two relations cannot be merged
                    for baseActivityNr in baseRelation:
                        if containsDependentPair:
                            break
                        for compareActivityNr in mergeRelation:
                            if not self.__isParallel(baseActivityNr, compareActivityNr):
                                containsDependentPair = True
                                break
                    if not containsDependentPair:
                        mergedSet = SortedSet(baseRelation + mergeRelation)
                        createdRelationSet.add(tuple(mergedSet))
            if len(createdRelationSet):
                # if new relations were created by merging, try to merge those as well in a recursive manner
                extendedRelationSet = self.__buildOrderedRelationSet(createdRelationSet)
                extendedRelationSet.update(baseRelationSet)
                return extendedRelationSet
            return set(baseRelationList)
    
    def __findSuperSets(self):
        subsetKeys = []
        for relation in self.setDict.keys():
            if len(relation) > 2:
                for relation2 in self.setDict.keys():
                    if (relation == relation2):
                        continue
                    if set(relation).issuperset(set(relation2)):
                        subsetKeys.append(relation2)            
        for relation in set(subsetKeys):
            self.setDict.pop(relation)
            
    def __createPlacesAndArcs(self):
        for place, value in self.getSetDict().items():
            if (value == "start"):
                newPlace = self.__makeStartPlace(place)
                self.net.places.add(newPlace)
                self.__addArcsStart(place, newPlace)
            elif (value == "end"):
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

    def __initialiseMarkings(self):
        self.initialMarking[self.start] = self.numberStartTokens
        self.finalMarking[self.end] = self.numberEndTokens
    

    
    
    
    
    
    
    
    
    
    
    

