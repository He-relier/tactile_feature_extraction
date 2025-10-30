# Tactile Feature Extraction: Code for tactile data collection and supervised learning

This repo contains code for tactile data collection with a vision-based tactile sensor and supervised learnig of tactile features. 
The data is collected using a UR5 and a force torque sensor to obtain labels for each corresponding tactile image. The data is then used for supervised learning to provide a model for predicting tactile features from tactile images in real-time.

This repository is based on the force sensor using **NI-USB-6211** and **ATI Mini45**.
Currently, it only supports **Windows** due to the NI-SUB-6211 driver.

**Parent Branch：https://github.com/maxyang27896/tactile_feature_extraction?tab=readme-ov-file**

ATI F/T mini45  Serial Number：
FT39618
Download the Mini45 calibration from here; 
https://www.ati-ia.com/Library/Software/FTDigitaldownload/getcalfiles.aspx

MINI45 document

https://www.ati-ia.com/products/ft/ft_models.aspx?id=mini45

connect the force sensor via DAQ.

https://www.ati-ia.com/app_content/documents/9620-05-DAQ.pdf

**ATI DAQ F/T software download**

https://www.ati-ia.com/Products/ft/software/daq_software.aspx

USB-6211 driver download

https://www.ni.com/en/support/downloads/drivers/download.ni-daq-mx.html#569187

