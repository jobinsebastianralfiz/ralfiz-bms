from django import forms
from django.contrib.auth.models import User

from .models import DigitalCard


class DigitalCardForm(forms.ModelForm):
    class Meta:
        model = DigitalCard
        fields = [
            'card_type', 'full_name', 'designation', 'company', 'slug', 'photo', 'logo', 'bio',
            'phone', 'whatsapp', 'email', 'website', 'address', 'map_url', 'google_review_url',
            'linkedin', 'instagram', 'facebook', 'twitter', 'youtube', 'github',
            'services', 'highlights', 'company_about', 'theme', 'owner', 'show_enquiry_form', 'is_active',
        ]
        widgets = {
            'bio': forms.Textarea(attrs={'rows': 3}),
            'address': forms.Textarea(attrs={'rows': 2}),
            'services': forms.Textarea(attrs={'rows': 4, 'placeholder': 'Websites\nMobile apps\nBusiness software'}),
            'highlights': forms.Textarea(attrs={'rows': 3, 'placeholder': '4+ Years | Professional experience\n100+ | Projects delivered\nKerala & GCC | Businesses served'}),
            'company_about': forms.Textarea(attrs={'rows': 3}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['slug'].required = False
        self.fields['card_type'].required = False
        self.fields['owner'].queryset = User.objects.filter(is_active=True).order_by('first_name', 'username')
        self.fields['owner'].label_from_instance = lambda u: u.get_full_name() or u.username
        for name, field in self.fields.items():
            if isinstance(field.widget, forms.CheckboxInput):
                field.widget.attrs['class'] = 'form-check-input'
            else:
                field.widget.attrs.setdefault('class', 'form-control')

    # (heading, [(field name, Bootstrap column)]) in the order the form shows them
    SECTIONS = [
        ('Who', [('card_type', 'col-md-6'), ('theme', 'col-md-6'), ('full_name', 'col-md-6'), ('designation', 'col-md-6'),
                 ('company', 'col-md-6'), ('slug', 'col-md-6'), ('photo', 'col-md-6'), ('logo', 'col-md-6'), ('bio', 'col-12')]),
        ('Contact', [('phone', 'col-md-6'), ('whatsapp', 'col-md-6'), ('email', 'col-md-6'), ('website', 'col-md-6'),
                     ('address', 'col-md-6'), ('map_url', 'col-md-6'), ('google_review_url', 'col-md-6')]),
        ('Social links', [('linkedin', 'col-md-4'), ('instagram', 'col-md-4'), ('facebook', 'col-md-4'),
                          ('twitter', 'col-md-4'), ('youtube', 'col-md-4'), ('github', 'col-md-4')]),
        ('Services and leads', [('services', 'col-md-6'), ('highlights', 'col-md-6'), ('company_about', 'col-md-6'), ('owner', 'col-md-6')]),
    ]

    def sections(self):
        return [(title, [(self[name], col) for name, col in fields]) for title, fields in self.SECTIONS]

    def clean_card_type(self):
        return self.cleaned_data.get('card_type') or 'person'

    def clean_slug(self):
        from django.utils.text import slugify
        slug = slugify(self.cleaned_data.get('slug') or '')
        if not slug:
            return DigitalCard.unique_slug(self.cleaned_data.get('full_name') or '', exclude_pk=self.instance.pk)
        if DigitalCard.objects.exclude(pk=self.instance.pk).filter(slug=slug).exists():
            raise forms.ValidationError('Another card already uses this link.')
        return slug
