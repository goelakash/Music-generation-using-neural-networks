#!/usr/bin/env python2
import os
import pprint

import numpy as np
from keras.models import Sequential, model_from_json
from keras.layers.recurrent import LSTM
from keras.layers.core import Dense, Dropout

from process_midi import midi_to_sequence, sequence_to_midi


def load_data():
    state_matrix = []
    for subdir, dirs, files in os.walk('music'):
        for file in files:
            print 'Loading "' + file + '" ...\n'
            file_path = os.path.join(subdir, file)
            state_matrix.extend(midi_to_sequence(file_path)[0])
    return state_matrix


def preprocess_data(state_matrix, prime_size):
    X = []
    Y = []
    step_size = 10
    for i in xrange(0, len(state_matrix) - prime_size, step_size):
        data_point_x = state_matrix[i: i + prime_size]
        data_point_y = state_matrix[i + prime_size]
        X.append(data_point_x)
        Y.append(data_point_y)
    return X, Y

model_arch_path = 'model_save/arch.json'
model_weights_path = 'model_save/weights.h5'


def save_model(model):
    json_string = model.to_json()
    open(model_arch_path, 'w').write(json_string)
    model.save_weights(model_weights_path)


def load_model():
    model = model_from_json(open(model_arch_path).read())
    model.load_weights(model_weights_path)
    return model


def main():
    print 'Loading data ...\n'
    state_matrix = load_data()
    # print len(state_matrix)
    prime_size = 50
    print 'Preprocessing data ...\n'
    X, Y = preprocess_data(state_matrix, prime_size)
    # print len(X), len(Y)
    X, Y = np.array(X), np.array(Y)
    print X.shape, Y.shape

    if os.path.exists('model_save'):
        print 'Loading model ...\n'
        model = load_model()
    else:
        print 'Building model ...\n'
        model = Sequential()
        print 'Adding layer 1 ...\n'
        model.add(LSTM(X.shape[2], input_shape=(
            X.shape[1], X.shape[2]), return_sequences=True))
        model.add(Dropout(0.2))
        print 'Adding layer 2 ...\n'
        model.add(LSTM(X.shape[2] * 2))
        model.add(Dropout(0.2))
        print 'Adding layer 3 ...\n'
        model.add(Dense(X.shape[2]))
        model.add(Dropout(0.2))

    print 'Compiling model ...\n'
    model.compile(loss='mean_squared_error',
                  optimizer="rmsprop", metrics=['accuracy'])

    if not os.path.exists('model_save'):
        os.system('mkdir -p model_save')

        print 'Training model ...\n'
        model.fit(X, Y, validation_split=0.2)

        print 'Saving model ...\n'
        save_model(model)

    print 'Predicting ...\n'
    predictions = model.predict(X, batch_size=32, verbose=1)

    print predictions.shape
    print 'Post-processing predictions ...\n'
    predictions = predictions.astype(int).clip(min=0)
    predictions = predictions.tolist()

    print 'Writing to output file ...\n'
    sequence_to_midi(predictions, 'out.mid', (100, None))


if __name__ == '__main__':
    main()