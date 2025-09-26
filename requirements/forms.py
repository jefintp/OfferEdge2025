from django import forms
NEGOTIATION_CHOICES = [
    ("lowest_bid", "Go with Lowest Bid"),
    ("negotiation", "Enable Negotiation Below Price"),
]

class RequirementForm(forms.Form):
    title = forms.CharField(max_length=100)
    description = forms.CharField(widget=forms.Textarea)
    quantity = forms.IntegerField(min_value=1)
    expectedPriceRange = forms.CharField(max_length=50)
    deadline = forms.DateTimeField(widget=forms.DateTimeInput(attrs={'type': 'datetime-local'}))

    negotiation_mode = forms.ChoiceField(
        choices=NEGOTIATION_CHOICES,
        widget=forms.RadioSelect,
        required=True
    )
    negotiation_trigger_price = forms.FloatField(required=False)

    attachment = forms.FileField(required=False)  # ✅ Add this line

    def clean(self):
        cleaned_data = super().clean()
        mode = cleaned_data.get("negotiation_mode")
        trigger_price = cleaned_data.get("negotiation_trigger_price")

        if mode == "negotiation":
            if trigger_price is None:
                raise forms.ValidationError("Please specify the price below which negotiation is allowed.")
            if trigger_price <= 0:
                raise forms.ValidationError("Negotiation trigger price must be greater than zero.")