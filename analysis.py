import matplotlib.pyplot as plt
import pandas as pd
import pm4py
from pm4py.objects.log.obj import EventLog
from typing import Callable

from analysisdata import AnalysisResult, AlgoData


class Analysis:
    
    def __init__(self, file_path: str, is_status_logging_on: bool = True):
        self.log: EventLog = pm4py.read_xes(file_path)
        self.algorithms: dict[str, AlgoData] = {}
        self.is_status_logging_on: bool = is_status_logging_on
        
    def add_algo_function(self, algo_name: str, algo_function: Callable) -> None:
        self.algorithms[algo_name] = AlgoData(algo_function)
        
    def add_algo_functions(self, algo_functions_with_names: list[(str, Callable)]) -> None:
        self.algorithms.update({name: AlgoData(function) for name, function in algo_functions_with_names})
        
    def run(self, stability_test_runs: int = 1) -> None:
        run_times = stability_test_runs if stability_test_runs > 1 else 1
        for name, algo in self.algorithms.items():  
            for i in range(run_times): 
                run_status_text = f"{i + 1}/{run_times}" if run_times > 1 else ""
                print(f"Running algo {name} {run_status_text}")
                self.__log_status("- Building Petri net...")
                net, init_marking, final_marking = algo.function(self.log)
                self.__log_status("- Petri net completed")
                self.__log_status("- Calculating replay fitness...")
                fitness = pm4py.fitness_token_based_replay(self.log, net, init_marking, final_marking)
                average_trace_fitness = fitness["average_trace_fitness"]
                log_fitness = fitness["log_fitness"]
                self.__log_status("- Replay fitness calculated")
                algo.add_result(net, init_marking, final_marking, average_trace_fitness, log_fitness)
                self.__log_status(f"- Algo finished\n")
            
    def get_simple_results(self) -> dict[str, AnalysisResult]:
        return {name: algo_data.results[0] for name, algo_data in self.algorithms.items()}
    
    def create_comparison_table(self) -> pd.DataFrame:
        comparison_dict = {name: [results.average_trace_fitness, results.log_fitness] for name, results in self.get_simple_results().items()}
        return pd.DataFrame(comparison_dict, index=["Avg trace fitness", "Log fitness"])
    
    def show_petri_nets(self) -> None:
        for name, result in self.get_simple_results().items():
            print(f"Algo {name}")
            pm4py.view_petri_net(result.net, result.init_marking, result.final_marking)
        
    def show_stability_graphs(self) -> None:
        stability_tested_algorithms = {name: algo_data for name, algo_data in self.algorithms.items() if len(algo_data.results) > 1}
        if len(stability_tested_algorithms) < 1:
            print("Not enough data (number of reruns too low) for stability evaluation")
            return
        figure, axis = plt.subplots(len(stability_tested_algorithms), 2)
        figure.set_size_inches(9, len(stability_tested_algorithms) * 2.4)
        for i, algo in enumerate(stability_tested_algorithms.items()):
            name, algo_data = algo
            current_axis = axis[i] if len(stability_tested_algorithms) > 1 else axis
            self.__create_stability_graph(current_axis[0], algo_data, "average_trace_fitness", 
                                          f"{name} avg. \ntrace fitness stability")
            self.__create_stability_graph(current_axis[1], algo_data, "log_fitness", 
                                          f"{name} log \ntrace fitness stability")
        plt.subplots_adjust(left=None, bottom=None, right=None, top=None, wspace=0.5, hspace=1)
        plt.show()
        
    def export_pnml(self, file_path: str, algo_name: str) -> None:
        result = self.get_simple_results().get(algo_name)
        pm4py.write_pnml(result.net, result.init_marking, result.final_marking, file_path)
        self.__log_status(f"Export into {file_path} successful")
    
    def __create_stability_graph(self, axis: plt.Axes, algo_data: AlgoData, value_attr_name: str, title: str) -> None:
        fitness_values = [result.__getattribute__(value_attr_name) for result in algo_data.results]
        axis.set_title(title)
        axis.set_xlabel("Number of reruns")
        axis.set_ylabel("Value")
        axis.plot(fitness_values, marker="o", linestyle="none")
        
    def __log_status(self, message: str) -> None:
        if self.is_status_logging_on:
            print(message)
        