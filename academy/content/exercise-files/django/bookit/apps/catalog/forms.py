from django import forms

from .models import Service

INPUT_CSS = "w-full rounded-lg border border-slate-300 px-3 py-2 focus:outline-none focus:ring-2 focus:ring-indigo-500"


class StyledFormMixin:
    """Adds Tailwind classes to every widget so templates stay clean."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            if not isinstance(field.widget, forms.CheckboxInput):
                field.widget.attrs.setdefault("class", INPUT_CSS)


class ServiceForm(StyledFormMixin, forms.ModelForm):
    class Meta:
        model = Service
        fields = ["name", "slug", "description", "duration_minutes", "price", "gst_rate", "is_active"]
        widgets = {"description": forms.Textarea(attrs={"rows": 3})}

    def clean_duration_minutes(self):
        minutes = self.cleaned_data["duration_minutes"]
        if minutes % 15:
            raise forms.ValidationError("Duration must be in 15-minute steps.")
        return minutes
