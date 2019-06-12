from __future__ import absolute_import, division, print_function

import pathlib

import matplotlib.pyplot as plt
import pandas as pd
import seaborn as sns

import tensorflow as tf
from tensorflow import keras
from tensorflow.keras import layers
import tensorflow as tf

print(tf.__version__)

dataset_path = '/Users/jameskim/Develop/Personal/apartment-auction-model/text_processor/output.tsv'

column_names = [
    'filename', 'auction_date_year', 'auction_date_day',
    'addr_1', 'addr_2', 'addr_3', 'floor',
    'bundled_item_count', 'min_price', 'area', 'sale_category', 'debt',
    'received_year', 'received_day',
    'auction_fail_count', 'winning_bid',
    'valuation_estate', 'valuation_building',
    'renter_deposit', 'renter_fee',
    'env_slope_tilted', 'env_slope_flat', 'env_shape_square', 'env_shape_odd',
    'evn_hanriver', 'env_accessible', 'env_complex', 'env_transportation',
    'env_scale', 'env_commerce', 'env_education', 'env_park', 'env_public_facility', 'env_hospital', 'env_religion',
    'env_farm', 'env_military', 'env_elevator', 'env_security', ]

raw_dataset = pd.read_csv(dataset_path, names=column_names, sep="\t", na_values="?", skiprows=[0])

dataset = raw_dataset.copy()
print(dataset.tail())

dataset.pop('filename')
dataset.pop('addr_1')  # Change this to Categorical vocabulary column
dataset.pop('addr_2')  # Change this to Categorical vocabulary column
dataset.pop('addr_3')  # Change this to Categorical vocabulary column
dataset = dataset.dropna()
train_dataset = dataset.sample(frac=0.8, random_state=0)
test_dataset = dataset.drop(train_dataset.index)

train_stats = train_dataset.describe()
train_stats.pop('winning_bid')
train_stats = train_stats.transpose()
print(train_stats)

train_labels = train_dataset.pop('winning_bid')
test_labels = test_dataset.pop('winning_bid')


def norm(x):
    return (x - train_stats['mean']) / train_stats['std']


normed_train_data = norm(train_dataset)
normed_test_data = norm(test_dataset)


def build_model():
    model = keras.Sequential([
        layers.Dense(64, activation=tf.nn.relu, input_shape=[len(train_dataset.keys())]),
        layers.Dense(64, activation=tf.nn.relu),
        layers.Dense(1)
    ])

    optimizer = tf.keras.optimizers.RMSprop(0.001)

    model.compile(loss='mean_squared_error',
                  optimizer=optimizer,
                  metrics=['mean_absolute_error', 'mean_squared_error'])
    return model


model = build_model()
model.summary()

example_batch = normed_train_data[:10]
example_result = model.predict(example_batch)
example_result


# Display training progress by printing a single dot for each completed epoch
class PrintDot(keras.callbacks.Callback):
    def on_epoch_end(self, epoch, logs):
        if epoch % 100 == 0: print('')
        print('.', end='')


EPOCHS = 1000

history = model.fit(
    normed_train_data, train_labels,
    epochs=EPOCHS, validation_split=0.2, verbose=0,
    callbacks=[PrintDot()])

hist = pd.DataFrame(history.history)
hist['epoch'] = history.epoch
print(hist.tail())


def plot_history(history):
    hist = pd.DataFrame(history.history)
    hist['epoch'] = history.epoch

    plt.figure()
    plt.xlabel('Epoch')
    plt.ylabel('Mean Abs Error [MPG]')
    plt.plot(hist['epoch'], hist['mean_absolute_error'],
             label='Train Error')
    plt.plot(hist['epoch'], hist['val_mean_absolute_error'],
             label='Val Error')
    plt.ylim([0, 5])
    plt.legend()

    plt.figure()
    plt.xlabel('Epoch')
    plt.ylabel('Mean Square Error [$MPG^2$]')
    plt.plot(hist['epoch'], hist['mean_squared_error'],
             label='Train Error')
    plt.plot(hist['epoch'], hist['val_mean_squared_error'],
             label='Val Error')
    plt.ylim([0, 20])
    plt.legend()
    plt.show()


plot_history(history)

model = build_model()

# The patience parameter is the amount of epochs to check for improvement
early_stop = keras.callbacks.EarlyStopping(monitor='val_loss', patience=10)

history = model.fit(normed_train_data, train_labels, epochs=EPOCHS,
                    validation_split=0.2, verbose=0, callbacks=[early_stop, PrintDot()])

plot_history(history)

loss, mae, mse = model.evaluate(normed_test_data, test_labels, verbose=0)

print("Testing set Mean Abs Error: {:5.2f} MPG".format(mae))
