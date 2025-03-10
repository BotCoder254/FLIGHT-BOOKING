import stripe
from django.conf import settings
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.shortcuts import render

stripe.api_key = settings.STRIPE_SECRET_KEY

@csrf_exempt
def create_checkout_session(request):
    try:
        data = json.loads(request.body)
        amount = float(data['amount'])

        checkout_session = stripe.checkout.Session.create(
            payment_method_types=['card'],
            line_items=[{
                'price_data': {
                    'currency': 'kes',
                    'unit_amount': int(amount * 100),
                    'product_data': {
                        'name': 'Booking Payment',
                    },
                },
                'quantity': 1,
            }],
            mode='payment',
            success_url=request.build_absolute_uri('/payment/success/'),
            cancel_url=request.build_absolute_uri('/payment/cancel/'),
        )
        return JsonResponse({'id': checkout_session.id})
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=400)

def payment_success(request):
    return render(request, 'booking/success.html')

def payment_cancel(request):
    return render(request, 'booking/cancel.html')

def tour_booking_view(request, tour_id):
    context = {
        'stripe_publishable_key': settings.STRIPE_PUBLISHABLE_KEY,
        # ... other context data ...
    }
    return render(request, 'booking/tour.html', context)

def flight_booking_view(request, flight_id):
    context = {
        'stripe_publishable_key': settings.STRIPE_PUBLISHABLE_KEY,
        # ... other context data ...
    }
    return render(request, 'booking/flight.html', context)

def hotel_booking_view(request, hotel_id):
    context = {
        'stripe_publishable_key': settings.STRIPE_PUBLISHABLE_KEY,
        # ... other context data ...
    }
    return render(request, 'booking/hotel.html', context) 