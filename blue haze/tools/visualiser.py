from math import sqrt
from random import random, randint
from tkinter import Tk, Canvas, Frame
from pandas import read_csv
from pygame import mixer

class Data:
    """handles all the data parsing and crunching from dB.csv"""
    DATA_LOGGING = False

    def __init__(self):
        # how many lines per point
        self.POINTS = 4
        self.db_path = db_path
        self.count = 0

        # extract usable data from csv
        df = read_csv(self.db_path, sep=',')
        self.coords = []
        self.eeg = []
        self.eda = []
        self.delta = []
        self.timestamp = []

        if self.DATA_LOGGING:
            print(f'dataframe = {df.values}')
            print(f'dataframe[1000] = {df.values[1000]}')

        # make the timestamp and chorus list for UI
        for _timestamp in df.values:
            self.timestamp.append(_timestamp[6:8])

        # make the delta list for timing
        for _delta in df.values:
            self.delta.append(_delta[5])

        # make the eda list
        for _eda in df.values:
            self.eda.append(_eda[12])

        # make the eeg list
        for _eeg in df.values:
            self.eeg.append(_eeg[13:17])

        # make the skeleton coords list
        for _coords in df.values:
            # generates a temp list for all the skeleton data
            temp_list = _coords[17:-1]
            # print(temp_list)

            # parse the skeleton to tuples for each joint
            t, temp = (), []

            # for each triplet of info (x, y, conf), make a tuple of x, y only,
            # then pack into a list
            for i, d in enumerate(temp_list):
                # if its x, y add to a tuple
                if i % 3 != 2:
                    t += (d, )
                else:
                    # add the tuple to a temp array
                    temp.append(t)
                    t = ()

            # pack tuple list to the final list
            self.coords.append(temp)

        if self.DATA_LOGGING:
            print(f'timestamp = {self.timestamp}')
            print(f'delta = {self.delta}')
            print(f'eda = {self.eda}')
            print(f'eeg = {self.eeg}')
            print(f'coords = {self.coords}')

    # iterate through lists for each frame
    def get_data(self):

        now_delta = self.delta[self.count]

        now_coords = self.coords[self.count]

        now_eeg = self.eeg[self.count]

        now_eda = self.eda[self.count]

        now_timestamp = self.timestamp[self.count]

        if self.DATA_LOGGING:
            print(f'full data is: coords = {now_coords}, eeg = {now_eeg}, eda = {now_eda}, delta = {now_delta}, timestamp = {now_timestamp}')

        self.count += 1
        return now_coords, now_eeg, now_eda, now_delta, now_timestamp

    # calc all distances
    def calc_hypot(self, x, x1, y, y1):
        # cal x diff
        diff_x = x - x1

        # make positive if < 0
        if diff_x < 0:
            diff_x *= -1

        # calc y diff
        diff_y = y - y1

        # make positive if < 0
        if diff_y < 0:
            diff_y *= -1

        # calc hypotenuse
        return sqrt(diff_x ** 2 + diff_y ** 2)

    # calcs shortest distances between skeleton points
    def shortest_dists(self, sub_list):
        if self.DATA_LOGGING:
            print('sub list = ', sub_list)

        # set up temp list for method
        temp_list = []

        # finds only 2 values
        for _ in range(self.POINTS):
            # calcs smallest num from 2 value of list
            _min = min(sub_list, key=lambda t: t[1])

            # adds ity to temp list for storage
            temp_list.append(_min[0])

            # removes it and repeats
            sub_list.remove(_min)

            if self.DATA_LOGGING:
                print(_min[0])
                print('temp list', temp_list)
        return temp_list

    # handles all main calcs coordination for line generation
    def worker(self, coords):
        lines = []
        for i, cood in enumerate(coords):
            sub_list = []

            # iter through each other coord
            for j, next_coord in enumerate(coords):

                if self.DATA_LOGGING:
                    print(f'coords are {i, cood} and {j, next_coord}')

                # if they are not same coord
                if i != j:

                    # calculates the hypotenuse
                    lngth = self.calc_hypot(cood[0], next_coord[0], cood[1], next_coord[1])

                    if self.DATA_LOGGING:
                        print(f'length between {i, cood} and {j, next_coord} = {lngth}')

                    # add as tuples to list
                    sub_list.append([j, lngth])

            # get a list of all the shortest disctances between nodes
            short_list = self.shortest_dists(sub_list)
            lines.append(short_list)
            if self.DATA_LOGGING:
                print(f' FINAL LINES (in order a, b, cood ... h              {lines}')

        return lines


class Draw(Frame):
    """object handling all drawing and scheduling"""
    DRAW_LOGGING = False

    # define all global vars
    WIDTH = 1580
    DEPTH = 1000
    WIDTH_FACTOR = WIDTH / 1000
    DEPTH_FACTOR = DEPTH / 1000
    # FPS = 10 # <---- change this to change speed of playback

    # init the root graphics window
    root = Tk()
    root.title("Skeleton")

    # init the canvas
    canvas = Canvas(root, width=WIDTH, height=DEPTH, bg='azure2')
    canvas.pack()

    def __init__(self, with_audio, fps):
        super().__init__()
        self.audio_path = audio_path
        self.FPS = fps

        # init data worker
        self.data_bot = Data()

        # with audio playback (normal FPS)
        if with_audio:
            # init audio mixer
            self.audio_init()

            # start the audio & graphics
            self.audio_play()

        self.UIUpdater()
        self.root.mainloop()

    # schedules all the mainloop tasks
    def UIUpdater(self):
        # gets skeleton coords, line, and colour details
        coords, eeg, eda, delta, timestamp = self.data_bot.get_data()
        lines = self.data_bot.worker(coords)

        # draws the stuff that is refreshed each frame
        self.drawing(coords, lines, eeg, eda, timestamp, delta)

        # control playback FPS here
        if self.FPS == 0:
            self.after(delta, self.UIUpdater)
        else:
            self.after(self.FPS, self.UIUpdater)

    # handles audio playback
    def audio_init(self):
        mixer.init()
        mixer.music.load(self.audio_path)

    # starts audio playback
    def audio_play(self):
        mixer.music.play(loops=0)

    # handles all the drawing onto the canvas
    def drawing(self, coords, lines, eeg, eda, timestamp, delta):
        # reset the canvas
        self.canvas.delete("all")

        self.canvas.create_text(200, 40, font=("Purisa", 20),
                                fill="white", text="EEG thinking")
        self.canvas.create_text(200, 100, font=("Purisa", 10),
                                fill="white", text=f'{eeg[0]}\n{eeg[1]}\n{eeg[2]}\n{eeg[3]}')
        self.canvas.create_text(600, 40, font=("Purisa", 20),
                                fill="white", text="Skeleton")
        self.canvas.create_text(600, 800, font=("Purisa", 20),
                                fill="white", text="Core nose-neck movement")
        self.canvas.create_text(1000, 40, font=("Purisa", 20),
                                fill="white", text=f"EDA arousal\n    {eda}")
        self.canvas.create_text(1400, 40, font=("Purisa", 20),
                                fill="white", text=f"timestamp =  {timestamp[0]} ms")
        self.canvas.create_text(1400, 140, font=("Purisa", 20),
                                fill="white", text=f"timedelta =  {delta} ms,\nerror = {delta - 100} ms")
        self.canvas.create_text(1400, 240, font=("Purisa", 20),
                                fill="white", text=f"chorus (loop) =  {timestamp[1]}")

        # change background on eda value
        col_eda = eda - 100 # dirty fix as offset
        col_eda = '{:06x}'.format(col_eda)
        col_eda = '#' + col_eda
        self.canvas.configure(bg = col_eda)

        # draw the skeleton points 5 pixels wide
        for i, coord in enumerate(coords):

            coord_x = coord[0] * self.WIDTH_FACTOR
            coord_y = coord[1] * self.DEPTH_FACTOR
            if coord_x < 0:
                continue
            elif coord_y < 0:
                continue

            self.canvas.create_oval(coord_x-2,
                                    coord_y-2,
                                    coord_x+2,
                                    coord_y+2,
                                    outline="#f11", fill="#f11", width=1)

            if self.DRAW_LOGGING:
                print('line = ', lines[i])

            # draw the line between the coord and its closest points
            for end_points in lines[i]:
                end = coords[end_points]
                if self.DRAW_LOGGING:
                    print(f'end = {end}')
                # self.canvas.create_line(coord_x, coord_y, (end[0]*self.WIDTH), (end[1]*self.HEIGHT), fill=col)
                self.canvas.create_line(coord_x, coord_y,
                                        (end[0] * self.WIDTH_FACTOR),
                                        (end[1] * self.DEPTH_FACTOR),
                                        fill="#fff")

        # draw just the nose and neck link as circle
        self.canvas.create_oval(coords[0][0] * self.WIDTH_FACTOR,
                                coords[0][1] * self.DEPTH_FACTOR + 500,
                                coords[1][0] * self.WIDTH_FACTOR,
                                coords[1][1] * self.DEPTH_FACTOR + 500,
                                outline="#f11", fill=None, width=1)

        # draw in the EEG blob
        # start circle coords
        eeg_x_a = eeg[0] / 1000 * self.WIDTH_FACTOR * 2
        eeg_y_a = eeg[1] / 1000 * self.DEPTH_FACTOR * 2

        # end circle coords
        eeg_x_b = eeg[2] / 1000 * self.WIDTH_FACTOR * 2 + 200
        eeg_y_b = eeg[3] / 1000 * self.DEPTH_FACTOR * 2 + 200

        self.canvas.create_rectangle(eeg_x_a,
                                     eeg_y_a,
                                     eeg_x_b,
                                     eeg_y_b,
                                     outline="#000", fill="#fff", width=1)

        # draw the EDA blob
        self.canvas.create_oval(900,
                                150,
                                900 + eda,
                                150 + eda,
                                outline="#000", fill="#fff", width=1)

if __name__ == '__main__':
    # user vars
    db_path = 'data/20210104_test-20200104-take3.csv'
    audio_path = 'data/20210104_test-20200104-take3.wav'

    # listen to sync audio track
    # for when you are using different FPS than normal
    with_audio_flag = True

    # adjust playback speed
    # 0 = default is original recorded speed, 10 = 10ms
    playback_fps = 0

    # do it ...
    Draw(with_audio_flag, playback_fps)