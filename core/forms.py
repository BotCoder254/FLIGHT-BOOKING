from django import forms
from django.contrib.auth.forms import UserCreationForm
from .models import User, Flight, Hotel, Tour, Booking, HotelImage, TourImage

class UserRegistrationForm(UserCreationForm):
    first_name = forms.CharField(max_length=30, required=True)
    last_name = forms.CharField(max_length=30, required=True)
    email = forms.EmailField(max_length=254, required=True)
    terms = forms.BooleanField(required=True)

    class Meta:
        model = User
        fields = ('username', 'first_name', 'last_name', 'email', 'password1', 'password2', 'role')

class FlightSearchForm(forms.Form):
    departure_city = forms.CharField(max_length=100, required=False)
    arrival_city = forms.CharField(max_length=100, required=False)
    departure_date = forms.DateField(required=False, widget=forms.DateInput(attrs={'type': 'date'}))
    return_date = forms.DateField(required=False, widget=forms.DateInput(attrs={'type': 'date'}))
    travel_class = forms.ChoiceField(choices=[('', 'Any')] + Flight.CLASS_CHOICES, required=False)
    passengers = forms.IntegerField(min_value=1, max_value=10, initial=1)
    max_price = forms.DecimalField(required=False, min_value=0)

class HotelSearchForm(forms.Form):
    location = forms.CharField(max_length=200, required=False)
    check_in = forms.DateField(required=False, widget=forms.DateInput(attrs={'type': 'date'}))
    check_out = forms.DateField(required=False, widget=forms.DateInput(attrs={'type': 'date'}))
    room_type = forms.ChoiceField(choices=[('', 'Any')] + Hotel.ROOM_CHOICES, required=False)
    guests = forms.IntegerField(min_value=1, max_value=10, initial=1)
    max_price = forms.DecimalField(required=False, min_value=0)
    min_rating = forms.DecimalField(required=False, min_value=0, max_value=5)

class TourSearchForm(forms.Form):
    destination = forms.CharField(max_length=200, required=False)
    tour_type = forms.ChoiceField(choices=[('', 'Any')] + Tour.TOUR_TYPE_CHOICES, required=False)
    start_date = forms.DateField(required=False, widget=forms.DateInput(attrs={'type': 'date'}))
    max_duration = forms.IntegerField(required=False, min_value=1)
    max_price = forms.DecimalField(required=False, min_value=0)
    participants = forms.IntegerField(min_value=1, max_value=20, initial=1)

class BookingForm(forms.ModelForm):
    check_in = forms.DateField(
        required=True,
        widget=forms.DateInput(
            attrs={
                'type': 'date',
                'class': 'appearance-none rounded-lg relative block w-full px-4 py-3 border border-gray-300 placeholder-gray-500 text-gray-900 focus:outline-none focus:ring-indigo-500 focus:border-indigo-500 focus:z-10 text-base h-12'
            }
        )
    )
    check_out = forms.DateField(
        required=True,
        widget=forms.DateInput(
            attrs={
                'type': 'date',
                'class': 'appearance-none rounded-lg relative block w-full px-4 py-3 border border-gray-300 placeholder-gray-500 text-gray-900 focus:outline-none focus:ring-indigo-500 focus:border-indigo-500 focus:z-10 text-base h-12'
            }
        )
    )
    
    class Meta:
        model = Booking
        fields = ['number_of_guests', 'special_requests']
        widgets = {
            'number_of_guests': forms.NumberInput(attrs={
                'class': 'appearance-none rounded-lg relative block w-full px-4 py-3 border border-gray-300 placeholder-gray-500 text-gray-900 focus:outline-none focus:ring-indigo-500 focus:border-indigo-500 focus:z-10 text-base h-12',
                'min': 1
            }),
            'special_requests': forms.Textarea(attrs={
                'class': 'appearance-none rounded-lg relative block w-full px-4 py-3 border border-gray-300 placeholder-gray-500 text-gray-900 focus:outline-none focus:ring-indigo-500 focus:border-indigo-500 focus:z-10 text-base min-h-[100px]',
                'rows': 4
            }),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            field.widget.attrs.update({'class': 'form-input rounded-lg border-gray-300 focus:border-indigo-500 focus:ring-indigo-500'})

    def save(self, commit=True):
        instance = super().save(commit=False)
        if commit:
            instance.check_in_date = self.cleaned_data['check_in']
            instance.check_out_date = self.cleaned_data['check_out']
            instance.save()
        return instance

class BookingStatusForm(forms.ModelForm):
    class Meta:
        model = Booking
        fields = ['status']
        widgets = {
            'status': forms.Select(attrs={'class': 'form-select rounded-md shadow-sm mt-1 block w-full'})
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['status'].choices = Booking.STATUS_CHOICES

class FlightForm(forms.ModelForm):
    class Meta:
        model = Flight
        fields = ['flight_number', 'airline', 'departure_city', 'arrival_city', 
                 'departure_time', 'arrival_time', 'price', 'available_seats', 'travel_class']
        widgets = {
            'departure_time': forms.DateTimeInput(attrs={'type': 'datetime-local'}),
            'arrival_time': forms.DateTimeInput(attrs={'type': 'datetime-local'}),
        }

class MultipleFileInput(forms.ClearableFileInput):
    allow_multiple_selected = True

class MultipleFileField(forms.FileField):
    def __init__(self, *args, **kwargs):
        kwargs.setdefault("widget", MultipleFileInput())
        super().__init__(*args, **kwargs)

    def clean(self, data, initial=None):
        single_file_clean = super().clean
        if isinstance(data, (list, tuple)):
            result = [single_file_clean(d, initial) for d in data]
        else:
            result = single_file_clean(data, initial)
        return result

class HotelForm(forms.ModelForm):
    images = MultipleFileField(required=False)
    
    class Meta:
        model = Hotel
        fields = ['name', 'location', 'description', 'price_per_night', 'room_type',
                 'available_rooms', 'amenities', 'rating']
        widgets = {
            'description': forms.Textarea(attrs={'rows': 4}),
            'amenities': forms.Textarea(attrs={'rows': 4}),
        }

    def save(self, commit=True):
        instance = super().save(commit=commit)
        if commit and self.files.getlist('images'):
            for f in self.files.getlist('images'):
                HotelImage.objects.create(hotel=instance, image=f)
        return instance

class TourForm(forms.ModelForm):
    images = MultipleFileField(required=False)
    
    class Meta:
        model = Tour
        fields = ['name', 'destination', 'description', 'duration_days', 'price',
                 'tour_type', 'max_participants', 'start_date', 'end_date',
                 'included_services']
        widgets = {
            'description': forms.Textarea(attrs={'rows': 4}),
            'included_services': forms.Textarea(attrs={'rows': 4}),
            'start_date': forms.DateInput(attrs={'type': 'date'}),
            'end_date': forms.DateInput(attrs={'type': 'date'}),
        }

    def save(self, commit=True):
        instance = super().save(commit=commit)
        if commit and self.files.getlist('images'):
            for f in self.files.getlist('images'):
                TourImage.objects.create(tour=instance, image=f)
        return instance

class TourBookingForm(forms.ModelForm):
    number_of_guests = forms.IntegerField(
        min_value=1,
        widget=forms.NumberInput(attrs={
            'class': 'appearance-none rounded-lg relative block w-full px-4 py-3 border border-gray-300 placeholder-gray-500 text-gray-900 focus:outline-none focus:ring-indigo-500 focus:border-indigo-500 focus:z-10 text-base h-12',
            'min': 1
        })
    )
    special_requests = forms.CharField(
        required=False,
        widget=forms.Textarea(attrs={
            'class': 'appearance-none rounded-lg relative block w-full px-4 py-3 border border-gray-300 placeholder-gray-500 text-gray-900 focus:outline-none focus:ring-indigo-500 focus:border-indigo-500 focus:z-10 text-base min-h-[100px]',
            'rows': 4
        })
    )

    class Meta:
        model = Booking
        fields = ['number_of_guests', 'special_requests']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            field.widget.attrs.update({'class': 'form-input rounded-lg border-gray-300 focus:border-indigo-500 focus:ring-indigo-500'})

    def save(self, commit=True):
        instance = super().save(commit=False)
        if commit:
            instance.save()
        return instance 