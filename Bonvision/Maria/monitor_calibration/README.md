# Monitor calibration

## This page explains how to perform monitor calibration for the monitors we use to show visual stimuli to the experimental animals.

### Why calibrating the monitor?

### Part 1: Monitor calibration test

- Before we can calibrate the monitor we first need to determine what the current colour correction is
- for this we need to measure what the monitor displays using a photodiode
- this is present in the current setup (December 2021)
- There is a Bonvision script for this available from [here](https://github.com/Schroeder-Lab/ExperimentalProtocols/blob/main/Bonvision/Maria/monitor_calibration/calibration_scripts_bonsai/GammaCalibration_Test.bonsai)
- However, it gives an error when we try to run it which couldn't be solved, therefore three custom scripts (one for each colour) were written to obtain the output from the photodiode (the phtodiode records the voltage).
- This output (in the form of a binary file) is then fed into a custom python script which feeds the data into an array and gives a graph with the normalised output from all 3 colours at 9 data points

This is how the plot looks like before and after correction:

![corrected_output](https://github.com/Schroeder-Lab/ExperimentalProtocols/blob/main/Bonvision/Maria/monitor_calibration/corrected_output2.png)


### Part 2: Monitor calibration
- the code then inverses and interpolates this data to obtain the corrected values which are used to create a lookup table (LUT)
- this LUT is fed into the **gamma correction** node in Bonsai. This node should be added to all our scripts to allow for gamma correction
