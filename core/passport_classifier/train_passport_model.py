import os
from tensorflow.keras.preprocessing.image import ImageDataGenerator
from tensorflow.keras.applications import MobileNetV2
from tensorflow.keras.models import Model
from tensorflow.keras.layers import Dense, GlobalAveragePooling2D, Dropout
from tensorflow.keras.callbacks import ModelCheckpoint
import tensorflow as tf

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
dataset_dir = os.path.join(BASE_DIR, "dataset")
img_height, img_width = 224, 224
batch_size = 16

# Подготовка данных
datagen = ImageDataGenerator(rescale=1./255, zoom_range=0.2, validation_split=0.2)
train_gen = datagen.flow_from_directory(dataset_dir, target_size=(img_height, img_width),
                                        batch_size=batch_size, class_mode='categorical',
                                        subset='training')
val_gen = datagen.flow_from_directory(dataset_dir, target_size=(img_height, img_width),
                                      batch_size=batch_size, class_mode='categorical',
                                      subset='validation')

# Лёгкая MobileNetV2
base_model = MobileNetV2(input_shape=(img_height, img_width, 3), include_top=False,
                         weights='imagenet', alpha=0.35)  # 👈 здесь ускорение
base_model.trainable = False

# Верхушка
x = base_model.output
x = GlobalAveragePooling2D()(x)
x = Dropout(0.3)(x)
x = Dense(128, activation='relu')(x)
x = Dropout(0.3)(x)
outputs = Dense(len(train_gen.class_indices), activation='softmax')(x)
model = Model(inputs=base_model.input, outputs=outputs)

model.compile(optimizer='adam', loss='categorical_crossentropy', metrics=['accuracy'])

checkpoint_path = os.path.join(BASE_DIR, "passport_model.keras")
model.fit(train_gen, validation_data=val_gen, epochs=10)

# Сохраняем в TFLite (ускоренный инференс)
converter = tf.lite.TFLiteConverter.from_keras_model(model)
tflite_model = converter.convert()
with open(os.path.join(BASE_DIR, "passport_model.tflite"), "wb") as f:
    f.write(tflite_model)
