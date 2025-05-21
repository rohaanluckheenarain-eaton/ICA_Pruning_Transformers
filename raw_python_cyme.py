import cympy
import locale
from collections import defaultdict, deque


#Set and Define Load Flow to run it to get initial values (these will determine what power flows in each node/section
# to make our PQ model equivalent at any regulators)

load_flow = cympy.sim.LoadFlow()
# set voltage variation, overvoltage to 103% and undervoltage to 97%, we are working with abnormal conditions being a 3% variation from initial case
load_flow.SetValue(97.0, 'ParametersConfigurations[0].LoadFlowGlobalVoltageLimits.LowVoltageLimit1') 
load_flow.SetValue(103.0, 'ParametersConfigurations[0].LoadFlowGlobalVoltageLimits.HighVoltageLimit1')
#set load flow voltage tolerance to 0.001% 
load_flow.SetValue(0.001, 'ParametersConfigurations[0].VoltageTolerance')
#set load flow maximum iterations to 60 (that is by default but good to remember)
load_flow.SetValue(60, 'ParametersConfigurations[0].MaximumIterations')
#Set P and Q scaling factors to 20% to match ICA parameters
load_flow.SetValue(20, "ParametersConfigurations[0].LoadFlowLoadScalingFactors.P")
load_flow.SetValue(20, "ParametersConfigurations[0].LoadFlowLoadScalingFactors.Q")
#Run load flow
load_flow.Run()

#List all nodes and get the feeder node
all_nodes = cympy.study.ListNodes()
feeder_node = all_nodes[0]

#given a root node, this goes downstreams and returns a 2d array where each index is a cluster of nodes that share the same bfs level
#assuming levels are delimited by number of regulator crossed from the root node. Each level basically are all cousins
def cluster_nodes_by_regulators(feeder_node):
  

    # Initialize clusters and queue
    clusters = []
    queue = deque([feeder_node])
    
    

    while queue:
        clusters.append([])

        for _ in range(len(queue)):
            cur_root_node = queue.popleft()
            clusters[-1].append(cur_root_node)

            cur_iterator = cympy.study.NetworkIterator(cur_root_node.ID)
            while cur_iterator.Next():
                cur_node, cur_section, cur_devices = cur_iterator.GetNode(), cur_iterator.GetSection(), cur_iterator.GetDevices()
                
                
                                
                regulator = False
                #Device Type of 0 or 1 is transformer or regulator, respectively
                for device in cur_devices:
                    #keep cur node as new root delimited by this regulator/transformer
                    #TODO only do this for transformer when conditions are fulfilled (within tap range it can regulate)
                    if device.DeviceType in [0, 1]:
                        queue.append(cur_node)
                        cur_iterator.Skip()
                        regulator = True
                        print(cur_section, cur_node)

                        #cympy.study.Disconnect(cur_section, cur_node)
                        
                        
                        break
                
                #if not a regulator, not a transformer, and not a valid transformer, add to cur cluster as non delimited
                if not regulator and cur_node:
                        clusters[-1].append(cur_node)
                    
                    
    return clusters

# Example usage
clusters = cluster_nodes_by_regulators(feeder_node)

#Gets power flow into a node, t
def get_power_flow_regulator(regulator_id):
    kw_keywords = ["KWA", "KWB", "KWC"]
    kvar_keywords = ["KVARA", "KVARB", "KVARC"]
    
    kw = []
    kvar = []
    
    for kw_keyword in kw_keywords:
        kw.append(cympy.study.QueryInfoDevice(kw_keyword, regulator_id, cympy.enums.DeviceType.Regulator))
        
    for kvar_keyword in kvar_keywords:
        kvar.append(cympy.study.QueryInfoDevice(kvar_keyword, regulator_id, cympy.enums.DeviceType.Regulator))
        
    return kw, kvar



    

 
#Get all regulators in the network, start at a section (regulator), iteratate downstream once, get the down 
 
 
 
def replace_regulators_with_spot_loads(node_id, regulator_id):
    pass
    


        
        
    
# for i in range(len(clusters)):
#     print(i, clusters[i])
    


# #to disconnect secondary side of regulator to put spot load
# #in this example, section is the REG and the Node is the one on the secondary side of the regulator

# cympy.study.Disconnect("SectionID", "NodeID")

# #connect a spot load to the newly secondary disconnected side of the regulator
# cympy.study.AddSection('NEW_ECG_SEC_ID', network, 'NEW_ECG_NUM', cympy.enums.DeviceType.SpotLoad, node_id, 'NEW_NODE')
         




#For every node, PQ model downstream all regulators adjacent to cur group.
#Go upstream current regulator and PQ model downstream all cousins (every sibling after going up parent)
#Recursively PQ model siblings (except parent that currently was upstreamed) until root reached.


