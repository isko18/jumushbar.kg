import os
import time
import logging
from celery import shared_task
from django.contrib.auth import get_user_model
from core.passport_classifier.utils import predict_passport_photo

logger = logging.getLogger(__name__)

@shared_task(bind=True)
def validate_passport_images_task(self, user_id, selfie_path, front_path, back_path):
    try:
        logger.info(f"🚀 [Task {self.request.id}] Старт валидации для User #{user_id}")
        User = get_user_model()
        user = User.objects.get(pk=user_id)

        def validate_photo(path, label):
            logger.info(f"🔍 [{label.upper()}] Проверка начата. Путь: {path}")
            if not os.path.exists(path):
                raise FileNotFoundError(f"[{label.upper()}] Файл не найден: {path}")

            start = time.perf_counter()
            ok, reason = predict_passport_photo(path, expected_type=label, return_reason=True)
            elapsed = time.perf_counter() - start
            logger.info(f"✅ [{label.upper()}] Результат: {ok}, Причина: {reason}, Время: {elapsed:.2f} сек.")
            return ok, reason

        # Валидация каждого изображения
        face_ok, face_msg = validate_photo(selfie_path, "face")
        front_ok, front_msg = validate_photo(front_path, "front")
        back_ok, back_msg = validate_photo(back_path, "back")

        # Определение результата
        all_passed = all([face_ok, front_ok, back_ok])
        user.passport_status = "validated" if all_passed else "rejected"

        # ✅ Добавляем флаг верификации
        user.is_verified = all_passed

        user.save()
        logger.info(f"🎯 [User #{user_id}] Итоговый статус: {user.passport_status}, is_verified={user.is_verified}")

        # Вернуть краткое резюме
        return {
            "user_id": user_id,
            "status": user.passport_status,
            "results": {
                "selfie": {"ok": face_ok, "msg": face_msg},
                "front": {"ok": front_ok, "msg": front_msg},
                "back": {"ok": back_ok, "msg": back_msg},
            }
        }

    except Exception as e:
        logger.exception(f"💥 Ошибка при валидации паспортов для User #{user_id}: {e}")
        return {
            "user_id": user_id,
            "error": str(e),
            "status": "failed"
        }
