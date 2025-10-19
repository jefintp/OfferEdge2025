from django import forms
from django.utils import timezone

NEGOTIATION_CHOICES = [
    ("lowest_bid", "Go with Lowest Bid"),
    ("negotiation", "Enable Negotiation Below Price"),
]

class RequirementForm(forms.Form):
    title = forms.CharField(max_length=100)
    description = forms.CharField(widget=forms.Textarea)
    quantity = forms.IntegerField(min_value=1)
    expectedPriceRange = forms.CharField(max_length=50, label="Expected Price Range")
    deadline = forms.DateTimeField(widget=forms.DateTimeInput(attrs={'type': 'datetime-local'}))

    category = forms.ChoiceField(
        choices=[("service", "Service"), ("product", "Product")],
        widget=forms.RadioSelect,
        required=True,
        label="Category"
    )
    location = forms.CharField(max_length=120, required=True, label="Location")

    negotiation_mode = forms.ChoiceField(
        choices=NEGOTIATION_CHOICES,
        widget=forms.RadioSelect,
        required=True,
        label="Deal Finalisation Preference"
    )
    negotiation_trigger_price = forms.FloatField(required=False)

    attachment = forms.FileField(required=False)  # ✅ Add this line

    def clean_deadline(self):
        deadline = self.cleaned_data.get("deadline")
        if not deadline:
            return deadline
        # Normalize to aware datetime in current timezone
        if timezone.is_naive(deadline):
            deadline = timezone.make_aware(deadline, timezone.get_current_timezone())
        now = timezone.now()
        if deadline <= now:
            raise forms.ValidationError("Deadline must be in the future.")
        return deadline

    def clean_location(self):
        """Normalize location to be case-insensitive by storing it in lowercase."""
        loc = self.cleaned_data.get("location")
        if loc is None:
            return loc
        return loc.strip().casefold()

    def clean(self):
        cleaned_data = super().clean()
        mode = cleaned_data.get("negotiation_mode")
        trigger_price = cleaned_data.get("negotiation_trigger_price")

        if mode == "negotiation":
            if trigger_price is None:
                raise forms.ValidationError("Please specify the price below which negotiation is allowed.")
            if trigger_price <= 0:
                raise forms.ValidationError("Negotiation trigger price must be greater than zero.")
