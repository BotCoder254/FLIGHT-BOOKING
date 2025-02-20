from django.urls import path
from . import views

urlpatterns = [
    path('', views.home, name='home'),
    path('register/', views.register, name='register'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('verify-email/<str:uidb64>/<str:token>/', views.verify_email, name='verify_email'),
    path('dashboard/', views.dashboard, name='dashboard'),
    
    # MPESA Payment URLs
    path('api/mpesa/stkpush/', views.initiate_mpesa_payment, name='initiate_mpesa_payment'),
    path('api/mpesa/query/<str:checkout_request_id>/', views.check_mpesa_status, name='check_mpesa_status'),
    
    # Search URLs
    path('flights/search/', views.search_flights, name='search_flights'),
    path('hotels/search/', views.search_hotels, name='search_hotels'),
    path('tours/search/', views.search_tours, name='search_tours'),
    path('api/cities/', views.get_cities, name='get_cities'),
    
    # Booking URLs
    path('flights/<int:flight_id>/book/', views.book_flight, name='book_flight'),
    path('hotels/<int:hotel_id>/book/', views.book_hotel, name='book_hotel'),
    path('tours/<int:tour_id>/book/', views.book_tour, name='book_tour'),
    path('bookings/<int:booking_id>/confirmation/', views.booking_confirmation, name='booking_confirmation'),
    path('bookings/', views.booking_list, name='booking_list'),
    path('bookings/<int:booking_id>/', views.booking_detail, name='booking_detail'),
    path('bookings/<int:booking_id>/cancel/', views.cancel_booking, name='cancel_booking'),
    path('bookings/<int:booking_id>/update-status/', views.update_booking_status, name='update_booking_status'),
    path('bookings/<int:booking_id>/payment/initiate/', views.initiate_payment, name='initiate_payment'),
    path('bookings/<int:booking_id>/payment/status/', views.check_payment_status, name='check_payment_status'),
    
    # Management URLs
    path('manage/flights/', views.manage_flights, name='manage_flights'),
    path('manage/flights/add/', views.add_flight, name='add_flight'),
    path('manage/flights/<int:flight_id>/edit/', views.edit_flight, name='edit_flight'),
    path('manage/flights/<int:flight_id>/delete/', views.delete_flight, name='delete_flight'),
    
    path('manage/hotels/', views.manage_hotels, name='manage_hotels'),
    path('manage/hotels/add/', views.add_hotel, name='add_hotel'),
    path('manage/hotels/<int:hotel_id>/edit/', views.edit_hotel, name='edit_hotel'),
    path('manage/hotels/<int:hotel_id>/delete/', views.delete_hotel, name='delete_hotel'),
    
    path('manage/tours/', views.manage_tours, name='manage_tours'),
    path('manage/tours/add/', views.add_tour, name='add_tour'),
    path('manage/tours/<int:tour_id>/edit/', views.edit_tour, name='edit_tour'),
    path('manage/tours/<int:tour_id>/delete/', views.delete_tour, name='delete_tour'),
    
    path('manage/users/', views.manage_users, name='manage_users'),
    path('manage/users/<int:user_id>/toggle-status/', views.toggle_user_status, name='toggle_user_status'),
    path('manage/users/<int:user_id>/toggle-role/', views.toggle_user_role, name='toggle_user_role'),
    path('manage/users/<int:user_id>/suspend/', views.suspend_user, name='suspend_user'),
    path('manage/users/<int:user_id>/delete/', views.delete_user, name='delete_user'),
    path('test-email-services/', views.test_email_services, name='test_email_services'),
    path('test-emails/', views.test_emails, name='test_emails'),
] 