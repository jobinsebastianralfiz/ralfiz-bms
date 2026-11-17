from django import forms

from .models import BusinessPartner, JointExpense, JointPayment, JointProject, JointQuote, JointUpdate


class _Styled(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for name, field in self.fields.items():
            w = field.widget
            if isinstance(w, forms.CheckboxInput):
                continue
            w.attrs.setdefault('class', 'form-control')
            if isinstance(w, forms.Textarea):
                w.attrs.setdefault('rows', 3)


DATE = forms.DateInput(attrs={'type': 'date'}, format='%Y-%m-%d')


class BusinessPartnerForm(_Styled):
    class Meta:
        model = BusinessPartner
        fields = ['company_name', 'name', 'email', 'phone', 'whatsapp', 'country', 'city', 'address',
                  'tax_number', 'currency', 'default_partner_share', 'notes', 'is_active']
        labels = {'name': 'Contact person', 'company_name': 'Company name'}


class JointProjectForm(_Styled):
    class Meta:
        model = JointProject
        fields = ['title', 'client_name', 'status', 'progress', 'contract_value', 'partner_share_percent',
                  'start_date', 'deadline', 'completed_date', 'linked_project', 'description', 'notes',
                  'internal_notes']
        widgets = {'start_date': DATE, 'deadline': DATE, 'completed_date': DATE}
        labels = {'notes': 'Notes for the partner'}

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['linked_project'].queryset = self.fields['linked_project'].queryset.select_related('client')
        self.fields['linked_project'].required = False


class JointQuoteForm(_Styled):
    class Meta:
        model = JointQuote
        fields = ['title', 'amount', 'quote_date', 'valid_until', 'status', 'details', 'file']
        widgets = {'quote_date': DATE, 'valid_until': DATE}


class JointPaymentForm(_Styled):
    class Meta:
        model = JointPayment
        fields = ['kind', 'amount', 'payment_date', 'method', 'reference', 'notes', 'receipt']
        widgets = {'payment_date': DATE}
        labels = {'kind': 'Who paid whom'}


class JointExpenseForm(_Styled):
    class Meta:
        model = JointExpense
        fields = ['description', 'amount', 'expense_date', 'paid_by', 'receipt']
        widgets = {'expense_date': DATE}


class JointUpdateForm(_Styled):
    class Meta:
        model = JointUpdate
        fields = ['message']
        widgets = {'message': forms.Textarea(attrs={'rows': 2, 'placeholder': 'Write an update…'})}
        labels = {'message': ''}
