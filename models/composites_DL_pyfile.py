# ## Deep Learning to find the response of a Ballistic Composite

# #### Imports needed for DL and handling of data


import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

# Make numpy values easier to read.
np.set_printoptions(precision=3, suppress=True)

import tensorflow as tf
from tensorflow.keras import layers
from tensorflow.keras.layers.experimental import preprocessing


# #### Reading of CSV file with all pre-calculated data for composites


composites_data = pd.read_csv("./data/all_data_2.csv")
composites_data.drop(composites_data.iloc[:, 0:12], inplace = True, axis = 1)
composites_data.drop(composites_data.iloc[:, 6:12], inplace = True, axis = 1)
composites_data.drop(composites_data.iloc[:, 12:-1], inplace = True, axis = 1)
composites_data.drop(["L2_sf_t", "L2_sf_c", "L2_rel", "L4_E", "L4_rho", "L4_sf_t", "L4_sf_c", "L4_rel", "L2_rho"], inplace=True, axis=1)
composites_data.head()


# #### Pre-processing of data and definition of the Model to train


from tensorflow.keras.optimizers import SGD, Adam
from tensorflow.keras.utils import to_categorical, normalize

#Split data into training and testing data
train_data = composites_data.sample(frac=0.8, random_state=123)
test_data = composites_data.drop(train_data.index)

#As all data is numeric, we can create a numpy array for all the x features (to make the operations faster) and we 
#can manually create the label y vector
def get_numpy(data):
    data_features = data.copy()
    data_labels = np.array(data_features.pop('Y'))
    data_features = np.array(data_features)
    return data_features, data_labels

comp_features_train, comp_labels_train = get_numpy(train_data)
comp_features_test, comp_labels_test = get_numpy(test_data)

#As every column doesn't have the same range and scale, it's useful to normalize the data using the Normalization layer
#provided by the layers module
comp_features_train = normalize(comp_features_train, axis=0)
comp_features_test = normalize(comp_features_test, axis=0)

#Number of True and False labels in the Test set
print("Percentage of true labels: ",np.sum(comp_labels_test)/len(comp_labels_test))
print("Percentage of false labels: ",np.sum(comp_labels_test == 0)/len(comp_labels_test))


## NN MODEL
#Model -> We will use a network with 1 hidden layer with 64 neurons on it. The final activation function will be a sigmoid
#function (to binary classify the composites), we will use the Adam optimizer algorithm and we will use a Mean Squared Error
#loss function. We keep track of the accuracy during the training process
composites_model = tf.keras.Sequential([
    #layers.LayerNormalization(),
    layers.Dense(256, input_shape=(comp_features_train.shape[1],), activation="relu"),
    layers.Dense(128, activation="relu"),
    layers.Dense(64, activation="relu"),
    layers.Dense(2, activation="softmax")
])

opt = Adam(learning_rate=0.003)
composites_model.compile(loss = "sparse_categorical_crossentropy",
                           optimizer = opt, metrics=["accuracy"])
composites_model.summary()

# Define a Callback class that stops training once accuracy reaches 99.9%
class myCallback(tf.keras.callbacks.Callback):
    def on_epoch_end(self, epoch, logs={}):
        if(logs.get('accuracy')>0.95):
            print("\nReached 99.9% accuracy so cancelling training!")
            self.model.stop_training = True


# #### Model fit with training data


#For training, 20 epochs will be used and callback is used to stop training when a given accuracy is reached (99.9%)
callbacks = myCallback()
history = composites_model.fit(comp_features_train, comp_labels_train, epochs=20, batch_size=32, 
                     callbacks=[callbacks], validation_data=(comp_features_test, comp_labels_test))


y = composites_model.predict(comp_features_test)
print(y)


#Plot history of model!
plt.plot(history.history['accuracy'])
plt.plot(history.history['val_accuracy'])
plt.title('model accuracy')
plt.ylabel('accuracy')
plt.xlabel('epoch')
plt.legend(['train', 'test'], loc='upper left')
plt.show()




