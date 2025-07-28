import os
import numpy as np
from PIL import Image
import tensorflow as tf

os.environ["TF_CPP_MIN_LOG_LEVEL"] = "3"  # минимальный лог
tf.config.set_visible_devices([], 'GPU')  # отключаем GPU

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
TFLITE_MODEL_PATH = os.path.join(BASE_DIR, "passport_model.tflite")

# Загружаем TFLite модель
interpreter = tf.lite.Interpreter(model_path=TFLITE_MODEL_PATH)
interpreter.allocate_tensors()
input_details = interpreter.get_input_details()
output_details = interpreter.get_output_details()

class_indices = {'back': 0, 'face': 1, 'front': 2}
class_names = {v: k for k, v in class_indices.items()}

def predict_passport_photo(image_file, expected_type=None, return_reason=False, confidence_threshold=0.7):
    try:
        img = Image.open(image_file)
        img = img.convert('RGB').resize((224, 224))
        img_array = np.array(img, dtype=np.float32) / 255.0
    except Exception as e:
        msg = f"❌ Ошибка при обработке изображения: {e}"
        return (False, msg) if return_reason else False

    if img_array.shape != (224, 224, 3):
        msg = f"❌ Неверная форма: {img_array.shape}"
        return (False, msg) if return_reason else False

    img_array = img_array.reshape((1, 224, 224, 3))

    interpreter.set_tensor(input_details[0]['index'], img_array)
    interpreter.invoke()
    prediction = interpreter.get_tensor(output_details[0]['index'])[0]

    predicted_class = int(np.argmax(prediction))
    predicted_label = class_names[predicted_class]
    confidence = prediction[predicted_class]

    if expected_type:
        expected_class = class_indices.get(expected_type, -1)
        if predicted_class != expected_class:
            msg = f"🔁 Ожидался: {expected_type}, а получен: {predicted_label}"
            return (False, msg) if return_reason else False
        if confidence < confidence_threshold:
            msg = f"⚠️ Слабая уверенность ({confidence:.2f}) для {expected_type}"
            return (False, msg) if return_reason else False
        return (True, None) if return_reason else True

    return (predicted_label, None) if return_reason else predicted_label
