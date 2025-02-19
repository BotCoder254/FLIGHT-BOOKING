from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, authenticate, logout
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Q, Sum, F
from django.utils import timezone
from .forms import (
    UserRegistrationForm, FlightSearchForm, HotelSearchForm,
    TourSearchForm, BookingForm, FlightForm, HotelForm, TourForm
)
from .models import User, Flight, Hotel, Tour, Booking
import base64
import logging
from datetime import datetime
import requests
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from rest_framework.decorators import api_view
from django.conf import settings
from django.template.loader import render_to_string

# Configure logging
logging.basicConfig(level=logging.INFO)

def home(request):
    if request.user.is_authenticated:
        return redirect('dashboard')
    return render(request, 'home.html')

def register(request):
    if request.method == 'POST':
        form = UserRegistrationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            messages.success(request, 'Registration successful!')
            return redirect('dashboard')
        else:
            messages.error(request, 'Please correct the errors below.')
    else:
        form = UserRegistrationForm()
    return render(request, 'registration/register.html', {'form': form})

@login_required
def dashboard(request):
    if request.user.role == User.ADMIN:
        # Get statistics for admin dashboard
        total_users = User.objects.count()
        total_bookings = Booking.objects.count()
        total_revenue = Booking.objects.filter(payment_status=Booking.PAID).aggregate(
            total=Sum('total_amount')
        )['total'] or 0
        active_listings = Flight.objects.count() + Hotel.objects.count() + Tour.objects.count()
        
        # Get recent bookings
        recent_bookings = Booking.objects.select_related('user', 'flight', 'hotel', 'tour')[:10]
        
        context = {
            'total_users': total_users,
            'total_bookings': total_bookings,
            'total_revenue': total_revenue,
            'active_listings': active_listings,
            'recent_bookings': recent_bookings,
        }
        return render(request, 'dashboard/admin_dashboard.html', context)
    
    # For travelers
    user_bookings = Booking.objects.filter(user=request.user).select_related(
        'flight', 'hotel', 'tour'
    ).order_by('-booking_date')
    
    context = {
        'bookings': user_bookings,
    }
    return render(request, 'dashboard/traveler_dashboard.html', context)

def search_flights(request):
    form = FlightSearchForm(request.GET or None)
    flights = Flight.objects.all()
    
    if form.is_valid():
        departure_city = form.cleaned_data.get('departure_city')
        arrival_city = form.cleaned_data.get('arrival_city')
        departure_date = form.cleaned_data.get('departure_date')
        travel_class = form.cleaned_data.get('travel_class')
        passengers = form.cleaned_data.get('passengers')
        max_price = form.cleaned_data.get('max_price')
        
        if departure_city:
            flights = flights.filter(departure_city__icontains=departure_city)
        if arrival_city:
            flights = flights.filter(arrival_city__icontains=arrival_city)
        if departure_date:
            flights = flights.filter(departure_time__date=departure_date)
        if travel_class:
            flights = flights.filter(travel_class=travel_class)
        if passengers:
            flights = flights.filter(available_seats__gte=passengers)
        if max_price:
            flights = flights.filter(price__lte=max_price)
        
        flights = flights.filter(departure_time__gte=timezone.now())
    
    context = {
        'form': form,
        'flights': flights,
    }
    return render(request, 'search/flights.html', context)

def search_hotels(request):
    form = HotelSearchForm(request.GET or None)
    hotels = Hotel.objects.all()
    
    if form.is_valid():
        location = form.cleaned_data.get('location')
        check_in = form.cleaned_data.get('check_in')
        check_out = form.cleaned_data.get('check_out')
        room_type = form.cleaned_data.get('room_type')
        guests = form.cleaned_data.get('guests')
        max_price = form.cleaned_data.get('max_price')
        min_rating = form.cleaned_data.get('min_rating')
        
        if location:
            hotels = hotels.filter(location__icontains=location)
        if room_type:
            hotels = hotels.filter(room_type=room_type)
        if guests:
            hotels = hotels.filter(available_rooms__gte=1)
        if max_price:
            hotels = hotels.filter(price_per_night__lte=max_price)
        if min_rating:
            hotels = hotels.filter(rating__gte=min_rating)
    
    context = {
        'form': form,
        'hotels': hotels,
    }
    return render(request, 'search/hotels.html', context)

def search_tours(request):
    form = TourSearchForm(request.GET or None)
    tours = Tour.objects.all()
    
    if form.is_valid():
        destination = form.cleaned_data.get('destination')
        tour_type = form.cleaned_data.get('tour_type')
        start_date = form.cleaned_data.get('start_date')
        max_duration = form.cleaned_data.get('max_duration')
        max_price = form.cleaned_data.get('max_price')
        participants = form.cleaned_data.get('participants')
        
        if destination:
            tours = tours.filter(destination__icontains=destination)
        if tour_type:
            tours = tours.filter(tour_type=tour_type)
        if start_date:
            tours = tours.filter(start_date__gte=start_date)
        if max_duration:
            tours = tours.filter(duration_days__lte=max_duration)
        if max_price:
            tours = tours.filter(price__lte=max_price)
        if participants:
            available_spots = Q(max_participants__gt=F('current_participants') + participants)
            tours = tours.filter(available_spots)
        
        tours = tours.filter(start_date__gte=timezone.now().date())
    
    context = {
        'form': form,
        'tours': tours,
    }
    return render(request, 'search/tours.html', context)

@login_required
def book_flight(request, flight_id):
    flight = get_object_or_404(Flight, id=flight_id)
    
    if request.method == 'POST':
        form = BookingForm(request.POST)
        if form.is_valid():
            booking = form.save(commit=False)
            booking.user = request.user
            booking.booking_type = Booking.FLIGHT
            booking.flight = flight
            booking.total_amount = flight.price * booking.number_of_guests
            booking.status = Booking.PENDING  # Keep as PENDING until payment
            booking.payment_status = Booking.UNPAID
            booking.save()
            
            # Update available seats
            flight.available_seats -= booking.number_of_guests
            flight.save()
            
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({
                    'success': True,
                    'booking_id': booking.id,
                    'total_amount': str(booking.total_amount)
                })
            
            messages.success(request, 'Flight booked successfully! Please complete the payment.')
            return redirect('booking_detail', booking_id=booking.id)
        else:
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({
                    'success': False,
                    'message': 'Invalid form data. Please check your input.'
                })
    else:
        form = BookingForm()
    
    context = {
        'form': form,
        'flight': flight,
    }
    return render(request, 'booking/flight.html', context)

@login_required
def book_hotel(request, hotel_id):
    hotel = get_object_or_404(Hotel, id=hotel_id)
    
    if request.method == 'POST':
        form = BookingForm(request.POST)
        if form.is_valid():
            booking = form.save(commit=False)
            booking.user = request.user
            booking.booking_type = Booking.HOTEL
            booking.hotel = hotel
            
            # Calculate total amount based on number of nights
            check_in = form.cleaned_data['check_in']
            check_out = form.cleaned_data['check_out']
            nights = (check_out - check_in).days
            booking.total_amount = hotel.price_per_night * nights * booking.number_of_guests
            booking.status = Booking.PENDING  # Keep as PENDING until payment
            booking.payment_status = Booking.UNPAID
            booking.save()
            
            # Update available rooms
            hotel.available_rooms -= 1
            hotel.save()
            
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({
                    'success': True,
                    'booking_id': booking.id,
                    'total_amount': str(booking.total_amount)
                })
            
            messages.success(request, 'Hotel booked successfully! Please complete the payment.')
            return redirect('booking_detail', booking_id=booking.id)
        else:
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({
                    'success': False,
                    'message': 'Invalid form data. Please check your input.'
                })
    else:
        form = BookingForm()
    
    context = {
        'form': form,
        'hotel': hotel,
    }
    return render(request, 'booking/hotel.html', context)

@login_required
def book_tour(request, tour_id):
    tour = get_object_or_404(Tour, id=tour_id)
    
    if request.method == 'POST':
        form = BookingForm(request.POST)
        if form.is_valid():
            booking = form.save(commit=False)
            booking.user = request.user
            booking.booking_type = Booking.TOUR
            booking.tour = tour
            booking.total_amount = tour.price * booking.number_of_guests
            booking.status = Booking.PENDING  # Keep as PENDING until payment
            booking.payment_status = Booking.UNPAID
            booking.save()
            
            # Update current participants
            tour.current_participants += booking.number_of_guests
            tour.save()
            
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({
                    'success': True,
                    'booking_id': booking.id,
                    'total_amount': str(booking.total_amount)
                })
            
            messages.success(request, 'Tour booked successfully! Please complete the payment.')
            return redirect('booking_detail', booking_id=booking.id)
        else:
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({
                    'success': False,
                    'message': 'Invalid form data. Please check your input.'
                })
    else:
        form = BookingForm()
    
    context = {
        'form': form,
        'tour': tour,
    }
    return render(request, 'booking/tour.html', context)

@login_required
def booking_list(request):
    if request.user.is_admin:
        # For admin users, show all paid bookings
        paid_bookings = Booking.objects.filter(payment_status=Booking.PAID)
    else:
        # For regular users, show only their paid bookings
        paid_bookings = Booking.objects.filter(user=request.user, payment_status=Booking.PAID)
    
    context = {
        'paid_bookings': paid_bookings,
    }
    
    # Check if it's an AJAX request for real-time updates
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return JsonResponse({
            'html': render_to_string('booking/booking_list_content.html', context, request=request)
        })
    
    return render(request, 'booking/booking_list.html', context)

@login_required
def booking_detail(request, booking_id):
    booking = get_object_or_404(Booking, id=booking_id)
    
    # Only allow users to view their own bookings unless they're admin
    if not request.user.is_admin and booking.user != request.user:
        messages.error(request, 'You do not have permission to view this booking.')
        return redirect('booking_list')
    
    return render(request, 'booking/booking_detail.html', {'booking': booking})

@login_required
def cancel_booking(request, booking_id):
    booking = get_object_or_404(Booking, id=booking_id)
    
    # Only allow users to cancel their own bookings unless they're admin
    if not request.user.is_admin and booking.user != request.user:
        messages.error(request, 'You do not have permission to cancel this booking.')
        return redirect('booking_list')
    
    if request.method == 'POST':
        if booking.status == Booking.CONFIRMED:
            booking.status = Booking.CANCELLED
            booking.save()
            
            # Return inventory
            if booking.booking_type == Booking.FLIGHT:
                booking.flight.available_seats += booking.number_of_guests
                booking.flight.save()
            elif booking.booking_type == Booking.HOTEL:
                booking.hotel.available_rooms += 1
                booking.hotel.save()
            elif booking.booking_type == Booking.TOUR:
                booking.tour.current_participants -= booking.number_of_guests
                booking.tour.save()
            
            messages.success(request, 'Booking cancelled successfully.')
        else:
            messages.error(request, 'This booking cannot be cancelled.')
    
    return redirect('booking_detail', booking_id=booking.id)

@login_required
def update_booking_status(request, booking_id):
    if not request.user.is_admin:
        messages.error(request, 'You do not have permission to update booking status.')
        return redirect('booking_list')
    
    booking = get_object_or_404(Booking, id=booking_id)
    
    if request.method == 'POST':
        new_status = request.POST.get('status')
        if new_status in dict(Booking.STATUS_CHOICES):
            booking.status = new_status
            booking.save()
            messages.success(request, 'Booking status updated successfully.')
        else:
            messages.error(request, 'Invalid status.')
    
    return redirect('booking_detail', booking_id=booking.id)

@login_required
def booking_confirmation(request, booking_id):
    booking = get_object_or_404(Booking, id=booking_id)
    
    # Only allow users to view their own booking confirmations unless they're admin
    if not request.user.is_admin and booking.user != request.user:
        messages.error(request, 'You do not have permission to view this booking.')
        return redirect('booking_list')
    
    return render(request, 'booking/confirmation.html', {'booking': booking})

def login_view(request):
    if request.user.is_authenticated:
        return redirect('dashboard')
        
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        user = authenticate(request, username=username, password=password)
        
        if user is not None:
            login(request, user)
            next_url = request.GET.get('next', 'dashboard')
            return redirect(next_url)
        else:
            messages.error(request, 'Invalid username or password.')
    
    return render(request, 'registration/login.html')

def logout_view(request):
    logout(request)
    return redirect('home')

@login_required
def manage_flights(request):
    if not request.user.role == 'admin':
        messages.error(request, 'You do not have permission to access this page.')
        return redirect('dashboard')
    flights = Flight.objects.all().order_by('-created_at')
    return render(request, 'dashboard/manage_flights.html', {'flights': flights})

@login_required
def manage_hotels(request):
    if not request.user.role == 'admin':
        messages.error(request, 'You do not have permission to access this page.')
        return redirect('dashboard')
    hotels = Hotel.objects.all().order_by('-created_at')
    return render(request, 'dashboard/manage_hotels.html', {'hotels': hotels})

@login_required
def manage_tours(request):
    if not request.user.role == 'admin':
        messages.error(request, 'You do not have permission to access this page.')
        return redirect('dashboard')
    tours = Tour.objects.all().order_by('-created_at')
    return render(request, 'dashboard/manage_tours.html', {'tours': tours})

@login_required
def manage_users(request):
    if not request.user.role == 'admin':
        messages.error(request, 'You do not have permission to access this page.')
        return redirect('dashboard')
    users = User.objects.all().order_by('-date_joined')
    return render(request, 'dashboard/manage_users.html', {'users': users})

@login_required
def add_flight(request):
    if not request.user.role == 'admin':
        messages.error(request, 'You do not have permission to access this page.')
        return redirect('dashboard')
    if request.method == 'POST':
        form = FlightForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Flight added successfully!')
            return redirect('manage_flights')
    else:
        form = FlightForm()
    return render(request, 'dashboard/flight_form.html', {'form': form, 'action': 'Add'})

@login_required
def edit_flight(request, flight_id):
    if not request.user.role == 'admin':
        messages.error(request, 'You do not have permission to access this page.')
        return redirect('dashboard')
    flight = get_object_or_404(Flight, id=flight_id)
    if request.method == 'POST':
        form = FlightForm(request.POST, instance=flight)
        if form.is_valid():
            form.save()
            messages.success(request, 'Flight updated successfully!')
            return redirect('manage_flights')
    else:
        form = FlightForm(instance=flight)
    return render(request, 'dashboard/flight_form.html', {'form': form, 'action': 'Edit'})

@login_required
def add_hotel(request):
    if request.method == 'POST':
        form = HotelForm(request.POST, request.FILES)
        if form.is_valid():
            hotel = form.save()
            messages.success(request, 'Hotel added successfully.')
            return redirect('manage_hotels')
    else:
        form = HotelForm()
    return render(request, 'dashboard/hotel_form.html', {'form': form, 'action': 'Add'})

@login_required
def edit_hotel(request, hotel_id):
    hotel = get_object_or_404(Hotel, id=hotel_id)
    if request.method == 'POST':
        form = HotelForm(request.POST, request.FILES, instance=hotel)
        if form.is_valid():
            hotel = form.save()
            messages.success(request, 'Hotel updated successfully.')
            return redirect('manage_hotels')
    else:
        form = HotelForm(instance=hotel)
    return render(request, 'dashboard/hotel_form.html', {'form': form, 'action': 'Edit'})

@login_required
def add_tour(request):
    if request.method == 'POST':
        form = TourForm(request.POST, request.FILES)
        if form.is_valid():
            tour = form.save()
            messages.success(request, 'Tour added successfully.')
            return redirect('manage_tours')
    else:
        form = TourForm()
    return render(request, 'dashboard/tour_form.html', {'form': form, 'action': 'Add'})

@login_required
def edit_tour(request, tour_id):
    tour = get_object_or_404(Tour, id=tour_id)
    if request.method == 'POST':
        form = TourForm(request.POST, request.FILES, instance=tour)
        if form.is_valid():
            tour = form.save()
            messages.success(request, 'Tour updated successfully.')
            return redirect('manage_tours')
    else:
        form = TourForm(instance=tour)
    return render(request, 'dashboard/tour_form.html', {'form': form, 'action': 'Edit'})

@login_required
def delete_flight(request, flight_id):
    if not request.user.role == 'admin':
        messages.error(request, 'You do not have permission to access this page.')
        return redirect('dashboard')
    flight = get_object_or_404(Flight, id=flight_id)
    flight.delete()
    messages.success(request, 'Flight deleted successfully!')
    return redirect('manage_flights')

@login_required
def delete_hotel(request, hotel_id):
    if not request.user.role == 'admin':
        messages.error(request, 'You do not have permission to access this page.')
        return redirect('dashboard')
    hotel = get_object_or_404(Hotel, id=hotel_id)
    hotel.delete()
    messages.success(request, 'Hotel deleted successfully!')
    return redirect('manage_hotels')

@login_required
def delete_tour(request, tour_id):
    if not request.user.role == 'admin':
        messages.error(request, 'You do not have permission to access this page.')
        return redirect('dashboard')
    tour = get_object_or_404(Tour, id=tour_id)
    tour.delete()
    messages.success(request, 'Tour deleted successfully!')
    return redirect('manage_tours')

@login_required
def toggle_user_status(request, user_id):
    if not request.user.role == 'admin':
        messages.error(request, 'You do not have permission to perform this action.')
        return redirect('dashboard')
    user = get_object_or_404(User, id=user_id)
    if user.is_superuser:
        messages.error(request, 'Cannot modify superuser status.')
        return redirect('manage_users')
    
    if user.is_active:
        user.is_active = False
        user.status = 'deactivated'
    else:
        user.is_active = True
        user.status = 'active'
    user.save()
    status = 'activated' if user.is_active else 'deactivated'
    messages.success(request, f'User {user.username} has been {status}.')
    return redirect('manage_users')

@login_required
def toggle_user_role(request, user_id):
    if not request.user.role == 'admin':
        messages.error(request, 'You do not have permission to perform this action.')
        return redirect('dashboard')
    user = get_object_or_404(User, id=user_id)
    if user.is_superuser:
        messages.error(request, 'Cannot modify superuser role.')
        return redirect('manage_users')
    user.role = 'traveler' if user.role == 'admin' else 'admin'
    user.save()
    messages.success(request, f'User {user.username} role has been changed to {user.role}.')
    return redirect('manage_users')

@login_required
def suspend_user(request, user_id):
    if not request.user.role == 'admin':
        messages.error(request, 'You do not have permission to perform this action.')
        return redirect('manage_users')
    
    if request.method == 'POST':
        try:
            user = get_object_or_404(User, id=user_id)
            if user.is_superuser:
                messages.error(request, 'Cannot suspend a superuser account.')
            else:
                user.is_active = False
                user.status = 'suspended'
                user.save()
                messages.success(request, f'Account for {user.username} has been suspended.')
        except User.DoesNotExist:
            messages.error(request, 'User not found.')
    
    return redirect('manage_users')

@login_required
def delete_user(request, user_id):
    if not request.user.role == 'admin':
        messages.error(request, 'You do not have permission to perform this action.')
        return redirect('manage_users')
    
    if request.method == 'POST':
        try:
            user = get_object_or_404(User, id=user_id)
            if user.is_superuser:
                messages.error(request, 'Cannot delete a superuser account.')
            else:
                username = user.username
                user.delete()
                messages.success(request, f'Account for {username} has been permanently deleted.')
        except User.DoesNotExist:
            messages.error(request, 'User not found.')
    
    return redirect('manage_users')

def get_mpesa_access_token():
    """Generate M-Pesa OAuth access token."""
    url = "https://api.safaricom.co.ke/oauth/v1/generate?grant_type=client_credentials"
    
    auth_string = f"{settings.MPESA_CONSUMER_KEY}:{settings.MPESA_CONSUMER_SECRET}"
    auth_bytes = auth_string.encode('ascii')
    auth_b64 = base64.b64encode(auth_bytes).decode('ascii')
    
    headers = {
        "Authorization": f"Basic {auth_b64}"
    }
    
    try:
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        return response.json()['access_token']
    except requests.exceptions.RequestException as e:
        logging.error(f"Error getting access token: {str(e)}")
        raise

@api_view(['POST'])
@csrf_exempt
def initiate_payment(request, booking_id):
    try:
        booking = get_object_or_404(Booking, id=booking_id)
        
        # Check if booking is already paid
        if booking.payment_status == Booking.PAID:
            return JsonResponse({
                'ResponseCode': '1',
                'ResponseDescription': 'This booking is already paid'
            })
        
        # Check if there's a pending payment
        if booking.transaction_id:
            return JsonResponse({
                'ResponseCode': '1',
                'ResponseDescription': 'A payment is already in progress for this booking'
            })
        
        # Get phone number from request
        data = request.data
        phone_number = data.get('phone_number', '')
        
        # Validate phone number format (should be 254XXXXXXXXX)
        if not phone_number.startswith('254') or not phone_number.isdigit() or len(phone_number) != 12:
            return JsonResponse({
                'ResponseCode': '1',
                'ResponseDescription': 'Invalid phone number format. Use 254XXXXXXXXX'
            })
        
        # Get M-Pesa access token
        auth_response = requests.get(
            'https://sandbox.safaricom.co.ke/oauth/v1/generate?grant_type=client_credentials',
            auth=(settings.MPESA_CONSUMER_KEY, settings.MPESA_CONSUMER_SECRET)
        )
        
        if auth_response.status_code != 200:
            return JsonResponse({
                'ResponseCode': '1',
                'ResponseDescription': 'Failed to get access token'
            })
        
        access_token = auth_response.json()['access_token']
        
        # Prepare STK Push request
        timestamp = timezone.now().strftime('%Y%m%d%H%M%S')
        password_str = f'{settings.MPESA_SHORTCODE}{settings.MPESA_PASSKEY}{timestamp}'
        password = base64.b64encode(password_str.encode()).decode('utf-8')
        
        stk_push_headers = {
            'Authorization': f'Bearer {access_token}',
            'Content-Type': 'application/json'
        }
        
        stk_push_payload = {
            'BusinessShortCode': settings.MPESA_SHORTCODE,
            'Password': password,
            'Timestamp': timestamp,
            'TransactionType': 'CustomerPayBillOnline',
            'Amount': int(booking.total_amount),
            'PartyA': phone_number,
            'PartyB': settings.MPESA_SHORTCODE,
            'PhoneNumber': phone_number,
            'CallBackURL': settings.MPESA_CALLBACK_URL,
            'AccountReference': f'TravelEase-{booking.id}',
            'TransactionDesc': f'Payment for booking #{booking.id}'
        }
        
        response = requests.post(
            'https://sandbox.safaricom.co.ke/mpesa/stkpush/v1/processrequest',
            json=stk_push_payload,
            headers=stk_push_headers
        )
        
        if response.status_code != 200:
            return JsonResponse({
                'ResponseCode': '1',
                'ResponseDescription': 'Failed to initiate payment'
            })
        
        response_data = response.json()
        
        # Validate response format
        if not response_data.get('CheckoutRequestID'):
            return JsonResponse({
                'ResponseCode': '1',
                'ResponseDescription': 'Invalid response from M-Pesa'
            })
        
        # Save transaction ID but don't change status yet
        booking.transaction_id = response_data['CheckoutRequestID']
        booking.save()
        
        return JsonResponse({
            'ResponseCode': '0',
            'ResponseDescription': 'Success. Request accepted for processing',
            'CheckoutRequestID': response_data['CheckoutRequestID'],
            'CustomerMessage': response_data.get('CustomerMessage', 'Success. Request accepted for processing')
        })
        
    except Exception as e:
        return JsonResponse({
            'ResponseCode': '1',
            'ResponseDescription': str(e)
        }, status=500)

@api_view(['POST'])
@csrf_exempt
def check_payment_status(request, booking_id):
    try:
        booking = get_object_or_404(Booking, id=booking_id)
        
        # Check if there's a transaction ID
        if not booking.transaction_id:
            return JsonResponse({
                'ResponseCode': '1',
                'ResponseDescription': 'No payment initiated for this booking'
            })
        
        # Get M-Pesa access token
        auth_response = requests.get(
            'https://sandbox.safaricom.co.ke/oauth/v1/generate?grant_type=client_credentials',
            auth=(settings.MPESA_CONSUMER_KEY, settings.MPESA_CONSUMER_SECRET)
        )
        
        if auth_response.status_code != 200:
            return JsonResponse({
                'ResponseCode': '1',
                'ResponseDescription': 'Failed to get access token'
            })
        
        access_token = auth_response.json()['access_token']
        
        # Query payment status
        headers = {
            'Authorization': f'Bearer {access_token}'
        }
        
        query_response = requests.post(
            'https://sandbox.safaricom.co.ke/mpesa/stkpushquery/v1/query',
            json={
                'BusinessShortCode': settings.MPESA_SHORTCODE,
                'CheckoutRequestID': booking.transaction_id,
                'Password': settings.MPESA_PASSWORD,
                'Timestamp': timezone.now().strftime('%Y%m%d%H%M%S')
            },
            headers=headers
        )
        
        if query_response.status_code != 200:
            return JsonResponse({
                'ResponseCode': '1',
                'ResponseDescription': 'Failed to query payment status'
            })
        
        result = query_response.json()
        
        if result.get('ResultCode') == '0':
            # Payment successful
            booking.payment_status = Booking.PAID
            booking.status = Booking.CONFIRMED  # Update status to CONFIRMED only after successful payment
            booking.save()
            
            return JsonResponse({
                'ResponseCode': '0',
                'ResponseDescription': 'Payment completed successfully'
            })
        elif result.get('ResultCode') == '1032':
            # Payment cancelled by user
            booking.transaction_id = ''  # Clear transaction ID to allow new payment
            booking.save()
            
            return JsonResponse({
                'ResponseCode': '1',
                'ResponseDescription': 'Payment cancelled by user'
            })
        else:
            return JsonResponse({
                'ResponseCode': '1',
                'ResponseDescription': 'Payment pending or failed'
            })
            
    except Exception as e:
        return JsonResponse({
            'ResponseCode': '1',
            'ResponseDescription': str(e)
        }, status=500) 