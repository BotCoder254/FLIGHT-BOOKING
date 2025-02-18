# TravelEase - Travel Booking Platform

A modern travel booking platform built with Django, PostgreSQL, Tailwind CSS, and M-Pesa integration.

## Features

- User Authentication with role-based access (Travelers and Admins)
- Flight, Hotel, and Tour Booking
- Beautiful and responsive UI with Tailwind CSS
- Interactive components with Alpine.js
- M-Pesa payment integration
- Admin dashboard with analytics
- User profiles and booking management
- Real-time notifications
- Secure payment processing

## Tech Stack

- **Backend**: Django 5.0.1
- **Database**: PostgreSQL
- **Frontend**: 
  - Tailwind CSS
  - Alpine.js
  - Font Awesome icons
- **Authentication**: Django built-in auth
- **Payment**: M-Pesa integration
- **Animations**: AOS (Animate on Scroll)

## Prerequisites

- Python 3.8+
- PostgreSQL
- Node.js and npm (for Tailwind CSS)

## Installation

1. Clone the repository:
   ```bash
   git clone <repository-url>
   cd travel-booking
   ```

2. Create and activate a virtual environment:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. Install Python dependencies:
   ```bash
   pip install -r requirements.txt
   ```

4. Set up environment variables:
   Create a `.env` file in the root directory and add:
   ```
   DATABASE_URL=your_database_url
   SECRET_KEY=your_secret_key
   DEBUG=True
   ```

5. Install Tailwind CSS dependencies:
   ```bash
   python manage.py tailwind install
   ```

6. Run migrations:
   ```bash
   python manage.py migrate
   ```

7. Create a superuser:
   ```bash
   python manage.py createsuperuser
   ```

8. Start the development server:
   ```bash
   python manage.py runserver
   ```

9. In a separate terminal, start the Tailwind CSS build process:
   ```bash
   python manage.py tailwind start
   ```

## Project Structure

```
travel_booking/
├── core/                   # Main application
│   ├── models.py          # Database models
│   ├── views.py           # View functions
│   ├── forms.py           # Forms
│   ├── urls.py            # URL patterns
│   └── admin.py           # Admin interface
├── templates/             # HTML templates
│   ├── base.html         # Base template
│   ├── home.html         # Landing page
│   ├── dashboard/        # Dashboard templates
│   └── registration/     # Auth templates
├── static/               # Static files
│   ├── css/             # Custom CSS
│   └── js/              # Custom JavaScript
├── media/               # User uploads
├── requirements.txt     # Python dependencies
└── manage.py           # Django management script
```

## Development

- Run tests:
  ```bash
  python manage.py test
  ```

- Format code:
  ```bash
  black .
  ```

- Check code style:
  ```bash
  flake8
  ```

## Deployment

1. Set `DEBUG=False` in production
2. Configure your web server (e.g., Nginx)
3. Set up SSL certificate
4. Configure PostgreSQL for production
5. Set up static file serving
6. Configure environment variables

## Contributing

1. Fork the repository
2. Create a feature branch
3. Commit your changes
4. Push to the branch
5. Create a Pull Request

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Acknowledgments

- Django documentation
- Tailwind CSS documentation
- Alpine.js documentation
- Font Awesome icons
- Unsplash for images 