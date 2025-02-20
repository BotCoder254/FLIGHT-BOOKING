// MPESA Payment Handler
class MpesaPayment {
    constructor() {
        this.currentBookingId = null;
        this.currentBookingType = null;
        this.pollInterval = null;
    }

    async initializePayment(amount, bookingId, bookingType) {
        this.currentBookingId = bookingId;
        this.currentBookingType = bookingType;
        
        const phoneNumber = document.getElementById('phoneNumber').value;
        const paymentStatus = document.getElementById('paymentStatus');
        const paymentError = document.getElementById('paymentError');
        const confirmButton = document.getElementById('confirmPayment');

        if (!phoneNumber.match(/^254[0-9]{9}$/)) {
            this.showError('Please enter a valid MPESA phone number (Format: 254XXXXXXXXX)');
            return;
        }

        try {
            // Show loading state
            paymentStatus.classList.remove('hidden');
            paymentError.classList.add('hidden');
            confirmButton.disabled = true;

            // Create booking first
            const bookingResponse = await this.createBooking();
            if (!bookingResponse.success) {
                throw new Error(bookingResponse.message || 'Failed to create booking');
            }

            // Initiate MPESA payment
            const response = await fetch('/api/mpesa/stkpush/', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': document.querySelector('[name=csrfmiddlewaretoken]').value
                },
                body: JSON.stringify({
                    phone_number: phoneNumber,
                    amount: amount,
                    orderId: bookingResponse.booking_id
                })
            });

            const data = await response.json();
            if (data.success) {
                this.startPolling(data.checkout_request_id);
            } else {
                throw new Error(data.message || 'Failed to initiate payment');
            }
        } catch (error) {
            this.handleError(error);
        }
    }

    async createBooking() {
        const form = document.getElementById('bookingForm');
        const formData = new FormData(form);
        
        try {
            const response = await fetch(window.location.href, {
                method: 'POST',
                body: formData,
                headers: {
                    'X-Requested-With': 'XMLHttpRequest'
                }
            });
            return await response.json();
        } catch (error) {
            throw new Error('Failed to create booking: ' + error.message);
        }
    }

    startPolling(checkoutRequestId) {
        this.pollInterval = setInterval(async () => {
            try {
                const response = await fetch(`/api/mpesa/query/${checkoutRequestId}/`);
                const data = await response.json();

                if (data.success) {
                    this.stopPolling();
                    window.location.href = `/bookings/${this.currentBookingId}/confirmation/`;
                } else if (data.status === 'CANCELLED') {
                    throw new Error('Payment was cancelled');
                }
                // Continue polling for pending status
            } catch (error) {
                this.handleError(error);
            }
        }, 5000); // Poll every 5 seconds
    }

    stopPolling() {
        if (this.pollInterval) {
            clearInterval(this.pollInterval);
            this.pollInterval = null;
        }
    }

    showError(message) {
        const paymentError = document.getElementById('paymentError');
        paymentError.textContent = message;
        paymentError.classList.remove('hidden');
    }

    handleError(error) {
        this.stopPolling();
        const paymentStatus = document.getElementById('paymentStatus');
        paymentStatus.classList.add('hidden');
        this.showError(error.message || 'An error occurred. Please try again.');
        document.getElementById('confirmPayment').disabled = false;
    }

    closeModal() {
        const modal = document.getElementById('paymentModal');
        const paymentStatus = document.getElementById('paymentStatus');
        const paymentError = document.getElementById('paymentError');
        
        modal.classList.add('hidden');
        paymentStatus.classList.add('hidden');
        paymentError.classList.add('hidden');
        document.getElementById('phoneNumber').value = '';
        this.stopPolling();
    }
}

// Initialize payment handler
const mpesaPayment = new MpesaPayment();

// Export for use in other files
window.mpesaPayment = mpesaPayment; 