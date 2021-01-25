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
    #INIT PARAMETERS FOR THE COMPOSITE
    FLOOR = Layer(1.52,1.21*10**9,891.3544,1,20*10**3)
    EMPAQUE= Layer(3.5,1.3954*10**6,25.9586,1,1)
    CASCARA = Layer(1,10.4092*10**6,1075.29144,120*10**2,100)
    PULPA = Layer(33,4.2741*10**6,1258.856,1.4*10**3,200)
    REC_SEM = Layer(2,410.9037*10**6,1049.96,1.4*10**3,200)
    SEM = Layer(12.5,36.9569*10**6,1064.85,1.4*10**3,200)
    all_layers = [FLOOR,EMPAQUE,CASCARA,PULPA,REC_SEM,SEM]
    
    rhoc=np.zeros(len(all_layers))
    for i in range(len(all_layers)):
        rhoc[i] = all_layers[i].rhoc
    
    #SIMULATION
    sigma_i= -4.4294/(1/rhoc[0]+1/rhoc[1])
    step = 0.01
    finalt = 150
    t = np.arange(0, finalt, step)
    
    #First, discretize each layer given finalt and step of time
    for layer in all_layers:
        layer.nodes(step,t.size)
        
    #Now, set initial conditions - V1
    wave1 = Wave(all_layers[0].numnod-1,all_layers[0].numnod,0,sigma_i)
    all_layers[0].waves.append(wave1)
    wave2 = Wave(0,all_layers[1].numnod,1,sigma_i)
    all_layers[1].waves.append(wave2)
    
    #Call for simulate_waves
    start_time = time.time()
    simulate_waves(all_layers, t, step) 
    print("--- {:f} seconds ---".format((time.time() - start_time)))
    
    
    #Export data to Excel file
    saveData = input('First, do you want to save all data on an xlsx file? [Y/N] ')
    if saveData == 'Y' or saveData == 'y':
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
            typ = int(input('What type of plot? [t vs sigma -> 1, h vs sigma -> 2, t vs sigma_max (tension) -> 3, t vs sigma_max (compression) -> 4] '))
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
                plt.ylabel('Stress (GPa)')
                plt.legend(loc='upper left')
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
                    plt.ylabel('Stress (GPa)')
                    plt.legend(loc='upper left')
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
                plt.ylabel('Stress (GPa)')
                plt.legend(loc='upper left')
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
                plt.ylabel('Stress (GPa)')
                plt.legend(loc='upper left')
                plt.grid(True)
                plt.show()
            else:
                print('Invalid type of plot')
        except Exception as e:
            print(e)
        finally:
            stop = input('Do you want to make another plot? [Y/N] ') == 'N'

'''
Main block to call for simulate
'''
if __name__ == "__main__":
    simulate()