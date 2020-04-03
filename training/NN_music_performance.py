import pandas as pd
from keras.models import load_model
from random import randrange
import numpy as np

def build_model():
	# build model from trained files
	model = load_model('data/model.h5')
	# make probability predictions with the model
	return model

def prediction(model, X):
	reshape
	pdct = model.predict(X)
	return pdct

def test_array():
	rang = 200
	for i in range(rang):
		sampl = np.random.uniform(low=0, high=1, size=(200))
	print (sampl)
	return sampl

#code starts here
model = build_model()
array = test_array()
for l in range (len(array)):
	num = array[l]
	pdct = prediction(model, num)
	print ('num= ', num, 'predict= ', pdct)


# for i in range(5):
# 	X = randrange (200)
# 	X /= 100
# 	X = str(X)
# 	predict = model.predict(X)
# 	print(predict)
