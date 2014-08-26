from __main__ import vtk, qt, ctk, slicer
import string
import numpy
import math
import operator
import collections


class TextureGLRL:

  def __init__(self, ii, parameterMatrix, parameterMatrixCoordinates, parameterValues, grayLevels, allKeys):
    self.textureFeaturesGLRL = collections.OrderedDict()
    self.textureFeaturesGLRL["SRE"] = "numpy.mean(numeratorSRE)"
    self.textureFeaturesGLRL["LRE"] = "numpy.mean(numeratorLRE)"
    self.textureFeaturesGLRL["GLN"] = "numpy.mean(numeratorGLN)"
    self.textureFeaturesGLRL["RLN"] = "numpy.mean(numeratorRLN)"
    self.textureFeaturesGLRL["RP"] = "numpy.mean(runPercentage)"
    self.textureFeaturesGLRL["LGLRE"] = "numpy.mean(numeratorLGLRE)"
    self.textureFeaturesGLRL["HGLRE"] = "numpy.mean(numeratorHGLRE)"
    self.textureFeaturesGLRL["SRLGLE"] = "numpy.mean(numeratorSRLGLE)"
    self.textureFeaturesGLRL["SRHGLE"] = "numpy.mean(numeratorSRHGLE)"
    self.textureFeaturesGLRL["LRLGLE"] = "numpy.mean(numeratorLRLGLE)"
    self.textureFeaturesGLRL["LRHGLE"] = "numpy.mean(numeratorLRHGLE)"
    
    self.ii = ii
    self.parameterMatrix = parameterMatrix
    self.parameterMatrixCoordinates = parameterMatrixCoordinates
    self.parameterValues = parameterValues
    self.grayLevels = grayLevels
    self.allKeys = allKeys
    
          
                        


  def EvaluateFeatures(self):   
    keys = set(self.allKeys).intersection(self.textureFeaturesGLRL.keys())
    if not keys:
      return(self.textureFeaturesGLRL)
    
    
    #GLRL
    angles = 13
    maxRunLength = numpy.max(self.parameterMatrix.shape)
    
    #maximum run length in P matrix initialized to levels
    P_glrl = numpy.zeros((self.grayLevels, maxRunLength, angles))
    P_glrl = self.glrl_loop(self.ii, self.parameterMatrix, self.parameterMatrixCoordinates, angles, self.grayLevels, P_glrl)
    
    #Initialize Metrics
    sum_P = numpy.zeros(angles)
    numeratorSRE = numpy.zeros(angles)
    numeratorLRE = numpy.zeros(angles)
    
    numeratorGLN = numpy.zeros(angles)
    numeratorRLN = numpy.zeros(angles)    
    runPercentage = numpy.zeros(angles)
                     
    numeratorLGLRE = numpy.zeros(angles)
    numeratorHGLRE = numpy.zeros(angles)
          
    numeratorSRLGLE = numpy.zeros(angles)
    numeratorSRHGLE = numpy.zeros(angles)
            
    numeratorLRLGLE = numpy.zeros(angles)
    numeratorLRHGLE = numpy.zeros(angles)
             
    #Calculate Metrics  
    for theta in xrange (angles):
      P = P_glrl[:,:,theta]
      
      #For theta(0:13), Ng_indices represent appearances of any gray level, 
      #size of list is number of unique gray levels
      Ng_indices, = numpy.nonzero(P.sum(1)) 
      Ng = Ng_indices.size
      
      #For theta(0:13), Nr_indices represent appearances of a run length for any gray level, 
      #size of list is number of unique run lengths
      Nr_indices, = numpy.nonzero(P.sum(0))
      Nr = Nr_indices.size  
      
      
      #Number of total voxels in the image        
      Np = self.voxelCount(self.parameterValues) #voxel count function
      #use StatisticsLib function?
      
      #Sum of all run length occurrences in P[:,:] for angle theta
      sum_P[theta] = P.sum()
           
      #for i in xrange(Ng):
        #for j in xrange(0,Nr):
      for i in Ng_indices:  
        for j in Nr_indices:
          Pval = P[i,j]    
          
          numeratorSRE[theta] += ((Pval) / ((j+1)**2)) 
          numeratorLRE[theta] += (Pval*((j+1)**2))
          
          numeratorGLN[theta] += ((P[i,:].sum())**2)       
          numeratorRLN[theta] += ((P[:,j].sum())**2)
                     
          numeratorLGLRE[theta] += ((Pval) / ((i+1)**2))
          numeratorHGLRE[theta] += (Pval*((i+1)**2))
          
          numeratorSRLGLE[theta] += ( (Pval) / (((j+1)**2)*((i+1)**2)) )  
          numeratorSRHGLE[theta] += ( (Pval*((i+1)**2)) / ((j+1)**2) )
            
          numeratorLRLGLE[theta] += ( (Pval*((j+1)**2)) / ((i+1)**2) ) 
          numeratorLRHGLE[theta] += ( (Pval*((j+1)**2))*((i+1)**2) )
          
      runPercentage[theta] = (sum_P[theta]/Np) 
      
      # check for the event that there are no run lengths
      # in the direction theta to avoid divide by zero errors
      if(sum_P[theta] != 0):  
             
        numeratorSRE[theta] = numeratorSRE[theta]/sum_P[theta]
        numeratorLRE[theta] = numeratorLRE[theta]/sum_P[theta]
      
        numeratorGLN[theta] = numeratorGLN[theta]/sum_P[theta]
        numeratorRLN[theta] = numeratorRLN[theta]/sum_P[theta]     
                     
        numeratorLGLRE[theta] = numeratorLGLRE[theta]/sum_P[theta]
        numeratorHGLRE[theta] = numeratorHGLRE[theta]/sum_P[theta]
          
        numeratorSRLGLE[theta] = numeratorSRLGLE[theta]/sum_P[theta]
        numeratorSRHGLE[theta] = numeratorSRHGLE[theta]/sum_P[theta]
            
        numeratorLRLGLE[theta] = numeratorLRLGLE[theta]/sum_P[theta]
        numeratorLRHGLE[theta] = numeratorLRHGLE[theta]/sum_P[theta]
    
    
    #Evaluate dictionary elements corresponding to user selected keys
    for key in keys:
      self.textureFeaturesGLRL[key] = eval(self.textureFeaturesGLRL[key])
    return(self.textureFeaturesGLRL)
    
  
  def glrl_loop(self, ii, matrix, matrixCoordinates, angles, grayLevels, P_out):    
    padVal = 0 #use eps or NaN to pad matrix
    matrixDiagonals = list()
    
    #For a single direction or diagonal (aDiags, bDiags...lDiags, mDiags):   
    #Generate a 1D array for each valid offset of the diagonal, a, in the range specified by lowBound and highBound  
    #Convert each 1D array to a python list ( matrix.diagonal(a,,).tolist() ) 
    #Join lists using reduce(lamda x,y: x+y, ...) to represent all 1D arrays for the direction/diagonal
     
    #use filter(lambda x: numpy.nonzero(x)[0].size>1, ....) to filter 1D arrays of size < 2 or value == 0 or padValue
    #should change from nonzero() to filter for padValue specifically (NaN or eps)
    
    #(1,0,0), #(-1,0,0),
    aDiags = reduce(lambda x,y: x+y, [a.tolist() for a in numpy.transpose(matrix,(1,2,0))])  
    matrixDiagonals.append( filter(lambda x: numpy.nonzero(x)[0].size>1, aDiags) )
                 
    #(0,1,0), #(0,-1,0),
    bDiags = reduce(lambda x,y: x+y, [a.tolist() for a in numpy.transpose(matrix,(0,2,1))])
    matrixDiagonals.append( filter(lambda x: numpy.nonzero(x)[0].size>1, bDiags) )
               
    #(0,0,1), #(0,0,-1), 
    cDiags = reduce(lambda x,y: x+y, [a.tolist() for a in numpy.transpose(matrix,(0,1,2))])
    matrixDiagonals.append( filter(lambda x: numpy.nonzero(x)[0].size>1, cDiags) )
                
    #(1,1,0),#(-1,-1,0),
    lowBound = -matrix.shape[0]+1
    highBound = matrix.shape[1]
    
    dDiags = reduce(lambda x,y: x+y, [matrix.diagonal(a,0,1).tolist() for a in xrange(lowBound, highBound)])
    matrixDiagonals.append( filter(lambda x: numpy.nonzero(x)[0].size>1, dDiags) )
                         
    #(1,0,1), #(-1,0-1),
    lowBound = -matrix.shape[0]+1
    highBound = matrix.shape[2]
      
    eDiags = reduce(lambda x,y: x+y, [matrix.diagonal(a,0,2).tolist() for a in xrange(lowBound, highBound)])
    matrixDiagonals.append( filter(lambda x: numpy.nonzero(x)[0].size>1, eDiags) )
        
    #(0,1,1), #(0,-1,-1),
    lowBound = -matrix.shape[1]+1
    highBound = matrix.shape[2]
    
    fDiags = reduce(lambda x,y: x+y, [matrix.diagonal(a,1,2).tolist() for a in xrange(lowBound, highBound)])
    matrixDiagonals.append( filter(lambda x: numpy.nonzero(x)[0].size>1, fDiags) )
                             
    #(1,-1,0), #(-1,1,0),    
    lowBound = -matrix.shape[0]+1
    highBound = matrix.shape[1]
    
    gDiags = reduce(lambda x,y: x+y, [matrix[:,::-1,:].diagonal(a,0,1).tolist() for a in xrange(lowBound, highBound)])
    matrixDiagonals.append( filter(lambda x: numpy.nonzero(x)[0].size>1, gDiags) )
     
    #(-1,0,1), #(1,0,-1),
    lowBound = -matrix.shape[0]+1
    highBound = matrix.shape[2]
    
    hDiags = reduce(lambda x,y: x+y, [matrix[:,:,::-1].diagonal(a,0,2).tolist() for a in xrange(lowBound, highBound)])
    matrixDiagonals.append( filter(lambda x: numpy.nonzero(x)[0].size>1, hDiags) )
                  
    #(0,1,-1), #(0,-1,1),
    lowBound = -matrix.shape[1]+1
    highBound = matrix.shape[2]
            
    iDiags = reduce(lambda x,y: x+y, [matrix[:,:,::-1].diagonal(a,1,2).tolist() for a in xrange(lowBound, highBound)])
    matrixDiagonals.append( filter(lambda x: numpy.nonzero(x)[0].size>1, iDiags) )
               
    #(1,1,1), #(-1,-1,-1)
    lowBound = -matrix.shape[0]+1
    highBound = matrix.shape[1]
    
    jDiags = [ numpy.diagonal(h,x,0,1).tolist() for h in [matrix.diagonal(a,0,1) for a in xrange(lowBound, highBound)] for x in xrange(-h.shape[0]+1, h.shape[1]) ]
    matrixDiagonals.append( filter(lambda x: numpy.nonzero(x)[0].size>1, jDiags) )
                             
    #(-1,1,-1), #(1,-1,1),
    lowBound = -matrix.shape[0]+1
    highBound = matrix.shape[1]
    
    kDiags = [ numpy.diagonal(h,x,0,1).tolist() for h in [matrix[:,::-1,:].diagonal(a,0,1) for a in xrange(lowBound, highBound)] for x in xrange(-h.shape[0]+1, h.shape[1]) ]
    matrixDiagonals.append( filter(lambda x: numpy.nonzero(x)[0].size>1, kDiags) )
                          
    #(1,1,-1), #(-1,-1,1),
    lowBound = -matrix.shape[0]+1
    highBound = matrix.shape[1]
    
    lDiags = [ numpy.diagonal(h,x,0,1).tolist() for h in [matrix[:,:,::-1].diagonal(a,0,1) for a in xrange(lowBound, highBound)] for x in xrange(-h.shape[0]+1, h.shape[1]) ]
    matrixDiagonals.append( filter(lambda x: numpy.nonzero(x)[0].size>1, lDiags) )
                         
    #(-1,1,1), #(1,-1,-1),
    lowBound = -matrix.shape[0]+1
    highBound = matrix.shape[1]
    
    mDiags = [ numpy.diagonal(h,x,0,1).tolist() for h in [matrix[:,::-1,::-1].diagonal(a,0,1) for a in xrange(lowBound, highBound)] for x in xrange(-h.shape[0]+1, h.shape[1]) ]
    matrixDiagonals.append( filter(lambda x: numpy.nonzero(x)[0].size>1, mDiags) )
                
    #or [n for n in mDiags if numpy.nonzero(n)[0].size>1] instead of filter(lambda x: numpy.nonzero(x)[0].size>1, mDiags)
    #ii is the array containing the corresponding intensity level to the i and j indices of P[:,:,g,a]
    #use ii[i] or ii[j] to get intensity level intensity, i+1 or j+1 for intensity level instead of using the dict
    voxelToIndexDict = dict(zip(ii,numpy.arange(ii.size)))
    
    #Run-Length Encoding (rle) for the 13 list of diagonals (1 list per 3D direction/angle)
    for angle in xrange (0, len(matrixDiagonals)): #13 diagonalLists
      P = P_out[:,:,angle]     
      for diagonal in matrixDiagonals[angle]:
        diagonal = numpy.array(diagonal, dtype='int')
        pos, = numpy.where(numpy.diff(diagonal) != 0) #can use instead of using map operator._ on np.where tuples
        pos = numpy.concatenate(([0], pos+1, [len(diagonal)]))     
              
        #a or pos[:-1] = run start #b or pos[1:] = run stop #diagonal[a] is matrix value       
        #adjust condition for pos[:-1] != padVal = 0 to != padVal = eps or NaN or whatever pad value
        rle = zip([n for n in diagonal[pos[:-1]] if n!=padVal], pos[1:] - pos[:-1])
        rle = [ [voxelToIndexDict[x],y-1] for x,y in rle ] #rle = map(lambda (x,y): [voxelToIndexDict[x],y-1], rle)
        # Increment GLRL matrix counter at coordinates defined by the run-length encoding               
        P[zip(*rle)] += 1
         
    return (P_out)   
       
  def voxelCount (self, parameterValues):
    return (parameterValues.size)        
