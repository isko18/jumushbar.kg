import tensorflow as tf
from tensorflow import keras
import os

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
keras_model_path = os.path.join(BASE_DIR, "passport_model.keras")
tflite_model_path = os.path.join(BASE_DIR, "passport_model.tflite")

model = keras.models.load_model(keras_model_path)

converter = tf.lite.TFLiteConverter.from_keras_model(model)
tflite_model = converter.convert()

with open(tflite_model_path, "wb") as f:
    f.write(tflite_model)

print("✅ TFLite модель сохранена:", tflite_model_path)
