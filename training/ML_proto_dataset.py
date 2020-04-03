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
    df.filter(['x', 'y', 'z', 'freq', 'amp'])
    # B) all rows with amp values greater than 0 (i.e. has a sound)
    df = df[df['amp'] > 0]
    print (df)
    # split into input (X) and output (y) variables
    X = df.iloc[:, 6].values # X = independent variables / input to our model (amplitude)
    y = df.iloc[:, 2:5].values # y = dependent variable/ outputs our model predicts
    return (X, y)

def train(X, y):
    # define the keras model
    model = Sequential()
    model.add(Dense(12, input_dim=3, activation='relu'))
    model.add(Dense(8, activation='relu'))
    model.add(Dense(1, activation='sigmoid'))
    # compile the keras model
    model.compile(loss='binary_crossentropy', optimizer='adam', metrics=['accuracy'])
    # fit the keras model on the dataset.
    # 150 epochs and batch size 400 (so really small)
    model.fit(X, y, epochs=150, batch_size=200)
    # evaluate the keras model
    _, accuracy = model.evaluate(X, y)
    print('Accuracy: %.2f' % (accuracy * 100))
    # so far loss is 60-70% and accuracy is ~ 9% = GIGO but - does it make music?
    model.save('data/model.h5')
    print ('saved')


# --------- programme starts here -----------
# if '__name__' == '__main__':
X, y = prep_dataset()
print('X =', X)
print('y =', y)
mod = train(X, y)
