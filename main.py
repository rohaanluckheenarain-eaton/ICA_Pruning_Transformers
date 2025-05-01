import cympy
import locale

#Default numeric formatting "to system, in Canada it uses a dot as decimal separator (I think)
locale.setlocale(locale.LC_NUMERIC, '')
# Deactivate the GUI refresh
cympy.app.ActivateRefresh(False)
# Open study file, Galveston is the study file for the python challenge
cympy.study.Open("C:/Users/E0835974/Desktop/ICA_Optimization/Test_ICA.sxst")



#start from feeder and iterate downstream



#For all nodes, if already visited node, skip
# If unvisited node, BFS from cur node. Visit all nodes until a transformer (that is within range) is reached.
#current partition represent a subset of nodes that will use the same heuristics of PQ model of transformers 
# (the same set of transformers are modelled for these nodes so only model them once)