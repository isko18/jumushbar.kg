from rest_framework.views import APIView
from rest_framework.response import Response
from apps.payments.models import Payment
from apps.orders.models import OrderResponse

class FreedomPayCallbackView(APIView):
    def post(self, request):
        payment_id = request.data.get('payment_id')
        status = request.data.get('status')

        payment = Payment.objects.filter(payment_id=payment_id).first()
        if not payment:
            return Response({'detail': 'Платёж не найден'}, status=404)

        payment.status = status
        payment.save()

        if status == 'success':
            # Создай OrderResponse если оплата прошла
            OrderResponse.objects.get_or_create(
                order=payment.order,
                executor=payment.executor,
                defaults={'message': 'Отклик через оплату'}
            )

        return Response({'detail': 'OK'})
