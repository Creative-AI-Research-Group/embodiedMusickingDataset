import pandas as pd
from keras.models import Sequential, load_model
from random import randrange

def build_model():
	# build model from trained files
	model = load_model('data/model.h5')
	# make probability predictions with the model
	return model

# def prediction(model, X):
# 	pdct = model.predict(X)
# 	return (pdct)


#code starts here
model = build_model()
for i in range(5):
	predict = model.predict(X)
	print(predict)
