
# first neural network with keras tutorial
from numpy import loadtxt
# from keras.models import Sequential
# from keras.layers import Dense

# proto dataset is seq_id; limb; x, y, z; FFt freq, amp
# amplitude is operation input X, with xyz  the predicted output (the embodied action)

# load the dataset
dataset = loadtxt('data/dataset', delimiter=';')
# split into input (X) and output (y) variables
print (dataset)

# X = dataset[:,8]
# y = dataset[:,2:5]
#
# print (X, y)