from keras.models import load_model
from random import randrange
import numpy as np
import glob
from pydub import AudioSegment
from pydub.playback import play
import threading

def prediction(model): # thread 1
	# new instance where we do not know the answer
	Xnew = np.array([[random(), random(), random()]])
	# make a prediction
	predict = model.predict(Xnew)
	ynew = float(predict[0,1])
	print ('ynew = ', ynew)
	predict_list.append(ynew)

def random():
	return randrange(-100, 100)/100

def get_sound_file(s): # thread 2
	prdct = predict_list[s] # NewValue = (((OldValue - OldMin) * (NewMax - NewMin)) / (OldMax - OldMin)) + NewMin
	sample = int((((prdct - 0.35) * (1001 - 0.0)) / (0.6 - 0.35)) + 0.0)
	print ('sample = ', sample)
	# looping = randrange(16)

def play_sound(sample):
	sound = sample_list_drums[sample]
	print (sound)
	song = AudioSegment.from_wav(sound)
	#looped_sound = song * looping
	play(song)

#code starts here
model = load_model('data/model.h5')
sample_list_drums = glob.glob('data/drums/*.wav')
# predict_lock = threading.Lock()
Xnew, ynew = 0, 0.5
predict_list = []

for i in range (100):
	prediction (model)

for s in range (100):
	get_sound_file(s)


thread_1 = threading.Thread(target=play_sound, args=(sample, ))
	thread_1.start


# # show the inputs and predicted outputs
# print("X=%s, Predicted=%s" % (Xnew[0], ynew[0]))
# sound_file = get_sound_file(ynew)

""" 
current output with latest model gives range 0.35 - 0.6
"""