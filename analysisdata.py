from pm4py.objects.petri_net.obj import PetriNet, Marking
from typing import Callable


class AnalysisResult:
    
    def __init__(self, net: PetriNet, init_marking: Marking, final_marking: Marking,
                 avg_trace_fitness: float, log_fitness: float):
        self.net: PetriNet = net
        self.init_marking: Marking = init_marking
        self.final_marking: Marking = final_marking
        self.average_trace_fitness: float = avg_trace_fitness
        self.log_fitness: float = log_fitness


class AlgoData:
    
    def __init__(self, algo_function: Callable):
        self.function: Callable = algo_function
        self.results: list[AnalysisResult] = []
        
    def add_result(self, net: PetriNet, init_marking: Marking, final_marking: Marking, 
                   avg_trace_fitness: float, log_fitness: float) -> None:
        self.results.append(AnalysisResult(net, init_marking, final_marking, avg_trace_fitness, log_fitness))