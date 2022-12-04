import numpy as np
import pm4py
from pm4py.objects.log.obj import EventLog
from pm4py.objects.petri_net.obj import PetriNet, Marking
from pm4py.objects.petri_net.utils import petri_utils
from sortedcontainers import SortedSet


class G2_AlphaAlgorithm:

    def __init__(self, numberStartTokens, numberEndTokens):
        """
        Initialises a G2_AlphaAlgorithm; an instance of G2_AlphaAlgorithm contains the following instance variables:
        ---
        :param numberStartTokens: number of start tokens for the petri net
        :param numberEndTokens: number of end tokens for the petri net
        :var numberStartTokens
        :var numberEndTokens
        :var dataLog: event log, as defined by the pm4py library
        :var net: a PetriNet, as defined by the pm4py library
        :var startEvents: a list of all start events in the data
        :var endEvents: a list of all end events in the data
        :var start: start place of the petri net, as defined by the pm4py library
        :var end: end place of the petri net, as defined by the pm4py library
        :var initialMarking: initial marking for visualising the petri net, as defined by the pm4py library
        :var finalMarking: final marking for visualising the petri net, as defined by the pm4py library
        :var activityToTransition: python dictionary with format (key: index number, value: transition)
        :var activityIsKey: python dictionary with format (key: activity, value: index)
        :var indexIsKey: python dictionary with format (key: index, value: activity)
        :var footprintMatrix: footprint matrix of the data
        :var setDict: python dictionary with format (key: set, value: arc anchor point)
        """
        self.numberStartTokens = numberStartTokens
        self.numberEndTokens = numberEndTokens
        self.dataLog = EventLog()
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
        """
        Takes the data and returns a petri net by way of the alpha algorithm
        ---
        :param log: event log to run the algorithm on 
        :returns: petri net, inital marking, final marking
        """
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
        """
        Sets the provided event log
        ---
        :params: log: event log
        :returns: NONE
        """
        self.dataLog = log
        
    def __addTransitions(self):
        """
        Extracts all distinct transitions from the event log, casts them to the appropriate format and adds 
        them to the petri net. Also sorts the transitions and assigns each to an index, storing them in the 
        dictionary activityToTransition
        ---
        :params: NONE
        :returns: NONE
        """
        log_activities = pm4py.get_event_attribute_values(self.dataLog, "concept:name")
        index = 0
        for key in sorted(log_activities.keys()):
            transition = PetriNet.Transition(key, key)
            self.activityToTransition[index] = transition
            self.net.transitions.add(transition)
            index += 1
            
    def __getStartAndEndEvents(self):
        """
        Extracts all start events from the data, casts them into the transition format and adds them to 
        the instance variable startEvents list. Does the same with all end events.
        ---
        :params: NONE
        :returns: NONE
        """
        startEventsFromLog = pm4py.get_start_activities(self.dataLog).keys()
        for key in startEventsFromLog:
            self.startEvents.append(PetriNet.Transition(key, key))
        endEventsFromLog = pm4py.get_end_activities(self.dataLog).keys()
        for key in endEventsFromLog:
            self.endEvents.append(PetriNet.Transition(key, key))

    def __addPlacesAndArcs(self):
        """
        Calls methods to create the footprint matrix and add places and arcs (/flows) to the petri net
        ---
        :params: NONE
        :returns: NONE
        """ 
        self.__createFootPrintMatrixDicts()
        self.__createFootPrintMatrix()
        self.__getPlacesAndArcs()
   
    def __createFootPrintMatrixDicts(self):
        """
        Extracts all distinct events from the log and creates the dictionaries activityIsKey and indexIsKey
        ---
        :params: NONE 
        :returns: NONE
        """
        log_activities = list(pm4py.get_event_attribute_values(self.dataLog, "concept:name").keys())
        log_activities.sort()
        index = 0
        for event in log_activities:
            self.activityIsKey[event] = index
            self.indexIsKey[index] = event
            index+=1
     
    def __createFootPrintMatrix(self):
        """
        Creates the footprint matrix for the data
        ---
        :params: NONE
        :returns: NONE
        """ 
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
        """
        Calls all methods necessary to extract Places and Arcs(/Flows) and add them to the petri net
        ---
        :params: NONE
        :returns: NONE
        """
        self.__fillSetDict()
        self.__findSuperSets()
        self.__removeSelfloops()
        self.__createPlacesAndArcs()
        self.__getStartAndEndPlacesAndArcs()
        
    def __isChoiceRelation(self, activityANr, activityBNr):
        """
        Checks if two activities (=parameters of the footprint matrix) are independent in the sense of the alpha algorithm
        ---
        :params: NONE
        :returns: true if independent, false if not independent
        """
        return self.footprintMatrix[activityANr][activityBNr] == 0
            
    def __fillSetDict(self):
        """
        Calculates all possible sets offered by the footprint matrix and stores them in setDict
        ---
        :params: NONE
        :returns: NONE
        """
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
                    # if there is an activity of one relation that is not in a "choice" relation with an activity
                    # of the other relation, the two relations cannot be merged
                    for baseActivityNr in baseRelation:
                        if containsDependentPair:
                            break
                        for compareActivityNr in mergeRelation:
                            if not self.__isChoiceRelation(baseActivityNr, compareActivityNr):
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
        """
        Removes all sets that are not supersets from setDict
        ---
        :params: NONE
        :returns: NONE
        """
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
    
    def __removeSelfloops(self):
        """
        If a relation contains an activity that has a selfloop (e.g. A>A direct succession in trace log),
        that activity is no more in a "choice" relation with itself, therefore the relation must be discarded
        from the places
        ---
        :params: NONE 
        :returns: NONE
        """
        loopRelations = set()
        for relation in self.setDict.keys():
            for activityNr in relation:
                if not self.__isChoiceRelation(activityNr, activityNr):
                    loopRelations.add(relation)
                    break
        for loopRelation in loopRelations:
            self.setDict.pop(loopRelation)
            
    def __createPlacesAndArcs(self):
        """
        Creates Places and Arcs from the entries in setDict, adds the Places to the petri net
        ---
        :params: NONE 
        :returns: NONE
        """
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
        """
        Takes entry from set dict where the anchor activity is at the start and turns it into a Place
        ---
        :param place: entry from setDict 
        :returns: a Place
        """
        placeString = "({'" + self.getIndexIsKey()[int(place[0])] + "'}, {'"
        for task in range(1, len(place)):
            if (task != 1):
                placeString += "', '"
            placeString += self.getIndexIsKey()[int(place[task])]
        placeString += "'})"
        newPlace = self.net.Place(placeString)
        return newPlace

    def __makeEndPlace(self, place):
        """
        Takes entry from set dict where the anchor activity is at the end and turns it into a Place
        ---
        :param place: entry from setDict 
        :returns: a Place
        """ 
        placeString = "({'"
        for task in range(0, (len(place)-1)):
            if (task != 0):
                placeString += "', '"
            placeString += self.getIndexIsKey()[int(place[task])]    
        placeString += "'}, {'" + self.getIndexIsKey()[int(place[-1])] + "'})" 
        newPlace = self.net.Place(placeString)
        return newPlace    

    def __addArcsStart(self, placeString, Place):
        """
        For a given setDict entry where the anchor activity is at the start, creates the corresponding arcs and 
        adds them to the petri net
        ---
        :param placeString: a setDict entry
        :param Place: a Place representing the setDict entry
        :returns: NONE
        """ 
        petri_utils.add_arc_from_to(self.getActivityToTransition()[int(placeString[0])], Place, self.net)
        for task in range(1, len(placeString)):
             petri_utils.add_arc_from_to(Place, self.getActivityToTransition()[int(placeString[task])], self.net)

    def __addArcsEnd(self, placeString, Place):
        """
        For a given setDict entry where the anchor activity is at the end, creates the corresponding arcs and adds them to the petri net
        ---
        :param placeString: a setDict entry
        :param Place: a Place representing the setDict entry
        :returns: NONE
        """ 
        for task in range(0, (len(placeString)-1)):
                petri_utils.add_arc_from_to(self.getActivityToTransition()[int(placeString[task])], Place, self.net) 
        petri_utils.add_arc_from_to(Place, self.getActivityToTransition()[int(placeString[len(placeString)-1])], self.net)

    def __getStartAndEndPlacesAndArcs(self):
        """
        Adds the start Place to the petri net and calls method to create and add the corresponding arcs. Does the same for all the end Place.
        ---
        :params: NONE 
        :returns: NONE
        """  
        self.net.places.add(self.start)
        self.__addStartArcs()
        self.net.places.add(self.end)  
        self.__addEndArcs()

    def __addStartArcs(self):
        """
        For all start events, adds arcs to the start Place to the petri net
        ---
        :params: NONE
        :returns: NONE
        """
        for startEvent in self.startEvents:
            for transition in self.activityToTransition.values():
                if (str(startEvent) == str(transition)):
                    petri_utils.add_arc_from_to(self.start, transition, self.net)             

    def __addEndArcs(self):
        """
        For all end events, adds arcs to the end Place to the petri net
        ---
        :params: NONE
        :returns: NONE
        """  
        for endEvent in self.endEvents:
            for transition in self.activityToTransition.values():
                if (str(endEvent) == str(transition)):
                    petri_utils.add_arc_from_to(transition, self.end, self.net)

    def __initialiseMarkings(self):
        """
        Adds inital and final Markings to the petri net
        ---
        :params: NONE 
        :returns: NONE
        """ 
        self.initialMarking[self.start] = self.numberStartTokens
        self.finalMarking[self.end] = self.numberEndTokens
    

    
    
    
    
    
    
    
    
    
    
    

