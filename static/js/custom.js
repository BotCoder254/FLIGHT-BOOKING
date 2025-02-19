// Initialize AOS animations
document.addEventListener('DOMContentLoaded', function() {
    AOS.init({
        duration: 800,
        easing: 'ease-out',
        once: true
    });
});

// Smooth scroll to sections
document.querySelectorAll('a[href^="#"]').forEach(anchor => {
    anchor.addEventListener('click', function (e) {
        e.preventDefault();
        const target = document.querySelector(this.getAttribute('href'));
        if (target) {
            target.scrollIntoView({
                behavior: 'smooth',
                block: 'start'
            });
        }
    });
});

// Sticky navigation
window.addEventListener('scroll', function() {
    const nav = document.querySelector('nav');
    if (window.scrollY > 100) {
        nav.classList.add('bg-white', 'shadow-lg');
    } else {
        nav.classList.remove('bg-white', 'shadow-lg');
    }
});

// Form validation
function validateForm(form) {
    const inputs = form.querySelectorAll('input[required], select[required], textarea[required]');
    let isValid = true;

    inputs.forEach(input => {
        if (!input.value.trim()) {
            isValid = false;
            input.classList.add('border-red-500');
            
            // Add error message
            const errorMessage = document.createElement('p');
            errorMessage.className = 'text-red-500 text-sm mt-1';
            errorMessage.textContent = 'This field is required';
            
            // Remove existing error message if any
            const existingError = input.parentNode.querySelector('.text-red-500');
            if (existingError) {
                existingError.remove();
            }
            
            input.parentNode.appendChild(errorMessage);
        } else {
            input.classList.remove('border-red-500');
            const errorMessage = input.parentNode.querySelector('.text-red-500');
            if (errorMessage) {
                errorMessage.remove();
            }
        }
    });

    return isValid;
}

// Password strength indicator
function checkPasswordStrength(password) {
    let strength = 0;
    
    // Length check
    if (password.length >= 8) strength += 1;
    
    // Contains lowercase letters
    if (password.match(/[a-z]/)) strength += 1;
    
    // Contains uppercase letters
    if (password.match(/[A-Z]/)) strength += 1;
    
    // Contains numbers
    if (password.match(/[0-9]/)) strength += 1;
    
    // Contains special characters
    if (password.match(/[^a-zA-Z0-9]/)) strength += 1;
    
    return strength;
}

// Update password strength indicator
const passwordInput = document.querySelector('input[type="password"]');
if (passwordInput) {
    passwordInput.addEventListener('input', function() {
        const strength = checkPasswordStrength(this.value);
        const indicator = document.getElementById('password-strength');
        
        if (indicator) {
            // Update indicator color and width based on strength
            indicator.style.width = `${strength * 20}%`;
            
            if (strength <= 2) {
                indicator.className = 'bg-red-500';
            } else if (strength <= 3) {
                indicator.className = 'bg-yellow-500';
            } else {
                indicator.className = 'bg-green-500';
            }
        }
    });
}

// Show/hide password toggle
const passwordToggle = document.querySelector('.password-toggle');
if (passwordToggle) {
    passwordToggle.addEventListener('click', function() {
        const passwordInput = this.previousElementSibling;
        const type = passwordInput.getAttribute('type') === 'password' ? 'text' : 'password';
        passwordInput.setAttribute('type', type);
        
        // Update icon
        const icon = this.querySelector('i');
        icon.className = type === 'password' ? 'fas fa-eye' : 'fas fa-eye-slash';
    });
}

// Form submission loading state
document.querySelectorAll('form').forEach(form => {
    form.addEventListener('submit', function(e) {
        if (validateForm(this)) {
            const submitButton = this.querySelector('button[type="submit"]');
            if (submitButton) {
                // Save original button content
                const originalContent = submitButton.innerHTML;
                
                // Show loading state
                submitButton.innerHTML = '<div class="spinner mr-2"></div>Loading...';
                submitButton.disabled = true;
                
                // Simulate form submission delay (remove in production)
                setTimeout(() => {
                    submitButton.innerHTML = originalContent;
                    submitButton.disabled = false;
                }, 2000);
            }
        } else {
            e.preventDefault();
        }
    });
});

// Notification system
function showNotification(message, type = 'success') {
    const notification = document.createElement('div');
    notification.className = `fixed top-4 right-4 p-4 rounded-lg shadow-lg transform transition-transform duration-300 ease-in-out ${
        type === 'success' ? 'bg-green-500' : 'bg-red-500'
    } text-white`;
    notification.textContent = message;
    
    document.body.appendChild(notification);
    
    // Animate in
    setTimeout(() => {
        notification.style.transform = 'translateX(0)';
    }, 100);
    
    // Remove after 3 seconds
    setTimeout(() => {
        notification.style.transform = 'translateX(100%)';
        setTimeout(() => {
            notification.remove();
        }, 300);
    }, 3000);
}

// Image lazy loading
document.addEventListener('DOMContentLoaded', function() {
    const lazyImages = document.querySelectorAll('img[data-src]');
    
    const imageObserver = new IntersectionObserver((entries, observer) => {
        entries.forEach(entry => {
            if (entry.isIntersecting) {
                const img = entry.target;
                img.src = img.dataset.src;
                img.removeAttribute('data-src');
                observer.unobserve(img);
            }
        });
    });
    
    lazyImages.forEach(img => imageObserver.observe(img));
});

// Flight Search Functionality
let searchTimeout;

function initializeFlightSearch() {
    const departureInput = document.querySelector('input[name="departure_city"]');
    const arrivalInput = document.querySelector('input[name="arrival_city"]');
    const searchForm = document.querySelector('.flight-search-form');

    if (departureInput) {
        setupCityAutocomplete(departureInput);
    }
    if (arrivalInput) {
        setupCityAutocomplete(arrivalInput);
    }
    if (searchForm) {
        setupRealTimeSearch(searchForm);
    }
}

function setupCityAutocomplete(input) {
    const wrapper = document.createElement('div');
    wrapper.className = 'relative';
    input.parentNode.insertBefore(wrapper, input);
    wrapper.appendChild(input);

    const suggestionBox = document.createElement('div');
    suggestionBox.className = 'absolute z-10 w-full bg-white border border-gray-300 rounded-lg mt-1 shadow-lg hidden';
    wrapper.appendChild(suggestionBox);

    input.addEventListener('input', function() {
        clearTimeout(searchTimeout);
        const query = this.value;
        
        if (query.length < 2) {
            suggestionBox.innerHTML = '';
            suggestionBox.classList.add('hidden');
            return;
        }

        searchTimeout = setTimeout(() => {
            fetch(`/api/cities/?q=${encodeURIComponent(query)}`)
                .then(response => response.json())
                .then(data => {
                    suggestionBox.innerHTML = '';
                    if (data.cities.length > 0) {
                        data.cities.forEach(city => {
                            const div = document.createElement('div');
                            div.className = 'px-4 py-2 hover:bg-gray-100 cursor-pointer';
                            div.textContent = city;
                            div.addEventListener('click', () => {
                                input.value = city;
                                suggestionBox.classList.add('hidden');
                                // Trigger search when selection is made
                                input.dispatchEvent(new Event('change'));
                            });
                            suggestionBox.appendChild(div);
                        });
                        suggestionBox.classList.remove('hidden');
                    } else {
                        suggestionBox.classList.add('hidden');
                    }
                });
        }, 300);
    });

    // Hide suggestions when clicking outside
    document.addEventListener('click', function(e) {
        if (!wrapper.contains(e.target)) {
            suggestionBox.classList.add('hidden');
        }
    });
}

function setupRealTimeSearch(form) {
    const inputs = form.querySelectorAll('input, select');
    inputs.forEach(input => {
        input.addEventListener('change', () => performSearch(form));
    });
}

function performSearch(form) {
    clearTimeout(searchTimeout);
    searchTimeout = setTimeout(() => {
        const formData = new FormData(form);
        const searchParams = new URLSearchParams(formData);
        
        fetch(`/flights/search/?${searchParams.toString()}`, {
            headers: {
                'X-Requested-With': 'XMLHttpRequest'
            }
        })
        .then(response => response.json())
        .then(data => {
            updateFlightResults(data.flights);
        })
        .catch(error => console.error('Error:', error));
    }, 500);
}

function updateFlightResults(flights) {
    const resultsContainer = document.querySelector('#flight-results');
    if (!resultsContainer) return;

    if (flights.length === 0) {
        resultsContainer.innerHTML = `
            <div class="text-center py-8">
                <p class="text-gray-500">No flights found matching your criteria.</p>
            </div>
        `;
        return;
    }

    resultsContainer.innerHTML = flights.map(flight => `
        <div class="bg-white rounded-lg shadow-md p-6 mb-4">
            <div class="flex items-center justify-between mb-4">
                <div>
                    <h3 class="text-lg font-semibold">${flight.airline}</h3>
                    <p class="text-gray-600">Flight ${flight.flight_number}</p>
                </div>
                <div class="text-right">
                    <p class="text-2xl font-bold text-indigo-600">$${flight.price}</p>
                    <p class="text-sm text-gray-500">${flight.travel_class}</p>
                </div>
            </div>
            
            <div class="flex items-center justify-between mb-4">
                <div class="text-center">
                    <p class="font-medium">${flight.departure_city}</p>
                    <p class="text-sm text-gray-500">${flight.departure_time}</p>
                </div>
                
                <div class="flex-1 px-8">
                    <div class="relative">
                        <div class="h-0.5 bg-gray-300 absolute w-full top-1/2"></div>
                        <div class="flex justify-center">
                            <i class="fas fa-plane text-indigo-600 text-2xl transform -rotate-90 bg-white px-2"></i>
                        </div>
                    </div>
                </div>
                
                <div class="text-center">
                    <p class="font-medium">${flight.arrival_city}</p>
                    <p class="text-sm text-gray-500">${flight.arrival_time}</p>
                </div>
            </div>
            
            <div class="flex items-center justify-between">
                <p class="text-sm text-gray-600">${flight.available_seats} seats available</p>
                <a href="/flights/${flight.id}/book/" class="inline-flex items-center px-4 py-2 border border-transparent text-sm font-medium rounded-md text-white bg-indigo-600 hover:bg-indigo-700">
                    Book Now
                </a>
            </div>
        </div>
    `).join('');
}

// Initialize search functionality for all booking types
function initializeSearch() {
    initializeFlightSearch();
    initializeHotelSearch();
    initializeTourSearch();
}

// Hotel Search Functionality
function initializeHotelSearch() {
    const searchForm = document.querySelector('.hotel-search-form');
    const locationInput = document.querySelector('input[name="location"]');

    if (locationInput) {
        setupLocationAutocomplete(locationInput);
    }
    if (searchForm) {
        setupRealTimeSearch(searchForm, 'hotel');
    }
}

// Tour Search Functionality
function initializeTourSearch() {
    const searchForm = document.querySelector('.tour-search-form');
    const destinationInput = document.querySelector('input[name="destination"]');

    if (destinationInput) {
        setupLocationAutocomplete(destinationInput);
    }
    if (searchForm) {
        setupRealTimeSearch(searchForm, 'tour');
    }
}

function setupLocationAutocomplete(input) {
    const wrapper = document.createElement('div');
    wrapper.className = 'relative';
    input.parentNode.insertBefore(wrapper, input);
    wrapper.appendChild(input);

    const suggestionBox = document.createElement('div');
    suggestionBox.className = 'absolute z-50 w-full bg-white border border-gray-300 rounded-lg mt-1 shadow-lg hidden';
    wrapper.appendChild(suggestionBox);

    input.addEventListener('input', function() {
        clearTimeout(searchTimeout);
        const query = this.value;
        
        if (query.length < 2) {
            suggestionBox.innerHTML = '';
            suggestionBox.classList.add('hidden');
            return;
        }

        searchTimeout = setTimeout(() => {
            // Use the same endpoint for locations
            fetch(`/api/cities/?q=${encodeURIComponent(query)}`)
                .then(response => response.json())
                .then(data => {
                    suggestionBox.innerHTML = '';
                    if (data.cities.length > 0) {
                        data.cities.forEach(city => {
                            const div = document.createElement('div');
                            div.className = 'px-4 py-2 hover:bg-gray-100 cursor-pointer';
                            div.textContent = city;
                            div.addEventListener('click', () => {
                                input.value = city;
                                suggestionBox.classList.add('hidden');
                                input.dispatchEvent(new Event('change'));
                            });
                            suggestionBox.appendChild(div);
                        });
                        suggestionBox.classList.remove('hidden');
                    } else {
                        suggestionBox.classList.add('hidden');
                    }
                });
        }, 300);
    });

    // Hide suggestions when clicking outside
    document.addEventListener('click', function(e) {
        if (!wrapper.contains(e.target)) {
            suggestionBox.classList.add('hidden');
        }
    });
}

function setupRealTimeSearch(form, type) {
    const inputs = form.querySelectorAll('input, select');
    inputs.forEach(input => {
        input.addEventListener('change', () => performSearch(form, type));
    });
}

function performSearch(form, type) {
    clearTimeout(searchTimeout);
    searchTimeout = setTimeout(() => {
        const formData = new FormData(form);
        const searchParams = new URLSearchParams(formData);
        
        fetch(`/${type}s/search/?${searchParams.toString()}`, {
            headers: {
                'X-Requested-With': 'XMLHttpRequest'
            }
        })
        .then(response => response.json())
        .then(data => {
            if (type === 'flight') {
                updateFlightResults(data.flights);
            } else if (type === 'hotel') {
                updateHotelResults(data.hotels);
            } else if (type === 'tour') {
                updateTourResults(data.tours);
            }
        })
        .catch(error => console.error('Error:', error));
    }, 500);
}

function updateHotelResults(hotels) {
    const resultsContainer = document.querySelector('#hotel-results');
    if (!resultsContainer) return;

    if (hotels.length === 0) {
        resultsContainer.innerHTML = `
            <div class="text-center py-8">
                <p class="text-gray-500">No hotels found matching your criteria.</p>
            </div>
        `;
        return;
    }

    resultsContainer.innerHTML = hotels.map(hotel => `
        <div class="bg-white rounded-lg shadow-md p-6 mb-4">
            <div class="flex items-center justify-between mb-4">
                <div>
                    <h3 class="text-lg font-semibold">${hotel.name}</h3>
                    <p class="text-gray-600"><i class="fas fa-map-marker-alt mr-2"></i>${hotel.location}</p>
                </div>
                <div class="text-right">
                    <p class="text-2xl font-bold text-indigo-600">$${hotel.price_per_night}</p>
                    <p class="text-sm text-gray-500">per night</p>
                </div>
            </div>
            
            <div class="grid grid-cols-2 gap-4 mb-4">
                <div class="text-sm">
                    <p><i class="fas fa-bed mr-2"></i>${hotel.room_type}</p>
                    <p><i class="fas fa-user-friends mr-2"></i>${hotel.available_rooms} rooms available</p>
                </div>
                <div class="text-sm">
                    <p><i class="fas fa-star text-yellow-400 mr-2"></i>${hotel.rating} / 5</p>
                    <p><i class="fas fa-concierge-bell mr-2"></i>${hotel.amenities}</p>
                </div>
            </div>
            
            <div class="flex items-center justify-between">
                <p class="text-sm text-gray-600">${hotel.description.substring(0, 100)}...</p>
                <a href="/hotels/${hotel.id}/book/" class="inline-flex items-center px-4 py-2 border border-transparent text-sm font-medium rounded-md text-white bg-indigo-600 hover:bg-indigo-700">
                    Book Now
                </a>
            </div>
        </div>
    `).join('');
}

function updateTourResults(tours) {
    const resultsContainer = document.querySelector('#tour-results');
    if (!resultsContainer) return;

    if (tours.length === 0) {
        resultsContainer.innerHTML = `
            <div class="text-center py-8">
                <p class="text-gray-500">No tours found matching your criteria.</p>
            </div>
        `;
        return;
    }

    resultsContainer.innerHTML = tours.map(tour => `
        <div class="bg-white rounded-lg shadow-md p-6 mb-4">
            <div class="flex items-center justify-between mb-4">
                <div>
                    <h3 class="text-lg font-semibold">${tour.name}</h3>
                    <p class="text-gray-600"><i class="fas fa-map-marker-alt mr-2"></i>${tour.destination}</p>
                </div>
                <div class="text-right">
                    <p class="text-2xl font-bold text-indigo-600">$${tour.price}</p>
                    <p class="text-sm text-gray-500">per person</p>
                </div>
            </div>
            
            <div class="grid grid-cols-2 gap-4 mb-4">
                <div class="text-sm">
                    <p><i class="fas fa-clock mr-2"></i>${tour.duration_days} days</p>
                    <p><i class="fas fa-calendar mr-2"></i>${tour.start_date} - ${tour.end_date}</p>
                </div>
                <div class="text-sm">
                    <p><i class="fas fa-users mr-2"></i>${tour.max_participants - tour.current_participants} spots left</p>
                    <p><i class="fas fa-tag mr-2"></i>${tour.tour_type}</p>
                </div>
            </div>
            
            <div class="flex items-center justify-between">
                <p class="text-sm text-gray-600">${tour.description.substring(0, 100)}...</p>
                <a href="/tours/${tour.id}/book/" class="inline-flex items-center px-4 py-2 border border-transparent text-sm font-medium rounded-md text-white bg-indigo-600 hover:bg-indigo-700">
                    Book Now
                </a>
            </div>
        </div>
    `).join('');
}

// Initialize when DOM is loaded
document.addEventListener('DOMContentLoaded', function() {
    initializeSearch();
}); 