## Business Intelligence II 2022WS - Exercise 2 - Group 2

Implementation of the α-miner algorithm.
α-miner is a process mining algorithm that aims to discover a process model from an event log. It uses a heuristic approach to discover a Petri net by analyzing the relationships between events and finding the most frequent patterns in the log, such as the causal dependencies and the ordering of events.

### How to start the application

1. Run `pipenv install`
2. Paste data set file into the folder `logs/`
3. Run `jupyter notebook`
4. Edit path to data set in the programs `comparison_stability.ipynb` or `comparison.ipynb`
   (default path: `logs/BPI_Challenge_2012.xes.gz` and `logs/BPI_Challenge_2017.xes.gz`)
5. Start the programs in notebook

### Runtime

-   comparison.ipynb: approx. **10 minutes**
-   comparison_stability.ipynb: approx. **1 minute**

(tested on i7-1165G7)
