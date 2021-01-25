import math
import numpy as np
import copy as cp

'''
Class/Object that represents each layer on the composite
Each Layer needs the following to be initialized:
h -> width (in mm)
E -> Young Modulus (in Pa)
rho -> density (in kg/m^3)
m -> mass (in kg)
v -> Poisson's ratio
kwargs -> arguments containing:
    sf_t -> Failure tension stress (in MPa)
    sf_c -> Failure compression stress (in MPa)
    rel -> relevant for max values (true or false)
If no sf_t nor sf_c are provided, None is default
If only sf_t or sf_c is provided, it is used as both sf_t and sf_c
If rel is not provided, True is taken as default

'''
class Layer:
    #Constructor of the Layer class
    def __init__(self,h,E,rho,m,v,**kwargs):
        self.h = h   # mm
        self.E = E   # Young modulus, Pa
        self.rho = rho  # Density, kg/m^3
        self.c = math.sqrt(E/rho)/1000   # mm / micro s
        self.m = m   # Mass Layer, kg
        self.v = v   #Poisson ratio
        self.rhoc = rho*1000*self.c  # rho times c,kg/m^2s
        self.waves = [] #list of all waves
        #Also, we initialize the failure stresses and relevant property as needed
        print(kwargs)
        if "sf_t" in kwargs or "sf_c" in kwargs:
            self.sf_t = kwargs["sf_t"] if "sf_t" in kwargs else kwargs["sf_c"] 
            self.sf_c = kwargs["sf_c"] if "sf_c" in kwargs else kwargs["sf_t"]
        else:
            self.sf_t = None
            self.sf_c = None
        self.rel = kwargs["rel"] if "rel" in kwargs else True #True by default
        
    #Function that finds the needed num of nodes and creates the mesh grid
    #goven the delta time and final time
    def nodes(self,deltat,tsize):
        self.dinit = self.c * deltat
        self.numnod = round(self.h / self.dinit)+1 #+1 to make it have one node more when we have an 'exact' model
        self.h = self.numnod * self.dinit
        self.mesh = np.zeros((tsize,self.numnod))
    
    #Function that returns an array for discrete width of layer
    #For example, for h = 3 and numnod = 7, returns [0,0.5,1,1.5,2,2.5,3]
    def hval(self):
        val = np.zeros(self.numnod)
        for i in range(len(val)):
            val[i] = self.dinit * i
        return val

    #String representation (readable format) of the Layer
    def __str__(self):
        return f"{{h = {self.h} mm, E = {self.E/1000000000} GPa, rho = {self.rho} kg/m^3" \
            + f", c = {self.c} mm/micro-s}}"
    
    #String representation of the layer
    def __repr__(self):
        return self.__str__()
 
'''
Class that represents a Wave on the composite
The wave object propagates in time. The wave needs the following
to be initialized:
pos -> starting position on layer (node)
size -> max size (num of nodes) for the wave to move through
direct -> direction of wave (1 or 2 for left or right respectively)
value -> Stress value of wave
active -> boolean, represents if active or not
t -> time of creation of wave
'''
class Wave:
    #Constructor of the Wave class
    def __init__(self,pos,size,direct,value,active=True):
        self.pos = pos #position inside the respective layer, node
        self.size = size #numnod of the respective layer
        self.direct = direct #0 -> left, 1 ->right
        self.value = value
        self.active = active #False,new in that step of time; True, we consider it
         
'''
Function that calculates the coefficient of transmitted stress
'''
def csT(z1,z2):
    return 2*z2/(z1+z2)

'''
Function that calculates the coefficient of reflected stress
'''
def csR(z1,z2):
    return (z2-z1)/(z2+z1)
        
'''
Function that runs the main simulation for the elastic waves propagation
Receives the List of Layers to consider (with the initial waves on them),
the time vector for the simulation and the time step
'''
def simulate_waves(all_layers, t, step):
    #Get layers and store its length on a variable
    qty_layers = len(all_layers);
    
    #Arrays for impedances and coefficients of T and R for all layers
    rhoc=np.zeros(qty_layers)
    for i in range(qty_layers):
        rhoc[i] = all_layers[i].rhoc
            
    #Arrays to store all coefficients for both transmitted and reflected stresses
    coeffsigma_T=np.zeros((qty_layers-1)*2)
    coeffsigma_R=np.zeros((qty_layers-1)*2)
    i = 0
    while i < (rhoc.size-1)*2:
        index=math.floor(i/2)
        if i%2 == 0:
            coeffsigma_T[i]=csT(rhoc[index],rhoc[index+1])
        else:
            coeffsigma_T[i]=csT(rhoc[index+1],rhoc[index])
        i+=1
    i = 0
    while i < (rhoc.size-1)*2:
        index=math.floor(i/2)
        if i%2 == 0:
            coeffsigma_R[i]=csR(rhoc[index],rhoc[index+1])
        else:
            coeffsigma_R[i]=csR(rhoc[index+1],rhoc[index])
        i+=1
        
    #STARTS THE MAIN SIMULATION!
    #Iterations for all times
    for i in range(1,t.size,1):
        #First, we set all the inactive waves as actives
        for k in range(qty_layers):
            for j in range(len(all_layers[k].waves)):
                all_layers[k].waves[j].active = True
        #Then, we start simulating each wave of each layer
        for k, actLayer in enumerate(all_layers): #loop for each layer
            actLayer.mesh[i] = cp.deepcopy(actLayer.mesh[i-1]) #copy previous time step
            for j, actWave in enumerate(actLayer.waves):  #loop for each wave
                #We check if the wave is active (not created on current time step)
                if actWave.active:
                    #If active, we consider its direction
                    if actWave.direct == 0:
                        #This means the wave is going left
                        if actWave.pos == 0: #being in the left side
                            if k == 0: #being in the left side and being in the 1st layer
                                #Here, the wave just gets reflected entirely
                                actWave.value = -actWave.value
                                for nod in range(0,2):
                                    actLayer.mesh[i][nod] = actLayer.mesh[i][nod] + actWave.value
                            else:
                                #The wave gets reflected given its coefficient
                                refl = coeffsigma_R[2*k-1]
                                actWave.value = refl*actWave.value
                                actLayer.mesh[i-1][actWave.pos] = actLayer.mesh[i-1][actWave.pos] + actWave.value #New waves, change the stress of the previous too
                                for nod in range(0,2):
                                    actLayer.mesh[i][nod] = actLayer.mesh[i][nod] + actWave.value
                            actWave.pos += 1 #Increase position
                            actWave.direct = 1 #Change direction
                        elif actWave.pos == actWave.size-1: #wave created in the last time step, it has to change nod=last too
                            for nod in range(0,2):
                                actLayer.mesh[i][actWave.pos-nod] = actLayer.mesh[i][actWave.pos-nod] + actWave.value
                            actLayer.mesh[i-1][actWave.pos] = actLayer.mesh[i-1][actWave.pos] + actWave.value #New waves, change the stress of the previous too
                            actWave.pos-=1
                        else:
                            #For any other case, the wave just decreases its position
                            #Special case: the node is one node before the left side and not first layer
                            if actWave.pos == 1 and k != 0:
                                #If so, the wave creates a new wave for previous layer
                                trans = coeffsigma_T[2*k-1]
                                newWave = Wave(all_layers[k-1].numnod-1,all_layers[k-1].numnod,0,actWave.value*trans,False)
                                all_layers[k-1].waves.append(newWave)
                            actLayer.mesh[i][actWave.pos-1] = actLayer.mesh[i][actWave.pos-1] + actWave.value
                            actWave.pos -= 1 #Decrease position
                    else:
                        #This means the wave is going right
                        if actWave.pos == actWave.size-1: #being in the right side
                            if k==qty_layers-1: #being in the right side and being in the last layer
                                #Here, the wave just gets reflected entirely
                                actWave.value = -actWave.value
                                for nod in range(0,2):
                                    actLayer.mesh[i][actWave.pos-nod] = actLayer.mesh[i][actWave.pos-nod] + actWave.value
                            else:
                                #The wave gets reflected given its coefficient
                                refl = coeffsigma_R[2*k]
                                actWave.value = refl*actWave.value
                                actLayer.mesh[i-1][actWave.pos] = actLayer.mesh[i-1][actWave.pos] + actWave.value #New waves, change the stress of the previous too
                                for nod in range(0,2):
                                    actLayer.mesh[i][actWave.pos-nod] = actLayer.mesh[i][actWave.pos-nod] + actWave.value
                            actWave.pos -= 1 #Decrease position
                            actWave.direct = 0 #Change direction
                        elif actWave.pos == 0: #wave created in the last time step, it has to change nod=0 too
                            for nod in range(0,2):
                                actLayer.mesh[i][nod] = actLayer.mesh[i][nod] + actWave.value
                            actLayer.mesh[i-1][actWave.pos] = actLayer.mesh[i-1][actWave.pos] + actWave.value #New waves, change the stress of the previous too
                            actWave.pos+=1
                        else:
                            #For any other case, the wave just increases its position
                            #Special case: the node is one node before the right side and not last layer
                            if actWave.pos == actWave.size-2 and k != qty_layers-1:
                                #If so, the wave creates a new wave for next layer
                                trans = coeffsigma_T[2*k]
                                newWave = Wave(0,all_layers[k+1].numnod,1,actWave.value*trans,False)
                                all_layers[k+1].waves.append(newWave)
                            actLayer.mesh[i][actWave.pos+1] = actLayer.mesh[i][actWave.pos+1] + actWave.value
                            actWave.pos += 1 #Increase position
        #Finally, we combine the waves at the same position (diminish computational time)
        for k in range(qty_layers):
            restart = True
            waves = all_layers[k].waves
            while restart:
                for j in range(len(waves)):
                    found = False
                    wave1 = waves[j]
                    for l in range(len(waves)):
                        wave2 = waves[l]
                        if wave1.pos == wave2.pos and wave1.direct == wave2.direct and j != l:
                            newWave = Wave(wave1.pos,wave1.size,wave1.direct,wave1.value+wave2.value,True)
                            waves.remove(wave1)
                            waves.remove(wave2)
                            waves.append(newWave)
                            found = True
                            break
                    if found:
                        break
                    if j == len(waves)-1:
                        restart = False
                restart = False  #For layers without waves