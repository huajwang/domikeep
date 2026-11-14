from django import forms


class QuoteForm(forms.Form):
    name = forms.CharField(max_length=120)
    contact = forms.CharField(max_length=200, label="Email or phone")
    message = forms.CharField(widget=forms.Textarea(attrs={"rows": 5}))
