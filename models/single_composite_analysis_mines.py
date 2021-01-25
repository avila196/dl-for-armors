import numpy as np
import matplotlib.pyplot as plt
import xlsxwriter as xlsx
import time
from wave_prop_analysis_V2 import Layer, Wave, simulate_waves

'''
Function that returns the middle column values of a given matrix
depending on its parity
'''
def middleH(matrix):
    if len(matrix[0])%2 == 0:
        i = matrix.shape[1]//2
        return [(row[i]) for row in matrix]
    else:
        i = matrix.shape[1]/2-0.5
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
    #Input file to read
    #filename = input("Enter input file name: ")
    filename = "./data/mines.txt"
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
                    #Now, we use the values to construct a layer.
                    #Given that some are optional, we construct a dictionary with
                    #optional parameters (stress failures and relevant property)
                    optional = {}
                    for op in parts[5:]:
                        #Check it's ending char to add it to dictionary
                        if op[-1] == "r":
                            optional["rel"] = op[:-1] == "1"
                        elif op[-1] == "c":
                            optional["sf_c"] = float(op[:-1])
                        else:
                            optional["sf_t"] = float(op[:-1])
                    #Then, we create the layer
                    layer = Layer(float(parts[0]), float(parts[1]), float(parts[2]),
                                  float(parts[3]), float(parts[4]), **optional)
                    all_layers.append(layer)    
                    done = True
                i += 1
        #Now, we set the parameters for the simulation
        finalt = -1
        step = -1
        while finalt == -1:
            if not lines[i].startswith("#"): #consider line that doesn't start with #
                parts = lines[i].strip().split(",")
                #First, we check if 'r' or 't'
                if parts[0] == 't':
                    finalt = float(parts[1])
                else:
                    #We find the time according to the num of reverberations of the first wave needed
                    one_rev = 0
                    for l in all_layers[1:]: #loop avoiding first layer (projectile)
                        one_rev += (l.h/l.c)*2
                    finalt = round(one_rev*float(parts[1]),2)
                    print(finalt)
                step = 0.01 if len(parts) == 2 else float(parts[2])
            i += 1
        
        #ADJUST LAYERS TO SIMPLIFICATIONS GIVEN ON PAPER
        all_layers[0].rho = 8000
        all_layers[0].c = 5
        all_layers[0].rhoc = 40
        all_layers[1].rho = 1600
        all_layers[1].c = 2.5
        all_layers[1].rhoc = 4
        all_layers[2].rho = 3667
        all_layers[2].c = 9
        all_layers[2].rhoc = 33
        all_layers[2].h = 18
        
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
                        wave = Wave(all_layers[layer_num-1].numnod-1,
                                    all_layers[layer_num-1].numnod,0,sigma)
                    else:
                        wave = Wave(0,all_layers[layer_num-1].numnod,1,sigma)
                    all_layers[layer_num-1].waves.append(wave)
                    done = True
                i += 1
                
    #SIMULATION
    #Call for simulate_waves
    start_time = time.time()
    print("--- SIMULATION IN PROGRESS ---")
    simulate_waves(all_layers, t, step) 
    print("--- DONE! Took {:f} seconds ---".format((time.time() - start_time)))
    
    #Export data to Excel file
    #saveData = input('First, do you want to save all data on an xlsx file? [Y/N] ')
    saveData = "n"
    if saveData.upper() == 'Y':
        fileName = input('Enter the name of the file to save (without extension): ')
        fileName += '.xlsx'
        workbook = xlsx.Workbook(fileName)
        for sheetNum, layToSave in enumerate(all_layers):
            allCols = all_layers[sheetNum].hval()
            parts = (len(allCols) // 16000) + 1
            lastIndex = 0
            for i in range(parts): #For loop in case a single sheet exceeds 16000 columns
                if i == parts-1:
                    endIndex = len(allCols)
                else:
                    endIndex = lastIndex+16000
                cols = allCols[lastIndex:endIndex]
                sheet = workbook.add_worksheet()
                if parts > 1:
                    sheet.name = 'Layer ' + str(sheetNum+1) + '.' + str(i+1)
                else:
                    sheet.name = 'Layer ' + str(sheetNum+1)
                sheet.write_string(0,1,'h (mm)')
                sheet.write_string(1,0,'t (micro-s)')
                sheet.write_row(0,2,cols)
                sheet.write_column(2,0,t)
                for rowNum, data in enumerate(all_layers[sheetNum].mesh,2):
                    sheet.write_row(rowNum,2,data[lastIndex:endIndex])
                lastIndex += 16000 #Update to the next part (if any)
        workbook.close()
    
    #PLOTS
    #plots -> type[time vs stress at certain thickness, thickness vs stres at certain time] input from the user
    stop = False 
    while(not stop):
        try: 
            typ = int(input('What type of plot? [t vs sigma -> 1, h vs sigma -> 2,'+
                            't vs sigma_max (tension) -> 3, t vs sigma_max (compression) -> 4, '+
                            'all_layers vs sigma (all times) -> 5]: '))
            if typ == 1:
                layToPlot = int(input('What layer you want to plot? (Number, 1 left, ...) '))
                dist = input('Beginning, middle or last part of the layer? [B,M,L] ')
                if(dist == 'B'):
                    values = column(all_layers[layToPlot-1].mesh,0)
                elif dist == 'M':
                    values = middleH(all_layers[layToPlot-1].mesh)
                elif dist == 'L':
                    values = column(all_layers[layToPlot-1].mesh,all_layers[layToPlot-1].numnod-1)
                else:
                    dist = 'M'
                    values = middleH(all_layers[layToPlot-1].mesh)
                    print('Invalid choice, by default the middle will be plot')
                lab = dist + ' part of the layer '+str(layToPlot)
                plt.plot(t,values, 'k',label=lab)
                plt.axis([0,t[t.size-1],np.amin(values)-0.1,np.amax(values)+0.1])
                plt.xlabel('Time (microseconds)')
                plt.ylabel('Stress (Pa)')
                plt.legend(loc='best')
                plt.grid(True)
                plt.show()
            elif typ == 2:
                layToPlot = int(input('What layer you want to plot? (Number, 1 left, ...) '))
                quest = 'What time (max 3 decimal places) you want to plot? [0 - '+str(t[t.size-1])+'] '
                plot_time = float(input(quest))
                if plot_time >= 0 and plot_time <= finalt:
                    values = all_layers[layToPlot-1].mesh[np.where(abs(t - plot_time) < 0.0001)[0][0]]
                    vec = np.linspace(0.,all_layers[layToPlot-1].h,len(values))
                    lab = 'Layer '+str(layToPlot)+' at '+str(plot_time) +' ms'
                    plt.plot(vec,values, 'k',label=lab)
                    plt.axis([0,all_layers[layToPlot-1].h,np.amin(values)-0.1,np.amax(values)+0.1])
                    plt.xlabel('Thickness (mm)')
                    plt.ylabel('Stress (Pa)')
                    plt.legend(loc='best')
                    plt.grid(True)
                    plt.show()
                else:
                    print('Invalid time')
            elif typ == 3:
                layToPlot = int(input('What layer you want to plot? (Number, 1 left, ...) '))
                maxValues = np.zeros(t.size)
                for i in range(t.size):
                    vec = all_layers[layToPlot-1].mesh[i][2:-2]
                    vec = [l for l in vec if l >= 0] or [0]
                    maxValues[i] = max(vec)
                lab = 'Max stress (T) on layer '+str(layToPlot)
                plt.plot(t,maxValues, 'k',label=lab)
                plt.axis([0,t[t.size-1], min(maxValues)-0.1, max(maxValues)+0.1])
                plt.xlabel('Time (microseconds)')
                plt.ylabel('Stress (Pa)')
                plt.legend(loc='best')
                plt.grid(True)
                plt.show()
            elif typ == 4:
                layToPlot = int(input('What layer you want to plot? (Number, 1 left, ...) '))
                maxValues = np.zeros(t.size)
                for i in range(t.size):
                    vec = all_layers[layToPlot-1].mesh[i][2:-2]
                    vec = [l for l in vec if l <= 0] or [0]
                    maxValues[i] = min(vec)
                lab = 'Max stress (C) on layer '+str(layToPlot)
                plt.plot(t,maxValues, 'k',label=lab)
                plt.axis([0,t[t.size-1], min(maxValues)-0.1, max(maxValues)+0.1])
                plt.xlabel('Time (microseconds)')
                plt.ylabel('Stress (Pa)')
                plt.legend(loc='best')
                plt.grid(True)
                plt.show()
            elif typ == 5:
                #Construct one array with all sigma values for all layers (excluding
                #the projectile) for all times
                total_h = sum([layer.h for layer in all_layers[1:]])
                total_nodes = sum([layer.numnod for layer in all_layers[1:]])
                vec = np.linspace(0, total_h, total_nodes)
                min_sigma = 0
                max_sigma = 0
                #Loop through all times
                for i in range(t.size):
                    #Get vector of sigma for all layers and update min or max if needed
                    sigma = np.array([])
                    for layer in all_layers[1:]:
                        sigma = np.append(sigma, layer.mesh[i])
                    if np.amin(sigma) < min_sigma:
                        min_sigma = np.amin(sigma)
                    if np.amax(sigma) > max_sigma:
                        max_sigma = np.amax(sigma)
                    plt.plot(vec, sigma, color="b")
                #Plot vertical lines where the layers are separated and boundaries
                #for the failure stresses
                x = 0
                for i,layer in enumerate(all_layers[1:]):
                    plt.axvline(x)
                    plt.axhline(layer.sf*1000000, xmin=x/total_h, xmax=(x+layer.h)/total_h, color="r")
                    plt.axhline(-layer.sf*1000000, xmin=x/total_h, xmax=(x+layer.h)/total_h, color="r")
                    x += layer.h
                plt.xlabel('Thickness (mm)')
                plt.ylabel('Stress (Pa)')
                plt.axis([0, total_h, -max([abs(min_sigma),abs(max_sigma)]), max([abs(min_sigma),abs(max_sigma)])])
                plt.title("Total Width vs Sigma (all times)")
                plt.show()
            elif typ == 6:
                #Construct one array with all sigma values for all layers (excluding
                #the projectile) for all times
                total_h = sum([layer.h for layer in all_layers[1:]])
                total_nodes = sum([layer.numnod for layer in all_layers[1:]])
                vec = np.linspace(0, total_h, total_nodes)
                min_sigma = 0
                max_sigma = 0
                #Loop through all times
                for i in range(t.size):
                    #Get vector of sigma for all layers and update min or max if needed
                    sigma = np.array([])
                    for layer in all_layers[1:]:
                        sigma = np.append(sigma, layer.mesh[i])
                    if np.amin(sigma) < min_sigma:
                        min_sigma = np.amin(sigma)
                    if np.amax(sigma) > max_sigma:
                        max_sigma = np.amax(sigma)
                    plt.plot(vec, sigma, color="b")
                #Plot vertical lines where the layers are separated and boundaries
                #for the failure stresses
                x = 0
                for i,layer in enumerate(all_layers[1:]):
                    plt.axvline(x)
                    plt.axhline(layer.sf*1000000, xmin=x/total_h, xmax=(x+layer.h)/total_h, color="r")
                    plt.axhline(-layer.sf*1000000, xmin=x/total_h, xmax=(x+layer.h)/total_h, color="r")
                    x += layer.h
                plt.xlabel('Thickness (mm)')
                plt.ylabel('Stress (Pa)')
                plt.axis([0, total_h, min_sigma-0.1,max_sigma+0.1])
                plt.title("Total Width vs Sigma (all times)")
                plt.show()
            else:
                print('Invalid type of plot')
        except Exception as e:
            print(e)
        finally:
            stop = input('Do you want to make another plot? [Y/N] ').upper() == 'N'

'''
Main block to call for simulate
'''
if __name__ == "__main__":
    simulate()