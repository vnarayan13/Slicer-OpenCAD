from __main__ import vtk, qt, ctk, slicer
import string


class MetricDescriptionLabel:
  
  def __init__(self, metricName):
    self.descriptionLabel = qt.QLabel()
    self.descriptionLabel.setFixedWidth(300)
    self.descriptionLabel.setFrameStyle(qt.QFrame.Box)
    self.descriptionLabel.setWordWrap(True)
   
    self.description = metricName + ' Description:\n\n'  
    self.setDescription(metricName)
    
    self.descriptionLabel.setText(self.description)
  
  def setDescription(self, metricName):
  
    if metricName == "Voxel Count":
      self.description += "Voxel Count is the total number of voxels within the ROI of the grayscale image or parameter map."
    elif metricName == "Energy":
      self.description += "Energy is a measure of the magnitude of values in an image. A greater amount larger values implies a greater sum of the squares of these values."
    elif metricName == "Entropy":
      self.description += "Entropy of the image histogram specifies the uncertainty in the image values. It measures the average amount of information required to encode the image values."
    elif metricName == "Minimum Intensity":
      self.description += "Minimum Intensity is the value of the voxel(s) in the image ROI with the least value."
    elif metricName == "Maximum Intensity":
      self.description += "Maximum Intensity is the value of the voxel(s) in the image ROI with the greatest value."
    elif metricName == "Mean Intensity":
      self.description += "Mean Intensity is the mean of the intensity or parameter values within the image ROI."
    elif metricName == "Median Intensity":
      self.description += "Median Intensity is the median of the intensity or parameter values within the image ROI."
    elif metricName == "Range":
      self.description += "Range is the difference between the highest and lowest voxel values within the image ROI."
    elif metricName == "Mean Deviation":
      self.description += "Mean Deviation is the mean of the distances of each image value from the mean of all the values in the image ROI."
    elif metricName == "Root Mean Square":
      self.description += "Root Mean Square is the square-root of the mean of the squares of the values in the image ROI. It is another measure of the magnitude of the image values."
    elif metricName == "Standard Deviation":
      self.description += "Standard Deviation measures the amount of variation or dispersion from the mean of the image values"
    elif metricName == "Skewness":
      self.description += "Skewness measures the asymmetry of the distribution of values in the image ROI about the mean of the values. Depending on where the tail is elongated and the mass of the distribution is concentrated, this value can be positive or negative."
    elif metricName == "Kurtosis":
      self.description += "Kurtosis is a measure of the 'peakedness' of the distribution of values in the image ROI. A higher kurtosis implies that the mass of the distribution is concentrated towards the tail(s) rather than towards the mean. A lower kurtosis implies the reverse, that the mass of the distribution is concentrated towards a spike the mean."
    elif metricName == "Variance":
      self.description += "Variance is the mean of the squared distances of each value in the image ROI from the mean of the values. This is a measure of the spread of the distribution about the mean."
    elif metricName == "Uniformity":
      self.description += "Uniformity is a measure of the sum of the squares of each discrete value in the image ROI. This is a measure of the heterogeneity of an image, where a greater uniformity implies a greater heterogeneity or a greater range of discrete image values."
    
    
      
    elif metricName == "Volume mm^3":
      self.description += "The volume of the specified ROI of the image in cubic millimeters."
    elif metricName == "Volume cc":
      self.description += "The volume of the specified ROI of the image in cubic centimeters."
    elif metricName == "Surface Area":
      self.description += "The surface area of the specified ROI of the image in square millimeters."
    elif metricName == "Surface:Volume Ratio":
      self.description += "The ratio of the surface area (square millimeters) to the volume (cubic millimeters) of the specified image ROI."
    elif metricName == "Compactness 1":
      self.description += "Compactness 1 is a dimensionless measure, independent of scale and orientation. Compactness 1 is defined as the ratio of volume to the (surface area)^(1.5). This is a measure of the compactness of the shape of the image ROI."
    elif metricName == "Compactness 2":
      self.description += "Compactness 2 is a dimensionless measure, independent of scale and orientation. This is a measure of the compactness of the shape of the image ROI."
    elif metricName == "Maximum 3D Diameter":
      self.description += "Maximum 3D Diameter is the maximum, pairwise euclidean distance between surface voxels of the image ROI."
    elif metricName == "Spherical Disproportion":
      self.description += "Spherical Disproportion is defined as the ratio of the surface area of the image ROI to the surface area of a sphere with the same volume as the image ROI."
    elif metricName == "Sphericity":
      self.description += "Sphericity is a measure of the roundness or spherical nature of the image ROI, where the sphericity of a sphere is the maximum value of 1."
    
     
     
    elif metricName == "Box-Counting Dimension":
      self.description += "Box-Counting Dimension is part of the family of Renyi Dimensions, where q=0 for Renyi Entropy calculations. This represents the fractal dimension: the slope of the curve on a plot of log(N) vs. log(1/s) where 'N' is the number of boxes occupied by the image ROI at each scale, 's', of an overlaid grid."
    elif metricName == "Information Dimension":
      self.description += "Information Dimension is part of the family of Renyi Dimensions, where q=1 for Renyi Entropy calculations."
    elif metricName == "Correlation Dimension":
      self.description += "Correlation Dimension is part of the family of Renyi Dimensions, where q=2 for Renyi Entropy calculations."
    
    
    elif metricName == "Geometrical Measures":
      self.description += "Edit parameters for or Toggle the generation of the extruded, binary 4D object needed to calculate metrics for this class. If this is unchecked, there will be no metrics computed for this Feature Class." 
    elif metricName == "Extruded Surface Area":
      self.description += "Extruded Surface Area is the surface area of the binary object when the image ROI is 'extruded' into 4D, where the parameter or intensity value defines the shape of the Fourth dimension."   
    elif metricName == "Extruded Volume":
      self.description += "Extruded Volume is the volume of the binary object when the image ROI is 'extruded' into 4D, where the parameter or intensity value defines the shape of the Fourth dimension."
    elif metricName == "Extruded Surface:Volume Ratio":
      self.description += "Extruded Surface:Volume Ratio is the ratio of the surface area to the volume of the binary object when the image ROI is 'extruded' into 4D, where the parameter or intensity value defines the shape of the Fourth dimension."
    
    
    elif metricName == "Texture: GLCM":
      self.description += "Edit parameters for or Toggle the generation of GLCM matrices needed to calculate metrics for this class. If this is unchecked, there will be no metrics computed for this Feature Class."  
    elif metricName == "Autocorrelation":
      self.description += "Autocorrelation is a measure of the magnitude of the fineness and coarseness of texture."
    elif metricName == "Cluster Prominence":
      self.description += "Cluster Prominence is a measure of the skewness and asymmetry of the GLCM. A higher values implies more asymmetry about the mean value while a lower value indicates a peak around the mean value and less variation about the mean."
    elif metricName == "Cluster Shade":
      self.description += "Cluster Shade is a measure of the skewness and uniformity of the GLCM. A higher cluster shade implies greater asymmetry."
    elif metricName == "Cluster Tendency":
      self.description += "Cluster Tendency indicates the number of potential clusters present in the image."
    elif metricName == "Contrast":
      self.description += "Contrast is a measure of the local intensity variation, favoring P(i,j) values away from the diagonal (i != j), with a larger value correlating with larger image variation."
    elif metricName == "Correlation":
      self.description += "Correlation is a value between 0 (uncorrelated) and 1 (perfectly correlated) showing the linear dependency of gray level values in the GLCM. For a symmetrical GLCM, ux = uy (means of px and py) and sigx = sigy (standard deviations of px and py)."
    elif metricName == "Difference Entropy":
      self.description += "Difference Entropy is.."
    elif metricName == "Dissimilarity":
      self.description += "Dissimilarity is.."
    elif metricName == "Energy (GLCM)":
      self.description += "Energy (for GLCM) is also the Angular Second Moment and is a measure of the homogeneity of an image. A homogeneous image will contain less discrete gray levels, producing a GLCM with fewer but relatively greater values of P(i,j), and a greater sum of the squares."   
    elif metricName == "Entropy (GLCM)":
      self.description += "Entropy (GLCM) indicates the uncertainty of the GLCM. It measures the average amount of information required to encode the image values."
    elif metricName == "Homogeneity 1":
      self.description += "Homogeneity 1 is a measure of local homogeneity that increases with less contrast in the window."
    elif metricName == "Homogeneity 2":
      self.description += "Homogeneity 2 is a measure of local homogeneity."
    elif metricName == "IMC1":
      self.description += "Informational Measure of Correlation 1 (IMC1) is.."
    elif metricName == "IMC2":
      self.description += "Informational Measure of Correlation 2 (IMC2) is.."
    elif metricName == "IDMN":
      self.description += "Inverse Difference Moment Normalized (IDMN) is a measure of the local homogeneity of an image. IDMN weights are the inverse of the Contrast weights (decreasing exponentially from the diagonal i=j in the GLCM). Unlike Homogeneity 2, IDMN normalizes the square of the difference between values by dividing over the square of the total number of discrete values."
    elif metricName == "IDN":
      self.description += "Inverse Difference Normalized (IDN) is another measure of the local homogeneity of an image. Unlike Homogeneity 1, IDN normalizes the difference between the values by dividing over the total number of discrete values."
    elif metricName == "Inverse Variance":
      self.description += "Inverse Variance is.."
    elif metricName == "Maximum Probability":
      self.description += "Maximum Probability is.."
    elif metricName == "Sum Average":
      self.description += "Sum Average is.."
    elif metricName == "Sum Entropy":
      self.description += "Sum Entropy is.."
    elif metricName == "Sum Variance":
      self.description += "Sum Variance weights elements that differ from the average value of the GLCM."
    elif metricName == "Variance (GLCM)":
      self.description += "Variance (for GLCM) is the dispersion of the parameter values around the mean of the combinations of reference and neighborhood pixels, with values farther from the mean weighted higher. A high variance indicates greater distances of values from the mean."
    
    
    elif metricName == "Texture: GLRL":
     self.description +="Edit parameters for or Toggle the generation of GLRL matrices needed to calculate metrics for this class. If this is unchecked, there will be no metrics computed for this Feature Class."  
    elif metricName == "SRE":
     self.description +="Short Run Emphasis (SRE) is a measure of the distribution of short run lengths, with a greater value indicative of shorter run lengths and more fine textural textures."    
    elif metricName == "LRE":
      self.description +="Long Run Emphasis (LRE) is a measure of the distribution of long run lengths, with a greater value indicative of longer run lengths and more coarse structural textures."
    elif metricName == "GLN":
      self.description +="Gray Level Non-Uniformity (GLN) measures the similarity of gray-level intensity values in the image, where a lower GLN value correlates with a greater similarity in intensity values."   
    elif metricName == "RLN":
      self.description +="Run Length Non-Uniformity (RLN) measures the similarity of run lengths throughout the image, with a lower value indicating more homogeneity among run lengths in the image."     
    elif metricName == "RP":
      self.description +="Run Percentage (RP) measures the homogeneity and distribution of runs of an image for a certain direction."     
    elif metricName == "LGLRE":
      self.description +="Low Gray Level Run Emphasis (LGLRE) measures the distribution of low gray-level values, with a higher value indicating a greater concentration of low gray-level values in the image."     
    elif metricName == "HGLRE":
      self.description +="High Gray Level Run Emphasis (HGLRE) measures the distribution of the higher gray-level values, with a higher value indicating a greater concentration of high gray-level values in the image."     
    elif metricName == "SRLGLE":
      self.description +="Short Run Low Gray Level Emphasis (SRLGLE) measures the joint distribution of shorter run lengths with lower gray-level values." 
    elif metricName == "SRHGLE":
      self.description +="Short Run High Gray Level Emphasis (SRHGLE)E) measures the joint distribution of shorter run lengths with higher gray-level values."    
    elif metricName == "LRLGLE":
      self.description +="Long Run Low Gray Level Emphasis (LRLGLE) measures the joint distribution of long run lengths with lower gray-level values."   
    elif metricName == "LRHGLE":
      self.description +="Long Run High Gray Level Emphasis (LRHGLE) measures the joint distribution of long run lengths with higher gray-level values."
      
  
    
  def getDescription(self):
  
    return(self.descriptionLabel)

