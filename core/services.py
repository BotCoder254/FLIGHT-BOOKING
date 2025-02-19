from django.core.mail import send_mail, EmailMultiAlternatives
from django.template.loader import render_to_string
from django.utils.html import strip_tags
from django.conf import settings

def send_html_email(subject, template_name, context, recipient_list):
    """
    Send HTML email using a template
    """
    html_content = render_to_string(template_name, context)
    text_content = strip_tags(html_content)
    
    msg = EmailMultiAlternatives(
        subject,
        text_content,
        settings.DEFAULT_FROM_EMAIL,
        recipient_list
    )
    msg.attach_alternative(html_content, "text/html")
    return msg.send()

def send_account_verification_email(user, verification_url):
    """
    Send account verification email
    """
    context = {
        'user': user,
        'verification_url': verification_url
    }
    return send_html_email(
        'Verify Your TravelEase Account',
        'emails/account_verification.html',
        context,
        [user.email]
    )

def send_password_reset_email(user, reset_url):
    """
    Send password reset email
    """
    context = {
        'user': user,
        'reset_url': reset_url
    }
    return send_html_email(
        'Reset Your TravelEase Password',
        'emails/password_reset.html',
        context,
        [user.email]
    )

def send_booking_confirmation_email(booking):
    """
    Send booking confirmation email
    """
    context = {
        'booking': booking,
        'user': booking.user
    }
    return send_html_email(
        f'Booking Confirmation - {booking.booking_type.title()} #{booking.id}',
        'emails/booking_confirmation.html',
        context,
        [booking.user.email]
    )

def send_booking_cancellation_email(booking):
    """
    Send booking cancellation email
    """
    context = {
        'booking': booking,
        'user': booking.user
    }
    return send_html_email(
        f'Booking Cancellation - {booking.booking_type.title()} #{booking.id}',
        'emails/booking_cancellation.html',
        context,
        [booking.user.email]
    )

def send_booking_status_update_email(booking):
    """
    Send booking status update email
    """
    context = {
        'booking': booking,
        'user': booking.user
    }
    return send_html_email(
        f'Booking Status Update - {booking.booking_type.title()} #{booking.id}',
        'emails/booking_status_update.html',
        context,
        [booking.user.email]
    )

def send_payment_confirmation_email(booking):
    """
    Send payment confirmation email
    """
    context = {
        'booking': booking,
        'user': booking.user
    }
    return send_html_email(
        f'Payment Confirmation - {booking.booking_type.title()} #{booking.id}',
        'emails/payment_confirmation.html',
        context,
        [booking.user.email]
    ) 