import cympy
import pandas as pd
import locale
from collections import defaultdict, deque

#Default numeric formatting "to system, in Canada it uses a dot as decimal separator (I think)
locale.setlocale(locale.LC_NUMERIC, '')
# Deactivate the GUI refresh
cympy.app.ActivateRefresh(False)
# Open study file, Galveston is the study file for the python challenge
cympy.study.Open("C:/Users/E0835974/OneDrive - Eaton/RD/ICA_Optimization/Test_ICA.sxst")
#Get the Network
network = cympy.study.ListNetworks()[0]


# Define the absolute percent difference thresholds
LOADING_VAR = 5.0       # 5% threshold for ICLoading
VOLT_VAR = 2.0          # 2% threshold for ICVoltVariation
MAX_VAR = 3.0           # 3% threshold for ICMax


#Gets power flow into a node, through a regulator. Need to define and run a load flow before
#this function is called, otherwise it will return 0 for all values.
def get_power_flow_regulator(regulator):
 
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

#Given any node, find downstream first regulator/transformers. Go upstream and do the same (ignoring the path
# that was traversed upwards from). Recursively do this until we reach the root node (Feeder)
def map_regulators_to_node(start_node, node_regulator_dict, verbose=True, final_result_set_verbose = True):
    """
    Maps all relevant regulators to the given start_node.
    This includes:
    - Immediate downstream regulators from the node.
    - First regulators found in sibling branches of all upstream nodes.
    
    Parameters:
    - start_node: the node to map regulators for
    - node_regulator_dict: dictionary to store the result
    - verbose: if True, prints detailed traversal logs
    """
    node_regulator_dict[start_node] = set()
    collected_regulators = set()

    def find_first_downstream_regulators(node, exclude_node=None):
        regulators = set()
        iterator = cympy.study.NetworkIterator(node.ID)

        if verbose:
            print(f"\n  Exploring downstream from node {node.ID} (excluding {exclude_node.ID if exclude_node else 'None'})")

        while iterator.Next():
            downstream_node = iterator.GetNode()
            if exclude_node and downstream_node.ID == exclude_node.ID:
                if verbose:
                    print(f"    Skipping excluded node {exclude_node.ID}")
                iterator.Skip()
                continue

            devices = iterator.GetDevices()
            for device in devices:
                if device.DeviceType in [0, 1]:  # Regulator or Transformer
                    if verbose:
                        print(f"    Found regulator {device.DeviceNumber} on edge {node.ID} → {downstream_node.ID}")
                    regulators.add(device)
                    iterator.Skip()
                    break

        return regulators

    if verbose:
        print(f"\nStarting regulator mapping for node {start_node.ID}")

    immediate = find_first_downstream_regulators(start_node)
    collected_regulators.update(immediate)

    if verbose:
        print(f"  Immediate downstream regulators for {start_node.ID}: {[r.DeviceNumber for r in immediate]}")

    upstream_iterator = cympy.study.NetworkIterator(start_node.ID, cympy.enums.IterationOption.Upstream)

    while upstream_iterator.Next():
        parent = upstream_iterator.GetNode()
        child = upstream_iterator.GetFromNode()

        if verbose:
            print(f"\nMoving upstream to parent node {parent.ID} from {child.ID}")

        sibling_regulators = find_first_downstream_regulators(parent, exclude_node=child)
        collected_regulators.update(sibling_regulators)

        if verbose:
            print(f"  Regulators found in sibling branches of {parent.ID}: {[r.DeviceNumber for r in sibling_regulators]}")

        upstream_iterator = cympy.study.NetworkIterator(parent.ID, cympy.enums.IterationOption.Upstream)

    node_regulator_dict[start_node] = collected_regulators
    if final_result_set_verbose:
        print(f"\n✅ Final regulator set for node {start_node.ID}: {[r.DeviceNumber for r in collected_regulators]}")

#given a regulator, replace it with a spot load EQ model that will be used for power flow calculations
def replace_regulators_with_spot_loads(regulator, network, regulator_dict):
    # Get the downstream node of the regulator
    child = cympy.study.GetNode(
        cympy.study.QueryInfoDevice("ToNodeId", regulator.DeviceNumber, regulator.DeviceType)
    )

    # Disconnect the upstream section from the child node
    upstream_iterator = cympy.study.NetworkIterator(child.ID, cympy.enums.IterationOption.Upstream)
    upstream_iterator.Next()
    up_section = upstream_iterator.GetSection()
    cympy.study.Disconnect(up_section.ID, child.ID)
    
    #New node created from disconnecting regulator (downstream of regulator)
    new_node = cympy.study.GetNode(cympy.study.QueryInfoDevice("ToNodeId", regulator.DeviceNumber, regulator.DeviceType))

    # Add a new spot load section at the child node
    new_spotload_section = regulator.DeviceNumber + "_NEW_SPOTLOAD_SEC"
    new_spotload_device_number = regulator.DeviceNumber + "_NEW_SPOTLOAD_NUM"

    cympy.study.AddSection(
        new_spotload_section,
        network,
        new_spotload_device_number,
        cympy.enums.DeviceType.SpotLoad,
        new_node.ID
    )
    
    spot_load = cympy.study.GetDevice(new_spotload_device_number, cympy.enums.DeviceType.SpotLoad)

   # Get kW and kVAR values of power flow through regulator as they dictate what the EQ spot load power consumption will be
    kw, kvar, _ = regulator_dict[regulator]
    
    for phase in range(len(kw)):
        base_path = f"CustomerLoads[0].CustomerLoadModels[0].CustomerLoadValues[{phase}].LoadValue"
        spot_load.SetValue(kw[phase], f"{base_path}.KW")
        spot_load.SetValue(kvar[phase], f"{base_path}.KVAR")
        
    #Update regulator_dict entry for cur regulator to keep track of original child node of cur regulator
    regulator_dict[regulator] = (kw, kvar, child)
        
#Given a regulator, reconnect it to the original child node that was disconnected when the regulator was replaced with a spot load EQ model.
#this fails if called on a regulator that was never EQ'd with a spot load model, in which case the child node will be None
def replace_spot_loads_with_regulators(regulator, regulator_dict):
    #Get the section created with the spot load EQ model for the current regulator
    new_spotload_section = regulator.DeviceNumber + "_NEW_SPOTLOAD_SEC"
  
    # Get the original child node of the regulator
    _, _, child = regulator_dict[regulator]
    #If child not instantiated for current spot load, it means it was never EQ'd, so we cannot replace it with a regulator
    try:
        if not child:
            raise ValueError("Child node is None, cannot replace spot load with regulator as it was never EQ'd")
        
        # Delete the spot load section that was created, if the section doesn't exist, a Value Error will be raised which means
        #The regulator also did not have a spot load EQ model, so we cannot remove it
        cympy.study.DeleteSection(new_spotload_section)
    except ValueError as e:
        return
    
    new_node = cympy.study.GetNode(cympy.study.QueryInfoDevice("ToNodeId", regulator.DeviceNumber, regulator.DeviceType))
    #reconnect regulator as originally connected
    cympy.study.Connect(new_node.ID, child.ID)

           
#Given a node, using node_regulator_dict, replace all regulators with spot loads EQ models, run ICA and record the result for that specific node.
#Put the circuit back to its original state by replacing the spot loads with regulators EQ models.
def ICA_Optimize(node, df):           
    """
    Replaces all regulators in the node with spot loads, runs ICA, and then restores the original state.
    
    Parameters:
    - node: the node to process
    """
    # Get all regulators for the node
    regulators = node_regulator_dict[node]
    
    # Replace each regulator with a spot load
    for regulator in regulators:
        replace_regulators_with_spot_loads(regulator, network, regulator_dict)
    
    # Run ICA (assuming this is a placeholder for actual ICA logic)
    ICA_Simulation.Run()
    print(f"Running ICA for node {node.ID} with replaced spot loads...")
        
    # Update only the row corresponding to this node
    df.loc[node.ID, 'ICLoading (optimized)'] = cympy.study.QueryInfoNode("ICLoading", node.ID)
    df.loc[node.ID, 'ICVoltVariation (optimized)'] = cympy.study.QueryInfoNode("ICVoltVariation", node.ID)
    df.loc[node.ID, 'ICMax (optimized)'] = cympy.study.QueryInfoNode("ICMax", node.ID)

    # Restore original state by replacing spot loads back with regulators
    for regulator in regulators:
        replace_spot_loads_with_regulators(regulator, regulator_dict)
    
    print(f"Restored original state for node {node.ID}")
   
# Function to compute absolute percent difference between true ICA values and optimized network retrieved ones
def is_close_enough(true_val, opt_val, threshold):
    true_val = float(true_val)
    opt_val = float(opt_val)
    if true_val == 0.0:  # Avoid division by zero
        return opt_val == 0.0
    return abs((opt_val - true_val) / true_val) * 100 <= threshold
        
#List all nodes and get the feeder node
all_nodes = cympy.study.ListNodes()
#Run ICA once to load values on nodes
ICA_Simulation = cympy.sim.IntegrationCapacityAnalysis()
ICA_Simulation.Run()
# Create the DataFrame with node.ID as the index
df = pd.DataFrame(index=[node.ID for node in all_nodes])
# Add the ICLoading (true) values as a column
df['ICLoading (true)'] = [cympy.study.QueryInfoNode("ICLoading", node.ID) for node in all_nodes]
# Add the ICVoltVariation (true)  values as columns
df['ICVoltVariation (true)'] = [cympy.study.QueryInfoNode("ICVoltVariation", node.ID) for node in all_nodes]
# Add the ICMax (true) values as columns
df['ICMax (true)'] = [cympy.study.QueryInfoNode("ICMax", node.ID) for node in all_nodes]
#Uncomment to see original state of nodes for current network (if ICA ran correctly and ground truth values initialized correctly)
#print(df)

# #Relate all regulators to their equivalent EQ model for power flow, key is regulator DeviceNumber,
#value is tuple of two lists ( [KWA, KWB, KWC], [KVARA, KVARB, KVARC] )
regulator_dict = defaultdict(tuple)
#keys are nodes, values is list of regulators that need to be replaced with spot loads EQ model
node_regulator_dict = defaultdict(set)

#For all device in the network, get power flow of regulators/transformers
for device in cympy.study.ListDevices():
    if device.DeviceType in [0, 1]:
        #two list of three values for each phases
        triple_kw, triple_kvar = get_power_flow_regulator(device)
        regulator_dict[device] = (triple_kw, triple_kvar, None)

 
#Get list of regulators to replace for all nodes for ICA optimization
for node in all_nodes:
    map_regulators_to_node(node, node_regulator_dict, verbose = False, final_result_set_verbose = False)
    #Testing new algorithm on N419 (node at index 0)
    ICA_Optimize(node, df)
    
    
# Apply the comparison row-wise
df['IsCloseEnough'] = df.apply(
    lambda row: (
        is_close_enough(row['ICLoading (true)'], row['ICLoading (optimized)'], LOADING_VAR) and
        is_close_enough(row['ICVoltVariation (true)'], row['ICVoltVariation (optimized)'], VOLT_VAR) and
        is_close_enough(row['ICMax (true)'], row['ICMax (optimized)'], MAX_VAR)
    ),
    axis=1
)

    

#Printing df to see if values of ground truth and after running ICA on optimized network appear correctly
print(df.dropna())

