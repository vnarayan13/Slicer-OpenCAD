from __main__ import vtk, qt, ctk, slicer
import string
import numpy
import math
import operator
import collections
#import decimal
#from decimal import *

class TextureGLCM:

  def __init__(self, ii, parameterMatrix, parameterMatrixCoordinates, parameterValues, grayLevels, allKeys):
    self.textureFeaturesGLCM = collections.OrderedDict()       
    self.textureFeaturesGLCM["Autocorrelation"] = "self.autocorrelationGLCM(self.P_glcm, prodMatrix)"
    self.textureFeaturesGLCM["Cluster Prominence"] = "self.clusterProminenceGLCM(self.P_glcm, sumMatrix, ux, uy)"
    self.textureFeaturesGLCM["Cluster Shade"] = "self.clusterShadeGLCM(self.P_glcm, sumMatrix, ux, uy)"
    self.textureFeaturesGLCM["Cluster Tendency"] = "self.clusterTendencyGLCM(self.P_glcm, sumMatrix, ux, uy)"
    self.textureFeaturesGLCM["Contrast"] = "self.contrastGLCM(self.P_glcm, diffMatrix)"
    self.textureFeaturesGLCM["Correlation"] = "self.correlationGLCM(self.P_glcm, prodMatrix, ux, uy, sigx, sigy)"
    self.textureFeaturesGLCM["Difference Entropy"] = "self.differenceEntropyGLCM(pxSuby, eps)"
    self.textureFeaturesGLCM["Dissimilarity"] = "self.dissimilarityGLCM(self.P_glcm, diffMatrix)"
    self.textureFeaturesGLCM["Energy (GLCM)"] = "self.energyGLCM(self.P_glcm)"
    self.textureFeaturesGLCM["Entropy(GLCM)"] = "numpy.mean(ent[0,:])"  #"self.entropyGLCM(self.P_glcm, pxy, eps)" 
    self.textureFeaturesGLCM["Homogeneity 1"] = "self.homogeneity1GLCM(self.P_glcm, diffMatrix)"
    self.textureFeaturesGLCM["Homogeneity 2"] = "self.homogeneity2GLCM(self.P_glcm, diffMatrix)"
    self.textureFeaturesGLCM["IMC1"] = "numpy.mean(imc1[0,:])" #"self.imc1GLCM(self,)" 
    #self.textureFeaturesGLCM["IMC2"] = "sum(imc2)/len(imc2)" #"self.imc2GLCM(self,)"  # produces a calculation error
    self.textureFeaturesGLCM["IDMN"] = "self.idmnGLCM(self.P_glcm, diffMatrix, Ng)"
    self.textureFeaturesGLCM["IDN"] = "self.idnGLCM(self.P_glcm, diffMatrix, Ng)"
    self.textureFeaturesGLCM["Inverse Variance"] = "self.inverseVarianceGLCM(self.P_glcm, diffMatrix, Ng)"
    self.textureFeaturesGLCM["Maximum Probability"] = "self.maximumProbabilityGLCM(self.P_glcm)"
    self.textureFeaturesGLCM["Sum Average"] = "self.sumAverageGLCM(pxAddy, kValuesSum)"
    self.textureFeaturesGLCM["Sum Entropy"] = "self.sumEntropyGLCM(pxAddy, eps)" 
    self.textureFeaturesGLCM["Sum Variance"] = "self.sumVarianceGLCM(pxAddy, kValuesSum)"   
    self.textureFeaturesGLCM["Variance (GLCM)"] = "self.varianceGLCM(self.P_glcm, ivector, u)"
    
    self.ii = ii
    self.parameterMatrix = parameterMatrix
    self.parameterMatrixCoordinates = parameterMatrixCoordinates
    self.parameterValues = parameterValues
    self.grayLevels = grayLevels
    self.keys = set(allKeys).intersection(self.textureFeaturesGLCM.keys())
                
  def EvaluateFeatures(self):
    if not self.keys:
      return(self.textureFeaturesGLCM)
        
    # normalization step:
 
    ##Generate GLCM Matrices (self.P_glcm)
    # make distance an optional parameter, as in: distances = numpy.arange(parameter)
    distances = numpy.array([1]) 
    directions = 26    
    self.P_glcm = numpy.zeros( (self.grayLevels, self.grayLevels, distances.size, directions) )
    self.P_glcm = self.glcm_loop(self.ii, self.parameterMatrix, self.parameterMatrixCoordinates, distances, directions, self.grayLevels, self.P_glcm) 
  
    #make each GLCM symmetric an optional parameter
    #if symmetric:
      #Pt = numpy.transpose(P, (1, 0, 2, 3))
      #P = P + Pt
    
    ##Calculate GLCM
    Ng = self.grayLevels
    ivector = numpy.arange(1,Ng+1) #shape = (Ng, distances.size, directions)
    jvector = numpy.arange(1,Ng+1) #shape = (Ng, distances.size, directions)
    eps = numpy.spacing(1)
    
    prodMatrix = numpy.multiply.outer(ivector, jvector) #shape = (Ng, Ng)
    sumMatrix = numpy.add.outer(ivector, jvector) #shape = (Ng, Ng)
    diffMatrix = numpy.absolute(numpy.subtract.outer(ivector, jvector)) #shape = (Ng, Ng)
    kValuesSum = numpy.arange(2, (Ng*2)+1) #shape = (2*Ng-1)
    kValuesDiff = numpy.arange(0,Ng) #shape = (Ng-1)
      
    u = self.P_glcm.mean(0).mean(0) #shape = (distances.size, directions)
    px = self.P_glcm.sum(1) #marginal row probabilities #shape = (Ng, distances.size, directions)
    py = self.P_glcm.sum(0) #marginal column probabilities #shape = (Ng, distances.size, directions)
    
    ux = px.mean(0) #shape = (distances.size, directions)
    uy = py.mean(0) #shape = (distances.size, directions)
    
    sigx = px.std(0) #shape = (distances.size, directions)
    sigy = py.std(0) #shape = (distances.size, directions)
    
    pxAddy = numpy.array([ numpy.sum(self.P_glcm[sumMatrix == k], 0) for k in kValuesSum ]) #shape = (2*Ng-1, distances.size, directions)
    pxSuby = numpy.array([ numpy.sum(self.P_glcm[diffMatrix == k], 0) for k in kValuesDiff ]) #shape = (Ng, distances.size, directions)
    
    HX = (-1) * numpy.sum( (px * numpy.where(px!=0, numpy.log2(px), numpy.log2(eps))), 0) #entropy of px #shape = (distances.size, directions)
    HY = (-1) * numpy.sum( (py * numpy.where(py!=0, numpy.log2(py), numpy.log2(eps))), 0) #entropy of py #shape = (distances.size, directions)
    HXY = (-1) * numpy.sum( numpy.sum( (self.P_glcm * numpy.where(self.P_glcm!=0, numpy.log2(self.P_glcm), numpy.log2(eps))), 0 ), 0 ) #shape = (distances.size, directions)
    
    ### generate pxy with shape = self.P_glcm.shape
    textureMetricArrayShape = tuple([distances.size, directions])      
    HXY1 = numpy.zeros(tuple([distances.size, directions]))
    HXY2 = numpy.zeros(tuple([distances.size, directions]))   
    ent = numpy.zeros(textureMetricArrayShape)
    imc1 = numpy.zeros(textureMetricArrayShape)
      
    #imc2 = []#numpy.zeros((textureMetricArrayShape), dtype='float128')          
    #decimal.getcontext().prec = 4
    for a in xrange(directions):
      for g in xrange(distances.size):
        Pij = self.P_glcm[:,:,g,a]         
        pxy = numpy.multiply.outer(px[:,g,a], py[:,g,a])
        HXY1[g,a] = (-1) * numpy.sum( Pij * numpy.where(pxy!=0, numpy.log2(pxy), numpy.log2(eps)) ) #shape = (distances.size, directions)
        HXY2[g,a] = (-1) * numpy.sum( pxy * numpy.where(pxy!=0, numpy.log2(pxy), numpy.log2(eps)) ) #shape = (distances.size, directions)      
        
        ent[g,a] = -1 * numpy.sum( Pij * numpy.where(pxy!=0, numpy.log2(pxy), numpy.log2(eps)) )        
        imc1[g,a] = ((HXY[g,a]) - HXY1[g,a])/(numpy.max([HX[g,a],HY[g,a]]))
       
       #produces Nan(square root of a negative)
       #exponent = decimal.Decimal( -2*(HXY2[g,a]-HXY[g,a]) )      
       #imc2.append( ( decimal.Decimal(1)-decimal.Decimal(numpy.e)**(exponent) )**(decimal.Decimal(0.5)) ) 
            
    
    #Evaluate dictionary elements corresponding to user selected keys
    for key in self.keys:
      self.textureFeaturesGLCM[key] = eval(self.textureFeaturesGLCM[key])
    return(self.textureFeaturesGLCM)        
    
    
  def autocorrelationGLCM(self, P_glcm, prodMatrix, meanFlag=True):
    ac = numpy.sum(numpy.sum(P_glcm*prodMatrix[:,:,None,None], 0 ), 0 )
    if meanFlag:
     return (ac.mean())
    else:
     return ac
    
  def clusterProminenceGLCM(self, P_glcm, sumMatrix, ux, uy, meanFlag=True):
    # Need to validate function
    cp = numpy.sum( numpy.sum( (P_glcm * ((sumMatrix[:,:,None,None] - ux[None,None,:,:] - uy[None,None,:,:])**4)), 0 ), 0 )
    if meanFlag:
     return (cp.mean())
    else:
     return cp
      
  def clusterShadeGLCM(self, P_glcm, sumMatrix, ux, uy, meanFlag=True):
    # Need to validate function
    cs = numpy.sum( numpy.sum( (P_glcm * ((sumMatrix[:,:,None,None] - ux[None,None,:,:] - uy[None,None,:,:])**3)), 0 ), 0 )
    if meanFlag:
     return (cs.mean())
    else:
     return cs
    
  def clusterTendencyGLCM(self, P_glcm, sumMatrix, ux, uy, meanFlag=True):
    # Need to validate function
    ct = numpy.sum( numpy.sum( (P_glcm * ((sumMatrix[:,:,None,None] - ux[None,None,:,:] - uy[None,None,:,:])**2)), 0 ), 0 )
    if meanFlag:
     return (ct.mean())
    else:
     return ct
    
  def contrastGLCM(self, P_glcm, diffMatrix, meanFlag=True):
    cont = numpy.sum( numpy.sum( (P_glcm * (diffMatrix[:,:,None,None]**2)), 0 ), 0 )
    if meanFlag:
     return (cont.mean())
    else:
     return cont
    
  def correlationGLCM(self,P_glcm, prodMatrix, ux, uy, sigx, sigy, meanFlag=True):
    # Need to validate function
    uxy = ux * uy
    sigxy = sigx * sigy  
    corr = numpy.sum( numpy.sum( ((P_glcm * prodMatrix[:,:,None,None] - uxy[None,None,:,:] ) / (sigxy[None,None,:,:])), 0 ), 0 )
    if meanFlag:
     return (corr.mean())
    else:
     return corr
    
  def differenceEntropyGLCM(self, pxSuby, eps, meanFlag=True):
    difent = numpy.sum( (pxSuby*numpy.where(pxSuby!=0,numpy.log2(pxSuby), numpy.log2(eps))), 0 )
    if meanFlag:
     return (difent.mean())
    else:
     return difent
    
  def dissimilarityGLCM(self, P_glcm, diffMatrix, meanFlag=True):
    dis = numpy.sum( numpy.sum( (P_glcm * diffMatrix[:,:,None,None]), 0 ), 0 )
    if meanFlag:
     return (dis.mean())
    else:
     return dis
    
  def energyGLCM(self, P_glcm, meanFlag=True):
    ene = numpy.sum( numpy.sum( (P_glcm**2), 0), 0 )
    if meanFlag:
     return (ene.mean())
    else:
     return ene
    
  #def entropyGLCM(self, P_glcm, pxy, eps, meanFlag=True):
    #ent = (-1) * numpy.sum( numpy.sum( (P_glcm * (numpy.where(pxy!=0, numpy.log2(pxy), numpy.log2(eps)))[:,:,None,None]), 0 ), 0 )
    #if meanFlag:
     #return (ent.mean())
    #else:
     #return ent
    
  def homogeneity1GLCM(self, P_glcm, diffMatrix, meanFlag=True):
    homo1 = numpy.sum( numpy.sum( (P_glcm / (1 + diffMatrix[:,:,None,None])), 0 ), 0 )
    if meanFlag:
     return (homo1.mean())
    else:
     return homo1
    
  def homogeneity2GLCM(self, P_glcm, diffMatrix, meanFlag=True):
    homo2 = numpy.sum( numpy.sum( (P_glcm / (1 + diffMatrix[:,:,None,None]**2)), 0 ), 0 )
    if meanFlag:
     return (homo2.mean())
    else:
     return homo2
    
  #def imc1GLCM(self,):
    #imc1[g,a] = ((HXY[g,a]) - HXY1[g,a])/(numpy.max([HX[g,a],HY[g,a]]))
    #if meanFlag:
     #return (homo2.mean())
    #else:
     #return homo2     
    
  #def imc2GLCM(self,):
    #imc2[g,a] = ( 1-numpy.e**(-2*(HXY2[g,a]-HXY[g,a])) )**(0.5) #nan value too high
    #if meanFlag:
     #return (homo2.mean())
    #else:
     #return homo2
    
  def idmnGLCM(self, P_glcm, diffMatrix, Ng, meanFlag=True):
    idmn = numpy.sum( numpy.sum( (P_glcm / (1 + ((diffMatrix[:,:,None,None]**2)/(Ng**2)))), 0 ), 0 )
    if meanFlag:
     return (idmn.mean())
    else:
     return idmn
     
  def idnGLCM(self, P_glcm, diffMatrix, Ng, meanFlag=True):
    idn  = numpy.sum( numpy.sum( (P_glcm / (1 + (diffMatrix[:,:,None,None]/Ng))), 0 ), 0 )
    if meanFlag:
     return (idn.mean())
    else:
     return idn
     
  def inverseVarianceGLCM(self, P_glcm, diffMatrix, Ng, meanFlag=True):
    maskDiags = numpy.ones(diffMatrix.shape, dtype = bool)
    maskDiags[numpy.diag_indices(Ng)] = False         
    inv = numpy.sum( (P_glcm[maskDiags] / (diffMatrix[:,:,None,None]**2)[maskDiags]), 0 )
    if meanFlag:
     return (inv.mean())
    else:
     return inv
       
  def maximumProbabilityGLCM(self, P_glcm, meanFlag=True):
    maxprob = P_glcm.max(0).max(0)
    if meanFlag:
     return (maxprob.mean())
    else:
     return maxprob
     
  def sumAverageGLCM(self, pxAddy, kValuesSum, meanFlag=True):
    sumavg =  numpy.sum( (kValuesSum[:,None,None]*pxAddy), 0 )  
    if meanFlag:
     return (sumavg.mean())
    else:
     return sumavg
     
  def sumEntropyGLCM(self, pxAddy, eps, meanFlag=True):
    sumentr = (-1) * numpy.sum( (pxAddy*numpy.where(pxAddy!=0, numpy.log2(pxAddy), numpy.log2(eps))), 0 )
    if meanFlag:
     return (sumentr.mean())
    else:
     return sumentr
     
  def sumVarianceGLCM(self, pxAddy, kValuesSum, meanFlag=True):
    sumvar = numpy.sum( (pxAddy*((kValuesSum[:,None,None] - kValuesSum[:,None,None]*pxAddy)**2)), 0 )
    if meanFlag:
     return (sumvar.mean())
    else:
     return sumvar
     
  def varianceGLCM(self, P_glcm, ivector, u, meanFlag=True):
    vari = numpy.sum( numpy.sum( (P_glcm * ((ivector[:,None]-u)**2)[:,None,None,:]), 0 ), 0 )
    if meanFlag:
     return (vari.mean())
    else:
     return vari
     
  def glcm_loop(self, ii, matrix, matrixCoordinates, distances, directions, grayLevels, out):
    # 26 GLCM matrices for each image for every direction from the voxel 
    # (26 for each neighboring voxel from a reference voxel centered in a 3x3 cube)
    # for GLCM matrices P(i,j;gamma, a), gamma = 1, a = 1...13
    
    angles_idx = 0
    distances_idx = 0
    r = 0
    c = 0
    h = 0
    rows = matrix.shape[2]
    cols = matrix.shape[1]
    height = matrix.shape[0]
    row = 0
    col = 0
    height = 0
    
    angles = numpy.array([ (1,0,0),
             (-1,0,0),
             (0,1,0),
             (0,-1,0),
             (0,0,1),
             (0,0,-1),      
             (1,1,0),
             (-1,1,0),
             (1,-1,0),
             (-1,-1,0),
             (1,0,1),
             (-1,0,1),
             (1,0,-1),
             (-1,0,-1),
             (0,1,1),
             (0,-1,1),
             (0,1,-1),
             (0,-1,-1),
             (1,1,1),
             (-1,1,1),
             (1,-1,1),
             (1,1,-1),
             (-1,-1,1),
             (-1,1,-1),
             (1,-1,-1),
             (-1,-1,-1) ])    
    
    indices = zip(*matrixCoordinates)
    
    for h, c, r in indices:
    
      for angles_idx in xrange(directions):
        angle = angles[angles_idx]
        
        for distances_idx in xrange(distances.size):
          distance = distances[distances_idx]
              
          i = matrix[h, c, r]
          i_idx = numpy.nonzero(ii == i)

          row = r + angle[2]
          col = c + angle[1]
          height = h + angle[0]
          
          #Can introduce Paramter Option for reference voxel(i) and neighbor voxel(j):
          #Intratumor only: i and j both must be in tumor ROI
          #Tumor+Surrounding: i must be in tumor ROI but J does not have to be
          if row >= 0 and row < rows and col >= 0 and col < cols:
            if tuple((height, col, row)) in indices:
              j = matrix[height, col, row]
              j_idx = numpy.nonzero(ii == j)
              #if i >= ii.min and i <= ii.max and j >= ii.min and j <= ii.max:
              out[i_idx, j_idx, distances_idx, angles_idx] += 1          
    
    return (out)  
    

 
