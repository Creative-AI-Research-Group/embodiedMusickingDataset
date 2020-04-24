from keras.models import load_model
from random import randrange
import numpy as np
import glob
from pydub import AudioSegment
from pydub.playback import play
import threading
from queue import Queue
import multiprocessing
import time
import random
import pyaudio

full_model = load_model('data/phase2_body_model.h5')

for i in range (0, 1000, 10):
	pred = np.array([i / 10])
	print (pred)
	pred = pred.reshape ((1, 1))
	print (pred)
	result = full_model.predict(pred)
	print(result)





#
# class Neural_nets:
# 	def __init__(self):
# 		self.body_model = load_model('data/phase3_body_model.h5')
# 		# self.head_model = load_model('data/phase2_head_model.h5')
# 		# self.left_model = load_model('data/phase2_LH_model.h5')
# 		# self.right_model = load_model('data/phase2_RH_model.h5')
# 		self.full_model = load_model('data/phase2_full_model.h5')
#
# 	def full_predict (self, amp_level):
# 		# make a prediction (inputs the amp level will return xyz tuple
# 		self.new_amp_level = [[0, amp_level]]
# 		self.predict = self.full_model.predict(self.new_amp_level)
# 		# self.full_result = float(
# 			#self.predict[1])  # returns only figure index [1], not prediction binary [0] from generated tuple
# 		print('prediction = ', self.predict)
# 		return (self.predict)
# 	#
# 	# def head_predict(self, amp_level):
# 	# 	# make a prediction
# 	# 	self.predict = self.head_model.predict(amp_level)
# 	# 	self.head_result = float(self.predict[0,1]) # returns only figure index [1], not prediction binary [0] from generated tuple
# 	# 	print ('head prediction = ', self.head_result)
# 	# 	return (self.head_result)
# 	#
# 	def body_predict(self, amp_level):
# 		# make a prediction
# 		self.new_amp_level = [[0, amp_level]]
# 		self.predict = self.body_model.predict(self.new_amp_level)
# 		# self.body_result = float(self.predict[0,1]) # returns only figure index [1], not prediction binary [0] from generated tuple
# 		print ('body prediction = ', self.predict)
# 		return (self.predict)
# 	#
# 	# def right_predict(self, amp_level):
# 	# 	# make a prediction
# 	# 	self.predict = self.right_model.predict(amp_level)
# 	# 	self.right_result = float(self.predict[0,1]) # returns only figure index [1], not prediction binary [0] from generated tuple
# 	# 	print ('right prediction = ', self.right_result)
# 	# 	return (self.right_result)
# 	#
# 	# def left_predict(self, amp_level):
# 	# 	# make a prediction
# 	# 	self.predict = self.left_model.predict(amp_level)
# 	# 	self.left_result = float(self.predict[0,1]) # returns only figure index [1], not prediction binary [0] from generated tuple
# 	# 	print ('left prediction = ', self.left_result)
# 	# 	return (self.left_result)
#
#
# class Sound: # handles sound playing
# 	def __init__(self):
# 		self.filepath = 'data/drums'
#
# 	def choose_sound(self, num):
# 		# reshape incoming data to fit sound files in folder e.g. 20
# 		# NewValue = (((OldValue - OldMin) * (NewMax - NewMin)) / (OldMax - OldMin)) + NewMin
# 		sample = int((((num - 0.35) * (19 - 0.0)) / (0.6 - 0.35)) + 0.0)
# 		print ('sample = ', sample)
# 		return sample
# 		# looping = randrange(16)
# 		# with sound_lock:
#
# 	def play_sound(self, sample):
# 		self.sound = self.filepath[sample]
# 		print (self.sound)
# 		self.song = AudioSegment.from_wav(self.sound)
# 		#looped_sound = song * looping
# 		play(self.song)
#
# class Robotmove:
# 	def __init__(self):
# 		pass
# #
# # def baudrate():
# # 	rate = random.randrange(5) / 100
# # 	return rate
# #
# # def body_handler(peak, rate):
# # 	b_num = Neural_nets.body_predict(peak)
# # 	Sound.
# # 	time.sleep(rate)
# #
# # def head_handler():
# 	pass
#
# def left_handler():
# 	pass
#
# def right_handler():
# 	pass
#
# ####################  MAIN CODE ##################
#
# if __name__ == "__main__":
#
# 	# defining audio streaming parameters
# 	CHUNK = 1024
# 	RATE = 44100
# 	nn = Neural_nets()
# 	snd = Sound()
# 	p = pyaudio.PyAudio()
# 	stream = p.open(format=pyaudio.paInt16, channels=1, rate=RATE, input=True,
# 					frames_per_buffer=CHUNK)
#
# # operational loop starts here
# 	while True:
# 		# open the micropohne
# 		data = np.fromstring(stream.read(CHUNK), dtype=np.int16)
# 		peak = np.average(np.abs(data)) * 2
# 		bars = "#" * int(50 * peak / 2 ** 16)
# 		print(" %05d %s" % (peak, bars))
# 		if peak > 50: 	# sound louder than background noise
# 			# send peak to NN
# 			nn_predict = nn.body_predict(peak/10000)
# 			# send result to robot move AND sound maker
# 			# Robotmove()
# 			# play_sound = snd.choose_sound(nn_predict[0][0])
#
#
#
#
#
#
# # # determine baud rate for overall
# # 		rate = baudrate()
# #
# # # multi-processsing starts here
# #
# # 		process_1 = multiprocessing.Process(target=body_handler, args=(peak, rate))
# # 		process_2 = multiprocessing.Process(target=head_handler, args=(peak))
# # 		process_3 = multiprocessing.Process(target=left_handler, args=(peak))
# # 		process_4 = multiprocessing.Process(target=right_handler, args=(peak))
# #
# # 		process_1.start()
# # 		process_2.start()
# # 		process_3.start()
# # 		process_4.start()
# #
# #
# # # stop the stream when finished
# # 	stream.stop_stream()
# # 	stream.close()
# # 	p.terminate()
#
#
#
#
