from django.contrib.auth.models import AbstractUser
from django.db import models
from django.utils import timezone

class User(AbstractUser):
    TRAVELER = 'traveler'
    ADMIN = 'admin'
    
    ROLE_CHOICES = [
        (TRAVELER, 'Traveler'),
        (ADMIN, 'Admin'),
    ]

    STATUS_CHOICES = [
        ('active', 'Active'),
        ('suspended', 'Suspended'),
        ('deactivated', 'Deactivated'),
    ]
    
    role = models.CharField(
        max_length=10,
        choices=ROLE_CHOICES,
        default=TRAVELER
    )
    status = models.CharField(
        max_length=15,
        choices=STATUS_CHOICES,
        default='active'
    )
    profile_picture = models.ImageField(upload_to='profile_pics/', null=True, blank=True)
    phone_number = models.CharField(max_length=15, null=True, blank=True)
    
    def is_admin(self):
        return self.role == self.ADMIN
    
    def is_traveler(self):
        return self.role == self.TRAVELER

class Flight(models.Model):
    ECONOMY = 'economy'
    BUSINESS = 'business'
    FIRST = 'first'
    
    CLASS_CHOICES = [
        (ECONOMY, 'Economy'),
        (BUSINESS, 'Business'),
        (FIRST, 'First'),
    ]
    
    flight_number = models.CharField(max_length=10)
    airline = models.CharField(max_length=100)
    departure_city = models.CharField(max_length=100)
    arrival_city = models.CharField(max_length=100)
    departure_time = models.DateTimeField()
    arrival_time = models.DateTimeField()
    price = models.DecimalField(max_digits=10, decimal_places=2)
    available_seats = models.IntegerField()
    travel_class = models.CharField(max_length=10, choices=CLASS_CHOICES, default=ECONOMY)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"{self.flight_number} - {self.departure_city} to {self.arrival_city}"
    
    class Meta:
        ordering = ['departure_time']

class Hotel(models.Model):
    STANDARD = 'standard'
    DELUXE = 'deluxe'
    SUITE = 'suite'
    
    ROOM_CHOICES = [
        (STANDARD, 'Standard'),
        (DELUXE, 'Deluxe'),
        (SUITE, 'Suite'),
    ]
    
    name = models.CharField(max_length=200)
    location = models.CharField(max_length=200)
    description = models.TextField()
    price_per_night = models.DecimalField(max_digits=10, decimal_places=2)
    room_type = models.CharField(max_length=10, choices=ROOM_CHOICES, default=STANDARD)
    available_rooms = models.IntegerField()
    amenities = models.TextField()
    rating = models.DecimalField(max_digits=3, decimal_places=1)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"{self.name} - {self.location}"
    
    class Meta:
        ordering = ['-rating']

class HotelImage(models.Model):
    hotel = models.ForeignKey('Hotel', related_name='images', on_delete=models.CASCADE)
    image = models.ImageField(upload_to='hotel_images/')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['created_at']

class Tour(models.Model):
    ADVENTURE = 'adventure'
    CULTURAL = 'cultural'
    BEACH = 'beach'
    CITY = 'city'
    
    TOUR_TYPE_CHOICES = [
        (ADVENTURE, 'Adventure'),
        (CULTURAL, 'Cultural'),
        (BEACH, 'Beach'),
        (CITY, 'City Tours'),
    ]
    
    name = models.CharField(max_length=200)
    destination = models.CharField(max_length=200)
    description = models.TextField()
    duration_days = models.IntegerField()
    price = models.DecimalField(max_digits=10, decimal_places=2)
    tour_type = models.CharField(max_length=10, choices=TOUR_TYPE_CHOICES, default=CULTURAL)
    max_participants = models.IntegerField()
    current_participants = models.IntegerField(default=0)
    start_date = models.DateField()
    end_date = models.DateField()
    included_services = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"{self.name} - {self.destination}"
    
    class Meta:
        ordering = ['start_date']

class TourImage(models.Model):
    tour = models.ForeignKey('Tour', related_name='images', on_delete=models.CASCADE)
    image = models.ImageField(upload_to='tour_images/')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['created_at']

class Booking(models.Model):
    PENDING = 'pending'
    CONFIRMED = 'confirmed'
    CANCELLED = 'cancelled'
    COMPLETED = 'completed'
    
    STATUS_CHOICES = [
        (PENDING, 'Pending'),
        (CONFIRMED, 'Confirmed'),
        (CANCELLED, 'Cancelled'),
        (COMPLETED, 'Completed'),
    ]
    
    UNPAID = 'unpaid'
    PAID = 'paid'
    REFUNDED = 'refunded'
    
    PAYMENT_STATUS_CHOICES = [
        (UNPAID, 'Unpaid'),
        (PAID, 'Paid'),
        (REFUNDED, 'Refunded'),
    ]
    
    FLIGHT = 'flight'
    HOTEL = 'hotel'
    TOUR = 'tour'
    
    BOOKING_TYPE_CHOICES = [
        (FLIGHT, 'Flight'),
        (HOTEL, 'Hotel'),
        (TOUR, 'Tour'),
    ]
    
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    booking_type = models.CharField(max_length=10, choices=BOOKING_TYPE_CHOICES)
    flight = models.ForeignKey(Flight, on_delete=models.SET_NULL, null=True, blank=True)
    hotel = models.ForeignKey(Hotel, on_delete=models.SET_NULL, null=True, blank=True)
    tour = models.ForeignKey(Tour, on_delete=models.SET_NULL, null=True, blank=True)
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default=PENDING)
    payment_status = models.CharField(max_length=10, choices=PAYMENT_STATUS_CHOICES, default=UNPAID)
    total_amount = models.DecimalField(max_digits=10, decimal_places=2)
    booking_date = models.DateTimeField(auto_now_add=True)
    check_in_date = models.DateField(null=True, blank=True)
    check_out_date = models.DateField(null=True, blank=True)
    number_of_guests = models.IntegerField(default=1)
    special_requests = models.TextField(blank=True)
    payment_method = models.CharField(max_length=50, blank=True)
    transaction_id = models.CharField(max_length=100, blank=True)
    
    def __str__(self):
        return f"{self.booking_type} booking by {self.user.username}"
    
    def save(self, *args, **kwargs):
        if not self.booking_date:
            self.booking_date = timezone.now()
        super().save(*args, **kwargs)
    
    class Meta:
        ordering = ['-booking_date'] 