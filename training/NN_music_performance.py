import pandas as pd
from keras.models import load_model
from random import randrange
import numpy as np

def build_model():
	# build model from trained files
	model = load_model('data/model.h5')
	sumry = model.summary()
	print (sumry)
	# make probability predictions with the model
	return model

def prediction(model, X):
	pdct = model.predict(X)
	return pdct

def test_array():
	rang = 200
	arry = []
	for i in range(rang):
		sampl = np.random.uniform(low=0, high=1, size=(3))
		arry = sampl
	print (arry)
	return arry

def random():
	return randrange(-100, 100)/100

#code starts here
model = build_model()

for i in range (100):
	# new instance where we do not know the answer
	Xnew = np.array([[random(), random(), random()]])
	# make a prediction
	ynew = model.predict(Xnew)
	# show the inputs and predicted outputs
	print("X=%s, Predicted=%s" % (Xnew[0], ynew[0]))




""" 
current output with latest model gives range 0.35 - 0.6
"""