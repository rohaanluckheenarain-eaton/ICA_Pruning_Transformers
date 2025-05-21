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
#dictionary that relates a regulator to its downstream node (where we disconnect to attach new spot load)
regulator_dict = defaultdict()


#Gets power flow into a node, t
def get_power_flow_regulator(regulator):
    kw_keywords = ["KWA", "KWB", "KWC"]
    kvar_keywords = ["KVARA", "KVARB", "KVARC"]
    
    kw = []
    kvar = []
    regulator_id = regulator.DeviceNumber
    
    for kw_keyword in kw_keywords:
        kw.append(cympy.study.QueryInfoDevice(kw_keyword, regulator_id, cympy.enums.DeviceType.Regulator))
        
    for kvar_keyword in kvar_keywords:
        kvar.append(cympy.study.QueryInfoDevice(kvar_keyword, regulator_id, cympy.enums.DeviceType.Regulator))
        
    return kw, kvar

#given a root node, this goes downstreams and returns a 2d array where each index is a cluster of nodes that share the same bfs level
#assuming levels are delimited by number of regulator crossed from the root node. Each level basically are all cousins
def cluster_nodes_by_regulators(feeder_node, regulator_dict):
  
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
                cur_node, cur_devices = cur_iterator.GetNode(), cur_iterator.GetDevices()
            
                           
                regulator = False
                #Device Type of 0 or 1 is transformer or regulator, respectively
                for device in cur_devices:
                    #keep cur node as new root delimited by this regulator/transformer
                    #TODO only do this for transformer when conditions are fulfilled (within tap range it can regulate)
                    if device.DeviceType in [0, 1]:
                        
                        #Get power flow into regulator
                        kw, kvar = get_power_flow_regulator(device)
                        
                        
                        #Upstream node of regulator
                        cur_parent = cur_iterator.GetFromNode()
                        queue.append(cur_node)
                        #Get all downstream adjacent section from child node of regulator
                        next_sections = cur_iterator.ListNextSections()
                        
                        
                        cur_iterator.Skip()
                        regulator = True
                        #Tuple of (parent, child, next_sections, and power flow in regulator)
                        regulator_dict[device] = (cur_parent, cur_node, next_sections, kw, kvar)

                        #cympy.study.Disconnect(cur_section, cur_node)                  
                        break
                
                #if not a regulator, not a transformer, and not a valid transformer, add to cur cluster as non delimited
                if not regulator and cur_node:
                        clusters[-1].append(cur_node)
                              
    return clusters





#get power flow into regulator (for spot load EQ replacement). Then initiate iterator to the regulator,
#travel once upstream to get upstream node and once downstream to get downstream node. (assuming that a node delimits the regulator
#in both direction. TODO This fails if multiple sections) 



#Give a regulator object to this function
def replace_regulators_with_spot_loads(regulator, network):
   
    #Get adjacent nodes to regulator being replaced
    parent, child, next_sections, kw, kvar = regulator_dict[regulator]
      
    for section in next_sections:
        cympy.study.Disconnect(section.ID, child.ID)
        
    new_spotload_section = regulator.DeviceNumber + "_NEW_SPOTLOAD_SEC"
    new_spotload_device_number = regulator.DeviceNumber + "_NEW_SPOTLOAD_NUM"
        
    #Add spot load section from child node to parent node
    cympy.study.AddSection(new_spotload_section, network, new_spotload_device_number, cympy.enums.DeviceType.SpotLoad, child.ID)
    
    #Reference to Spot Load that was just placed
    spot_load = cympy.study.GetDevice(new_spotload_device_number, cympy.enums.DeviceType.SpotLoad)
    #Set the spot load to be a PQ model with appropriate kw, kvar per phase
    
    for phase in range(len(kw)):
        # Set the spot load to be a PQ model with appropriate kw, kvar per phase
        base_path = f"CustomerLoads[0].CustomerLoadModels[0].CustomerLoadValues[{phase}].LoadValue"
        
        #print(base_path)
        
        
        spot_load.SetValue(kw[phase], f"{base_path}.KW")
        spot_load.SetValue(kvar[phase], f"{base_path}.KVAR")
        


def replace_spot_loads_with_regulators(regulator, network):
    #Identify SpotLoad to Remove
    new_spotload_section = regulator.DeviceNumber + "_NEW_SPOTLOAD_SEC"
    #Delete section with new spotload
    cympy.study.DeleteSection(new_spotload_section)
    
    
    for section in regulator_dict[regulator][2]:
        #Get the section that was disconnected
        cur_section = cympy.study.GetSection(section.ID)
        #Get the node that was disconnected
        cur_node = cympy.study.GetNode(cur_section.GetToNode())
        
        #Reconnect the section to the node
        cympy.study.Connect(cur_section, cur_node)
    
    
    
    
    #TODO
    pass




            
#build clusters and dict where keys are all regulators and values are (parent, child) node of the regulator
#use dict to attach spot load to child node and disconnect everything else from it
clusters = cluster_nodes_by_regulators(feeder_node, regulator_dict)
        
#Regulator_dict is built by BFS on the network, its keys are all regulators.
network = cympy.study.ListNetworks()[0]
for regulator in regulator_dict.keys():
    replace_regulators_with_spot_loads(regulator, network)
    
    
    replace_spot_loads_with_regulators(regulator, network)
    break






###PSEUDO CODE

"""
For every node, 
"""
   
    

    
