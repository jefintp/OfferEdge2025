from django import forms

class QuoteForm(forms.Form):
    price = forms.FloatField(min_value=0)
    deliveryTimeline = forms.CharField(max_length=100)
    notes = forms.CharField(widget=forms.Textarea, required=False)
    attachments = forms.FileField(required=False)