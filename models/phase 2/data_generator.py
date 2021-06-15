import numpy as np
import csv
from wave_prop_analysis_V2 import Layer, Wave, simulate_waves

'''
Function that checks if a given composite should be considered or not.
The function labels the answers for future training and testing
'''
def label(all_layers):
    #We loop through relevant layers to find the state of them
    for i,layer in enumerate(all_layers[1:],1):
        if layer.rel:
            #We first find both max tension and compression stresses for all
            #times and all points
            max_tension = np.amax(layer.hydStress()) if np.amax(layer.hydStress()) > 0 else 0
            max_compression = np.amin(layer.hydStress()) if np.amin(layer.hydStress()) < 0 else 0
            #Finally, we check if stresses are above the failure stress
            if abs(max_compression) > layer.sf_c or abs(max_tension) > layer.sf_t:
                return 0 #meaning it can't be considered
    #If the loop ends without any returns, it means the layer satisfies the conditions
    #on the relevant layers to be considered
    return 1
    
'''
Function that simulates the wave propagation for some generated data
and exports data to a CSV file
'''
def simulate():
    #Start setting the parameters for all layers to consider
    data_layer1 = [(334e9,3690), (344e9,3970), (260e9,3590)]
    h2 = np.linspace(0.5,0.7,9)
    h4 = np.linspace(0.5,0.7,9)
    h6 = np.linspace(0.5,0.7,9)
    h9 = np.linspace(1,3,3)
    #List to hold all the parameters to export to CSV
    rows = []
    i = 1
    for data in data_layer1:
        for h2i in h2:
            for h4i in h4:
                for h6i in h6:
                    for h9i in h9:
                        print(i, end="")
                        #Create composite
                        L0 = Layer(18.75,14e9,11340,1,0.431,sf_t=2069e6,rel=False)
                        L1 = Layer(5,data[0],data[1],1,0.22,sf_t=742e6,rel=False)
                        L2 = Layer(h2i,2.02e9,1104,1,0.3,sf_t=89e6,rel=False)
                        L3 = Layer(4,70e9,2210,1,0.22,sf_t=48e6,rel=False)
                        L4 = Layer(h4i,2.02e9,1104,1,0.3,sf_t=89e6,rel=False)
                        L5 = Layer(4,70e9,2210,1,0.22,sf_t=48e6,rel=False)
                        L6 = Layer(h6i,2.02e9,1104,1,0.3,sf_t=89e6,rel=False)
                        L7 = Layer(4,70e9,2210,1,0.22,sf_t=48e6,rel=False)
                        L8 = Layer(0.6,2.02e9,1104,1,0.3,sf_t=89e6,rel=False)
                        L9 = Layer(h9i,2.586e9,1200,1,0.33,sf_t=104e6,rel=True)
                        all_layers = [L0,L1,L2,L3,L4,L5,L6,L7,L8,L9]
                        #Set num of nodes given the time for simulation
                        step = 0.01
                        one_rev = 0
                        for l in all_layers[1:]: #loop avoiding first layer (projectile)
                            one_rev += (l.h/l.c)*2
                        finalt = round(one_rev,2)
                        #Using the parameters, we create the time vector and we discretize each layer
                        t = np.arange(0, finalt, step)
                        for layer in all_layers:
                            layer.nodes(step,t.size)
                        #Set initial wave conditions
                        sigma = -100/(1/all_layers[0].rhoc+1/all_layers[1].rhoc)
                        wave = Wave(all_layers[0].numnod-1,all_layers[0].numnod,0,sigma)
                        all_layers[0].waves.append(wave)
                        wave = Wave(0,all_layers[1].numnod,1,sigma)
                        all_layers[1].waves.append(wave)
                        #SIMULATE WAVES
                        simulate_waves(all_layers, t, step)
                        #Label the result of simulation
                        y = label(all_layers)
                        #Append result into rows list (x inputs and y label)
                        row = []
                        for layer in all_layers:
                            row.extend([layer.h, layer.E, layer.rho, layer.sf_t, layer.sf_c, (1 if layer.rel else 0)])
                        row.append(y)
                        rows.append(row)
                        i += 1

    #Once all composites were simulated, we export the data to a CSV file
    #First, we create the header
    header = []
    for i, layer in enumerate(all_layers):
        l = "L"+str(i)
        header.extend([l+"_h",l+"_E",l+"_rho",l+"_sf_t",l+"_sf_c",l+"_rel"])
    header.append("Y")
    #Now, we use the csv module to export the file
    with open('all_data_2.csv', 'w', newline='') as file:
        writer = csv.writer(file)
        writer.writerow(header)
        writer.writerows(rows)

'''
Main block to call for simulate
'''
if __name__ == "__main__":
    simulate()