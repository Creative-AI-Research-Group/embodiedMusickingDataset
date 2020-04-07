from keras.models import load_model
from random import randrange
import numpy as np
import glob
from pydub import AudioSegment
from pydub.playback import play
import threading
from queue import Queue

def prediction(model):
	# new instance where we do not know the answer
	Xnew = np.array([random()])
	# make a prediction
	predict = model.predict(Xnew)
	print (predict)
	# ynew = float(predict[0,1])
	# print ('ynew = ', ynew)
	# return (ynew)

def random():
	return randrange(100)/1000

def get_sound_file(ynew): # thread
	# prdct = prediction(model)
	# NewValue = (((OldValue - OldMin) * (NewMax - NewMin)) / (OldMax - OldMin)) + NewMin
	sample = int((((ynew - 0.35) * (20 - 0.0)) / (0.6 - 0.35)) + 0.0)
	print ('sample = ', sample)
	# looping = randrange(16)
	with sound_lock:
		play_sound(sample)

def play_sound(sample):
	sound = sample_list_drums[sample]
	print (sound)
	song = AudioSegment.from_wav(sound)
	#looped_sound = song * looping
	play(song)

# if __name__ == "__main__":
#code starts here
body_model = load_model('data/new_model.h5')
# head_model = load_model('data/head_model.h5')
# left_model = load_model('data/left_model.h5')
# right_model = load_model('data/right_model.h5')
sample_list_drums = glob.glob('data/drums/*.wav')


"""
the idea is to thread - with four different workers each playing a sound
prediction has to be called for once a sound is initialed (the dual thread)

4 workers gets predictons
each choose a sound file/ locatoin
first in locks sound player until complete
"""

sound_lock = threading.Lock()

# this is the operational stuff
def main_task(worker):
	# PRESTUFF HERE
	sound_file = get_sound_file(worker)

	with sound_lock:
		play_sound(sound_file)

# this organises the threading
def threader():
	while True: # will cpontinue until all threads and deamons die
		worker = q.get() # getting the worker from the queue
		main_task(worker) # put the worker to work
		q.task_done() # this instance complete lets move on

# this is the queue of tasks
q = Queue()

for x in range(10): # 10 workers
	t = threading.Thread(target=threader)
	t.daemon = True
	t.start()

for worker in range (20): # 20 jobs
	worker = prediction(body_model)
	q.put(worker) # putting a worker in a q Queue

q.join()


#
#
#
#
#
# for i in range (100):
# 	prediction (model)
#
# for s in range (100):
# 	get_sound_file(s)
#
#
# thread_1 = threading.Thread(target=play_sound, args=(sample, ))
# 	thread_1.start


# # show the inputs and predicted outputs
# print("X=%s, Predicted=%s" % (Xnew[0], ynew[0]))
# sound_file = get_sound_file(ynew)

""" 
current output with latest model gives range 0.35 - 0.6
"""