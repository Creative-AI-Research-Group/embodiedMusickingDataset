from pydub import AudioSegment
from pydub.playback import play
import glob
from queue import Queue
import threading
import time
import multiprocessing
from random import randrange


audio_path = '../data/audio'
model_path = '../data/'
# mp = multiprocessing()

def timer():
    duration = input ('what is the duration of this performance?')
    print (duration)
    end_time = int(duration) + time.time()
    print (end_time)


class Audio_play():
    pass

my_audio_list = [f for f in glob.glob("../data/audio/*.aif")]


play_lock = threading.Lock()

def play_sound(song):
    print(song)
    play_sound = AudioSegment.from_file(song)
    with play_lock:
        play(play_sound)

def threader():
    while True:
        song = q.get()
        play_sound(song)
        q.task_done()

q = Queue()
num_threads = 8

for i in range(num_threads):
    t = threading.Thread(target=threader)
    t.setDaemon(True)
    t.start()

for sound_play in range (200):
    rnd = randrange(len(my_audio_list))
    song = my_audio_list[rnd]
    q.put(song)

for sound_play in reversed(range (20)):
    song = my_audio_list[sound_play]
    q.put(song)

q.join()


#
#
# if __name__ == '__main__':
#     mp1 = multiprocessing(process = timer)
#     mp2 = process = dataset queries
#     mp3 = ML prediction
#     mp4 = audio