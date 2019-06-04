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

raw_dataset = pd.read_csv(dataset_path, names=column_names, sep="\t", skiprows=[0])

dataset = raw_dataset.copy()
print(dataset.tail())

dataset.pop('filename')
dataset.pop('addr_1')
dataset.pop('addr_2')
dataset.pop('addr_3')
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
