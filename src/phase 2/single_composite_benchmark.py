import numpy as np
import time
import copy as cp
import wave_prop_analysis_V2, wave_prop_analysis_V1

'''
Function that returns the middle column values of a given matrix
depending on its parity
'''
def middleH(matrix):
    if len(matrix[0])%2 == 0:
        i = len(matrix[0])/2
        return [(row[i]) for row in matrix]
    else:
        i = len(matrix[0])/2-0.5
        return [row[int(i)] for row in matrix]

'''
Function to get a vertical cut, a point/node through time
'''
def column(matrix, i):
    return [row[int(i)] for row in matrix]

'''
Function that simulates the wave propagation on a single composite
'''
def simulate():
    #BENCHMARK SIMULATION
    #We read as many different files as needed to run a benchmark simulation
    #between the composites described on the files
    num_composites = int(input("How many composites are up to compare? "))
    filenames = []
    #Loop to ask for all filenames
    for i in range(num_composites):
        filenames.append(input("Enter file #"+str(i+1)+": "))
    #The simulation will be run for times 10, 20, 50 and 100
    #The simulation will be applied to the num of composites requested
    #The simulation will be tested using both versions of the main code
    #The simulation will be run 3 times for each time, considering a time step of 0.01
    versions = [wave_prop_analysis_V1, wave_prop_analysis_V2]
    finalts = [10, 20, 50, 100]
    step = 0.01
    n = 3
    running_times = np.zeros((len(finalts),len(filenames),len(versions),n))
    print("\n--- SIMULATION IN PROGRESS ---")
    #First loop: final times considered
    for ft, finalt in enumerate(finalts):
        print(">> Simulating finalt = "+str(finalt))
        #Second loop: both versions of simulation codes
        for v, version in enumerate(versions):
            #Third loop: files to simulate
            for f, filename in enumerate(filenames):
                #Loop through file to construct simulation
                with open(filename,"r") as file:
                    lines = file.readlines()
                    i = 0
                    #First, we read the num of layers for composite
                    qty_layers = -1
                    while qty_layers == -1:
                        if not lines[i].startswith("#"): #consider line that doesn't start with #
                            qty_layers = int(lines[i])
                        i += 1
                    #Now, we construct the layers of the composite
                    all_layers = []
                    for l in range(qty_layers):
                        done = False
                        while not done:
                            if not lines[i].startswith("#"): #consider line that doesn't start with #
                                #We first split the line by commas
                                parts = lines[i].strip().split(",")
                                #Now, we use the values to construct a layer
                                rel = True if len(parts) == 5 else parts[5] == 'true'
                                layer = version.Layer(float(parts[0]), float(parts[1]), float(parts[2]),
                                              float(parts[3]), float(parts[4]), rel)
                                all_layers.append(layer)    
                                done = True
                            i += 1
                    #Now, we set the parameters for the simulation
                    done = False
                    while not done:
                        if not lines[i].startswith("#"): #consider line that doesn't start with #
                            # --- We can skip the line, not used for benchmark
                            done = True
                        i += 1
                    #Using the parameters, we create the time vector and we discretize each layer
                    t = np.arange(0, finalt, step)
                    for layer in all_layers:
                        layer.nodes(step,t.size)
                    #Finally, we read the init conditions (init waves) to consider
                    #First, num of init waves
                    qty_waves = -1
                    while qty_waves == -1:
                        if not lines[i].startswith("#"): #consider line that doesn't start with #
                            qty_waves = int(lines[i])
                        i += 1
                    #Now, we construct the waves and add them to respective layers
                    for w in range(qty_waves):
                        done = False
                        while not done:
                            if not lines[i].startswith("#"): #consider line that doesn't start with #
                                #We first split the line by commas
                                parts = lines[i].strip().split(",")
                                #Now, we use the values to construct a wave on the respective layer
                                layer_num = int(parts[0])
                                pos = parts[1]
                                if parts[3] == "s":
                                    sigma = float(parts[2])
                                else:
                                    vel = float(parts[2])
                                    sigma = vel/(1/all_layers[0].rhoc+1/all_layers[1].rhoc)
                                if pos == "E":
                                    wave = version.Wave(all_layers[layer_num-1].numnod-1,
                                                all_layers[layer_num-1].numnod,0,sigma)
                                else:
                                    wave = version.Wave(0,all_layers[layer_num-1].numnod,1,sigma)
                                all_layers[layer_num-1].waves.append(wave)
                                done = True
                            i += 1
                #We're ready to run the simulation n times for each finalt
                for i in range(n):
                    #Run simulation and measure time
                    layers_copy = cp.deepcopy(all_layers)
                    start_time = time.time()
                    version.simulate_waves(layers_copy, t, step)
                    end_time = time.time()
                    running_times[ft][f][v][i] = (end_time-start_time)
                print("Composite #"+str(f+1)+" completed for version #"+str(v+1))
    print("--- SIMULATION COMPLETED ---\n")
    #Final printing of benchmark table!
    #Header of table
    print("-"*25+"-"*(num_composites*(13*len(versions))))
    header = "{0:25s}"
    for i in range(num_composites):
        header += "{"+str(i+1)+":"+str(13*len(versions))+"s}"
    print(header.format(*([""]+["|Composite #"+str(i+1) for i in range(num_composites)])))
    print("-"*25+"-"*(num_composites*(13*len(versions))))
    #Sub-header for the num of versions for each composite
    subheader = ""
    for i in range(len(versions)):
        subheader += "{"+str(i+1)+":13s}"
    print("{0:25s}".format("Running Time")+subheader.format(*([""]+["|V"+str(i+1) for i in range(len(versions))]))*num_composites)
    print("-"*25+"-"*(num_composites*(13*len(versions))))
    #Print each row finding the average of the running times
    for ft, finalt in enumerate(finalts):
        avgs = []
        for f in range(num_composites):
            for v in range(len(versions)):
                #Find average of current composite and version
                avgs.append(np.average(running_times[ft][f][v]))
        #Print average values on the row
        row = "{0:<25d}"
        for i in range(len(avgs)):
            row += "{"+str(i+1)+":<13.5f}"
        print(row.format(*([finalt]+avgs)))
    
'''
Main block to call for simulate
'''
if __name__ == "__main__":
    simulate()