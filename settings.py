INSTALLED_APPS = [
    # ... other apps ...
    'compressor',
    'corsheaders',
    'stripe',
] 

# Compression settings
COMPRESS_ENABLED = True
STATICFILES_FINDERS = [
    'django.contrib.staticfiles.finders.FileSystemFinder',
    'django.contrib.staticfiles.finders.AppDirectoriesFinder',
    'compressor.finders.CompressorFinder',
] 

MIDDLEWARE = [
    'corsheaders.middleware.CorsMiddleware',
    # ... other middleware ...
]

# CORS settings
CORS_ALLOW_ALL_ORIGINS = True  # For development only. Configure properly for production
# OR for specific origins:
# CORS_ALLOWED_ORIGINS = [
#     "http://localhost:8000",
#     "http://127.0.0.1:8000",
# ] 

# Stripe Settings
STRIPE_PUBLISHABLE_KEY = 'pk_test_51JMihKFmxId2hxxFi0AXS1khPIQgFDkZt4hf0zL5tnpFvDvDtuPA19wFLRQp7DJ7MKz9IkoFz0JO4IspKKk1DiaC00CNojZg4v'
STRIPE_SECRET_KEY = 'sk_test_51JMihKFmxId2hxxFTAnAHR0RmO7tmiaMbHzl3QcnVIjx2GkHVG1n7lvDNFARVXPqiTg9YhJnQbHCc9YAlwODrGjJ00814iNd6B'
STRIPE_WEBHOOK_SECRET = 'your_webhook_secret'