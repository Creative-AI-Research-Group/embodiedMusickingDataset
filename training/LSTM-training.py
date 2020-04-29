""" thank you https://machinelearningmastery.com/multivariate-time-series-forecasting-lstms-keras/"""

from math import sqrt
from numpy import concatenate
from matplotlib import pyplot
from pandas import read_csv
from pandas import DataFrame
from pandas import concat
from sklearn.preprocessing import MinMaxScaler
from sklearn.preprocessing import LabelEncoder
from sklearn.metrics import mean_squared_error
from keras.models import Sequential
from keras.layers import Dense
from keras.layers import LSTM

# proto dataset is seq_id; limb; x, y, z; FFt freq, amp
# amplitude is operation input X, with xyz  the predicted output (the embodied action)

"""predict next step of amp given current conditions of xyz, freq and amp"""

    # load the dataset
df = read_csv('../data/raw_phase1_dataset.csv', header=None)
col_name = ['id', 'limb', 'x', 'y', 'z', 'freq', 'amp']
df.columns = col_name
    # apply filter function
    # A) just the features we want
df = df.filter(['limb', 'x', 'y', 'z', 'freq', 'amp'])
    # B) all rows with amp values greater than 0.1 (i.e. has a sound) & freq below 2500
df = df[df['amp'] > 0.1]
df = df[df['freq'] < 2500]
    # C) only "body" data
df = df[df['limb'] == '/Hand_Right']
df = df.filter(['x', 'y', 'z', 'freq', 'amp'])
print (df)

#print out data
values = df.values
# specify columns to plot
groups = [0, 1, 2, 3, 4]
i = 1
# plot each column
pyplot.figure()
for group in groups:
    pyplot.subplot(len(groups), 1, i)
    pyplot.plot(values[:, group])
    pyplot.title(df.columns[group], y=0.5, loc='right')
    i += 1
pyplot.show()

# LSTM Data Preparation

# convert series to supervised learning
def series_to_supervised(data, n_in=1, n_out=1, dropnan=True):
    n_vars = 1 if type(data) is list else data.shape[1]
    df = DataFrame(data)
    cols, names = list(), list()
    # input sequence (t-n, ... t-1)
    for i in range(n_in, 0, -1):
        cols.append(df.shift(i))
        names += [('var%d(t-%d)' % (j+1, i)) for j in range(n_vars)]
    # forecast sequence (t, t+1, ... t+n)
    for i in range(0, n_out):
        cols.append(df.shift(-i))
        if i == 0:
            names += [('var%d(t)' % (j+1)) for j in range(n_vars)]
        else:
            names += [('var%d(t+%d)' % (j+1, i)) for j in range(n_vars)]
    # put it all together
    agg = concat(cols, axis=1)
    agg.columns = names
    # drop rows with NaN values
    if dropnan:
        agg.dropna(inplace=True)
    return agg

# label encode FREQ as integer
# integer encode direction
encoder = LabelEncoder()
values[:, 3] = encoder.fit_transform(values[:, 3])
# ensure all data is float
values = values.astype('float32')
# normalize features
scaler = MinMaxScaler(feature_range=(0, 1))
scaled = scaler.fit_transform(values)
# frame as supervised learning
reframed = series_to_supervised(scaled, 1, 1)
# drop columns we don't want to predict
reframed.drop(reframed.columns[[5, 6, 7, 8, 9]], axis=1, inplace=True)
print(reframed.head())


# split into train and test sets
values = reframed.values
n_train_data = int(len(values) * 0.8) # test last 20%
print (n_train_data)

train = values[:n_train_data, :]
test = values[n_train_data:, :]
# split into input and outputs
train_X, train_y = train[:, :-1], train[:, -1]
test_X, test_y = test[:, :-1], test[:, -1]

# reshape input to be 3D [samples, timesteps, features]
train_X = train_X.reshape((train_X.shape[0], 1, train_X.shape[1]))
test_X = test_X.reshape((test_X.shape[0], 1, test_X.shape[1]))
print(train_X.shape, train_y.shape, test_X.shape, test_y.shape)

# design network
model = Sequential()
model.add(LSTM(50, input_shape=(train_X.shape[1], train_X.shape[2])))
model.add(Dense(1))
model.compile(loss='mae', optimizer='adam')
# fit network
history = model.fit(train_X, train_y, epochs=1000, batch_size=72, validation_data=(test_X, test_y), verbose=2, shuffle=False)
# plot history
pyplot.plot(history.history['loss'], label='train')
pyplot.plot(history.history['val_loss'], label='test')
pyplot.legend()
pyplot.show()

model.save('../data/LSTM-RH_model.h5')
print ('saved')


