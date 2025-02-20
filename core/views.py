from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, authenticate, logout
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Q, Sum, F
from django.utils import timezone
from .forms import (
    UserRegistrationForm, FlightSearchForm, HotelSearchForm,
    TourSearchForm, BookingForm, FlightForm, HotelForm, TourForm, BookingStatusForm
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
from .services import (
    send_account_verification_email,
    send_password_reset_email,
    send_booking_confirmation_email,
    send_booking_cancellation_email,
    send_booking_status_update_email,
    send_payment_confirmation_email
)
from django.contrib.sites.shortcuts import get_current_site
from django.urls import reverse
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.utils.encoding import force_bytes
from django.contrib.auth.tokens import default_token_generator
import json

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
            try:
                user = form.save(commit=False)
                user.is_active = False  # User needs to verify email
                user.save()
                
                # Generate verification URL
                current_site = get_current_site(request)
                uid = urlsafe_base64_encode(force_bytes(user.pk))
                token = default_token_generator.make_token(user)
                verification_url = f"http://{current_site.domain}{reverse('verify_email', args=[uid, token])}"
                
                # Send verification email
                try:
                    send_account_verification_email(user, verification_url)
                    messages.success(request, 'Please check your email to verify your account.')
                    return redirect('login')
                except Exception as e:
                    # If email sending fails, delete the user and show error
                    user.delete()
                    messages.error(request, f'Failed to send verification email. Please try again later. Error: {str(e)}')
            except Exception as e:
                messages.error(request, f'Registration failed. Please try again. Error: {str(e)}')
        else:
            # Add form errors to messages
            for field, errors in form.errors.items():
                for error in errors:
                    messages.error(request, f'{field}: {error}')
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
    
    if request.method == 'GET':
        departure_city = request.GET.get('departure_city')
        arrival_city = request.GET.get('arrival_city')
        departure_date = request.GET.get('departure_date')
        return_date = request.GET.get('return_date')
        travel_class = request.GET.get('travel_class')
        passengers = request.GET.get('passengers', 1)
        max_price = request.GET.get('max_price')
        
        # Build the query dynamically
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
        
        # Ensure future flights only
        flights = flights.filter(departure_time__gte=timezone.now())
        
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            # Return JSON response for AJAX requests
            flight_data = []
            for flight in flights:
                flight_data.append({
                    'id': flight.id,
                    'airline': flight.airline,
                    'flight_number': flight.flight_number,
                    'departure_city': flight.departure_city,
                    'arrival_city': flight.arrival_city,
                    'departure_time': flight.departure_time.strftime('%Y-%m-%d %H:%M'),
                    'arrival_time': flight.arrival_time.strftime('%Y-%m-%d %H:%M'),
                    'price': str(flight.price),
                    'available_seats': flight.available_seats,
                    'travel_class': flight.get_travel_class_display()
                })
            return JsonResponse({'flights': flight_data})
    
    context = {
        'form': form,
        'flights': flights,
    }
    return render(request, 'search/flights.html', context)

def get_cities(request):
    """Get autocomplete suggestions for cities"""
    query = request.GET.get('q', '')
    if query:
        # Get unique cities from both departure and arrival cities
        departure_cities = Flight.objects.filter(
            departure_city__icontains=query
        ).values_list('departure_city', flat=True).distinct()
        arrival_cities = Flight.objects.filter(
            arrival_city__icontains=query
        ).values_list('arrival_city', flat=True).distinct()
        
        # Combine and remove duplicates
        cities = list(set(list(departure_cities) + list(arrival_cities)))
        cities.sort()
        return JsonResponse({'cities': cities[:10]})  # Limit to 10 suggestions
    return JsonResponse({'cities': []})

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
            
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            # Return JSON response for AJAX requests
            hotel_data = []
            for hotel in hotels:
                hotel_data.append({
                    'id': hotel.id,
                    'name': hotel.name,
                    'location': hotel.location,
                    'price_per_night': str(hotel.price_per_night),
                    'room_type': hotel.get_room_type_display(),
                    'available_rooms': hotel.available_rooms,
                    'rating': hotel.rating,
                    'amenities': hotel.amenities,
                    'description': hotel.description
                })
            return JsonResponse({'hotels': hotel_data})
    
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
        start_date = form.cleaned_data.get('start_date')
        end_date = form.cleaned_data.get('end_date')
        tour_type = form.cleaned_data.get('tour_type')
        max_price = form.cleaned_data.get('max_price')
        participants = form.cleaned_data.get('participants')
        
        if destination:
            tours = tours.filter(destination__icontains=destination)
        if start_date:
            tours = tours.filter(start_date__gte=start_date)
        if end_date:
            tours = tours.filter(end_date__lte=end_date)
        if tour_type:
            tours = tours.filter(tour_type=tour_type)
        if max_price:
            tours = tours.filter(price__lte=max_price)
        if participants:
            tours = tours.filter(max_participants__gte=F('current_participants') + participants)
            
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            # Return JSON response for AJAX requests
            tour_data = []
            for tour in tours:
                tour_data.append({
                    'id': tour.id,
                    'name': tour.name,
                    'destination': tour.destination,
                    'price': str(tour.price),
                    'duration_days': tour.duration_days,
                    'start_date': tour.start_date.strftime('%Y-%m-%d'),
                    'end_date': tour.end_date.strftime('%Y-%m-%d'),
                    'tour_type': tour.get_tour_type_display(),
                    'max_participants': tour.max_participants,
                    'current_participants': tour.current_participants,
                    'description': tour.description
                })
            return JsonResponse({'tours': tour_data})
    
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
            booking.status = Booking.PENDING
            booking.payment_status = Booking.UNPAID
            booking.save()
            
            # Update available seats
            flight.available_seats -= booking.number_of_guests
            flight.save()
            
            # Send booking confirmation email
            send_booking_confirmation_email(booking)
            
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({
                    'success': True,
                    'booking_id': booking.id,
                    'total_amount': str(booking.total_amount)
                })
            
            messages.success(request, 'Flight booked successfully! Please complete the payment.')
            return redirect('booking_detail', booking_id=booking.id)
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
            
            # Send cancellation email
            send_booking_cancellation_email(booking)
            
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
        form = BookingStatusForm(request.POST, instance=booking)
        if form.is_valid():
            old_status = booking.status
            booking = form.save()
            
            if old_status != booking.status:
                # Send status update email
                send_booking_status_update_email(booking)
            
            messages.success(request, 'Booking status updated successfully.')
            return redirect('booking_detail', booking_id=booking.id)
    
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
            if not user.is_active:
                messages.error(request, 'Please verify your email address before logging in. Check your inbox for the verification link.')
                return render(request, 'registration/login.html')
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

@api_view(['POST'])
@csrf_exempt
def initiate_payment(request, booking_id):
    """
    Endpoint to initiate payment for a booking
    """
    try:
        booking = get_object_or_404(Booking, id=booking_id)
        
        # Return success response with booking details
        return JsonResponse({
            'success': True,
            'message': 'Payment initiated successfully',
            'booking_id': booking.id,
            'amount': float(booking.total_amount)
        })
    except Exception as e:
        return JsonResponse({
            'success': False,
            'message': str(e)
        }, status=400)

@api_view(['POST'])
@csrf_exempt
def check_payment_status(request, booking_id):
    """
    Endpoint to check payment status
    """
    try:
        booking = get_object_or_404(Booking, id=booking_id)
        
        return JsonResponse({
            'success': True,
            'status': booking.payment_status,
            'message': 'Payment status retrieved successfully'
        })
    except Exception as e:
        return JsonResponse({
            'success': False,
            'message': str(e)
        }, status=400)

def verify_email(request, uidb64, token):
    try:
        uid = urlsafe_base64_decode(uidb64).decode()
        user = User.objects.get(pk=uid)
    except (TypeError, ValueError, OverflowError, User.DoesNotExist):
        user = None

    if user is not None and default_token_generator.check_token(user, token):
        user.is_active = True
        user.save()
        messages.success(request, 'Your email has been verified. You can now log in.')
        return redirect('login')
    else:
        messages.error(request, 'The verification link is invalid or has expired.')
        return redirect('login')

@login_required
def test_email_services(request):
    if not request.user.is_admin:
        messages.error(request, 'You do not have permission to test email services.')
        return redirect('dashboard')
    
    try:
        # Test verification email
        verification_url = f"http://{get_current_site(request).domain}/verify-email/test/test/"
        send_account_verification_email(request.user, verification_url)
        
        # Create a test booking for other email tests
        test_booking = Booking.objects.filter(user=request.user).first()
        if test_booking:
            # Test booking confirmation email
            send_booking_confirmation_email(test_booking)
            
            # Test booking cancellation email
            send_booking_cancellation_email(test_booking)
            
            # Test booking status update email
            send_booking_status_update_email(test_booking)
            
            # Test payment confirmation email
            send_payment_confirmation_email(test_booking)
            
            messages.success(request, 'All email services tested successfully. Please check your inbox.')
        else:
            messages.warning(request, 'No booking found for email tests. Only verification email was tested.')
        
    except Exception as e:
        messages.error(request, f'Error testing email services: {str(e)}')
    
    return redirect('dashboard')

def test_emails(request):
    """
    Test script to verify all email functionality
    """
    try:
        # 1. Test account verification email
        test_user = User.objects.filter(is_active=True).first()
        if not test_user:
            messages.error(request, 'No active user found for testing emails.')
            return redirect('dashboard')
        
        verification_url = f"http://{get_current_site(request).domain}/verify-email/test/test/"
        send_account_verification_email(test_user, verification_url)
        print(f"✓ Verification email sent to {test_user.email}")
        
        # 2. Test booking-related emails
        test_booking = Booking.objects.filter(user=test_user).first()
        if test_booking:
            # Test booking confirmation
            send_booking_confirmation_email(test_booking)
            print(f"✓ Booking confirmation email sent for booking #{test_booking.id}")
            
            # Test booking cancellation
            send_booking_cancellation_email(test_booking)
            print(f"✓ Booking cancellation email sent for booking #{test_booking.id}")
            
            # Test booking status update
            send_booking_status_update_email(test_booking)
            print(f"✓ Booking status update email sent for booking #{test_booking.id}")
            
            # Test payment confirmation
            send_payment_confirmation_email(test_booking)
            print(f"✓ Payment confirmation email sent for booking #{test_booking.id}")
            
            print("\nAll email tests completed successfully!")
            return JsonResponse({
                'success': True,
                'message': 'All email tests completed successfully. Check your inbox.'
            })
        else:
            return JsonResponse({
                'success': False,
                'message': 'No test booking found. Only verification email was tested.'
            })
            
    except Exception as e:
        print(f"Error testing emails: {str(e)}")
        return JsonResponse({
            'success': False,
            'message': f'Error testing emails: {str(e)}'
        })

@csrf_exempt
def initiate_mpesa_payment(request):
    if request.method == 'POST':
        try:
            # Get the raw request body and parse it
            data = json.loads(request.body)
            phone_number = data.get('phoneNumber')
            amount = data.get('amount')
            order_id = data.get('orderId')

            # Log the received data
            logging.info(f"Received payment request: {data}")

            if not all([phone_number, amount, order_id]):
                missing_fields = [field for field, value in {
                    'phoneNumber': phone_number,
                    'amount': amount,
                    'orderId': order_id
                }.items() if not value]
                return JsonResponse({
                    'error': f'Missing required fields: {", ".join(missing_fields)}',
                    'status': 'error'
                }, status=400)

            try:
                # Forward the request to the MPESA server with correct field names
                mpesa_response = requests.post(
                    'http://localhost:8000/stkpush',
                    json={
                        'phone': phone_number,  # Changed from 'phoneNumber' to 'phone'
                        'amount': float(amount),
                        'orderId': order_id
                    },
                    headers={
                        'Content-Type': 'application/json'
                    },
                    timeout=30
                )

                # Log the response for debugging
                logging.info(f"MPESA Response Status: {mpesa_response.status_code}")
                logging.info(f"MPESA Response Content: {mpesa_response.text}")

                if not mpesa_response.ok:
                    return JsonResponse({
                        'error': 'MPESA service returned an error',
                        'status': 'error'
                    }, status=mpesa_response.status_code)

                try:
                    response_data = mpesa_response.json()
                    return JsonResponse(response_data)
                except json.JSONDecodeError:
                    # If response is not JSON, return the raw text
                    response_text = mpesa_response.text.strip()
                    if response_text:
                        return JsonResponse({
                            'CheckoutRequestID': response_text,
                            'status': 'success'
                        })
                    else:
                        return JsonResponse({
                            'error': 'Invalid response from MPESA service',
                            'status': 'error'
                        }, status=500)

            except requests.exceptions.ConnectionError:
                logging.error("Failed to connect to MPESA server")
                return JsonResponse({
                    'error': 'MPESA service is currently unavailable. Please try again later.',
                    'status': 'error'
                }, status=503)
            except requests.exceptions.Timeout:
                logging.error("MPESA server request timed out")
                return JsonResponse({
                    'error': 'Request timed out. Please try again.',
                    'status': 'error'
                }, status=504)
            except Exception as e:
                logging.error(f"MPESA server error: {str(e)}")
                return JsonResponse({
                    'error': str(e),
                    'status': 'error'
                }, status=500)
        except json.JSONDecodeError as e:
            logging.error(f"Invalid JSON in request: {str(e)}")
            return JsonResponse({
                'error': 'Invalid request data',
                'status': 'error'
            }, status=400)
        except Exception as e:
            logging.error(f"Payment initiation error: {str(e)}")
            return JsonResponse({
                'error': str(e),
                'status': 'error'
            }, status=500)
    return JsonResponse({'error': 'Invalid request method'}, status=405)

@csrf_exempt
def check_mpesa_status(request, checkout_request_id):
    if request.method == 'GET':
        try:
            # Forward the status check to the MPESA server
            try:
                status_response = requests.get(
                    f'http://localhost:8000/status/{checkout_request_id}',
                    timeout=30
                )

                # Log the response for debugging
                logging.info(f"Status Check Response Status: {status_response.status_code}")
                logging.info(f"Status Check Response Content: {status_response.text}")

                try:
                    response_data = status_response.json()
                    return JsonResponse(response_data)
                except json.JSONDecodeError:
                    # If response is not JSON, check if it's a known status
                    status_text = status_response.text.strip().upper()
                    if status_text in ['COMPLETED', 'FAILED', 'PENDING']:
                        return JsonResponse({
                            'status': status_text
                        })
                    else:
                        return JsonResponse({
                            'error': 'Invalid status response',
                            'status': 'error'
                        }, status=500)

            except requests.exceptions.ConnectionError:
                logging.error("Failed to connect to MPESA server for status check")
                return JsonResponse({
                    'error': 'MPESA service is currently unavailable. Please try again later.',
                    'status': 'error'
                }, status=503)
            except requests.exceptions.Timeout:
                logging.error("MPESA status check timed out")
                return JsonResponse({
                    'error': 'Status check timed out. Please try again.',
                    'status': 'error'
                }, status=504)
            except Exception as e:
                logging.error(f"MPESA status check error: {str(e)}")
                return JsonResponse({
                    'error': str(e),
                    'status': 'error'
                }, status=500)
        except Exception as e:
            logging.error(f"Status check error: {str(e)}")
            return JsonResponse({
                'error': str(e),
                'status': 'error'
            }, status=400)
    return JsonResponse({'error': 'Invalid request method'}, status=405)