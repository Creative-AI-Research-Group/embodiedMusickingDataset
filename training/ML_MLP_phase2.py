import pandas as pd
from keras.models import Sequential
from keras.layers import Dense, Dropout
import numpy as np

# proto dataset is seq_id; limb; x, y, z; FFt freq, amp
# amplitude is operation input X, with xyz  the predicted output (the embodied action)

def main():
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
    # print (df)
    # split into input (X) and output (y) variables
    x_array = df.iloc[:, 1:4].values  # y = dependent variable/ outputs our model predicts (xyz) as numpy arrays
    y_array = df.iloc[:, -1].values # X = independent variables / input to our model (amplitude)
    # calc length of 2D array (rows, columns)
    print (len(y_array))
    y_len = int((len(y_array)/5) * -1)
    x_len = int((len(x_array)/5) * -1)
    print (y_len)
    # extract the last 1/5 for testing and create new arrays
    y_train, y_test = np.split (y_array, [y_len]) # all rows, last 1/5 columns
    x_train, x_test = np.split(x_array, [x_len])
    print (len(y_test))
    print(len(y_train))

    # define the keras model MLP
    model = Sequential()
    model.add(Dense(64, input_dim=3, activation='relu'))
    model.add(Dropout(0.5))
    model.add(Dense(64, activation='relu'))
    model.add(Dropout(0.5))
    model.add(Dense(1, activation='sigmoid'))
    # compile the keras model
    model.compile(loss='binary_crossentropy',
                  optimizer='rmsprop',
                  metrics=['accuracy'])
    # fit the keras model on the dataset.
    model.fit(x_train, y_train,
              epochs=20,
              batch_size=128)
    # evaluate the keras model
    score = model.evaluate(x_test, y_test, batch_size=128)
    # print('Score: %.2f' % (score * 100))
    model.save('data/phase2_body_model.h5')
    print ('saved')

# --------- programme starts here -----------
if __name__ == '__main__':
    main()
