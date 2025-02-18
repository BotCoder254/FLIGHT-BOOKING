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