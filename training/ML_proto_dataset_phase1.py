import pandas as pd
from keras.models import Sequential
from keras.layers import Dense

# proto dataset is seq_id; limb; x, y, z; FFt freq, amp
# amplitude is operation input X, with xyz  the predicted output (the embodied action)

def prep_dataset():
    # load the dataset
    df = pd.read_csv('data/raw_phase1_dataset.csv', header=None)
    col_name = ['id', 'limb', 'x', 'y', 'z', 'freq', 'amp']
    df.columns = col_name
    # apply filter function
    # A) just the features we want
    df = df.filter(['limb', 'x', 'y', 'z', 'freq', 'amp'])
    # B) all rows with amp values greater than 0.1 (i.e. has a sound)
    df = df[df['amp'] > 0.1]
    # C) only "body" data
    df = df[df['limb'] == '/Body']
    print (df)
    # split into input (X) and output (y) variables
    y = df.iloc[:, 1:4].values  # X = independent variables / input to our model
    X = df.iloc[:, -1].values # y = dependent variable/ outputs our model predicts (amplitude)
    return (X, y)

def train(X, y):
    # define the keras model using 3 inputs
    model = Sequential()
    model.add(Dense(12, input_dim=1, activation='relu'))
    model.add(Dense(8, activation='relu'))
    model.add(Dense(3, activation='sigmoid'))
    # compile the keras model
    model.compile(loss='mse', optimizer='adam', metrics=['accuracy'])
    # fit the keras model on the dataset.
    # 150 epochs and batch size 400 (so really small)
    model.fit(X, y, epochs=150, batch_size=200)
    # evaluate the keras model
    _, accuracy = model.evaluate(X, y)
    print('Accuracy: %.2f' % (accuracy * 100))
    model.save('data/new_model.h5')
    print ('saved')



"""so far loss vs accuracy are
input = amp, output= xyz (ABOVE 0.1) (body only) (loss='mse') loss = 2%, accuracy = 100%
input = xyz, output= amp (ABOVE 0) (/Hand_Right only) (loss='mse') loss = 8%, accuracy = 87%
input = xyz, output= amp (ABOVE 0) (/Body only) (loss='mse') loss = 8%, accuracy = 99%
input = xyz, output= amp (ABOVE 0.2) (/Body only) (loss='mse') loss = 6%, accuracy = 16%
input = xyz, output= amp (ABOVE 0.2) (/Body only) loss = 66%, accuracy = 16%
input = xyz, output= amp (body only) loss = 60%, accuracy = 11%
input = xyz, output= amp (all limbs) loss = 70%, accuracy = 9%
input = amp; output = xyz loss = -21169.1751% and accuracy is 0%  

Overall - GIGO but - does it make music?

"""

# --------- programme starts here -----------
if __name__ == '__main__':
    X, y = prep_dataset()
    print('X =', X)
    print('y =', y)
    train(X, y)
