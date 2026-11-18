from decimal import ROUND_HALF_UP, Decimal

from django import forms

from .models import (BusinessPartner, JointCredential, JointExpense, JointPayment, JointProject, JointQuote,
                     JointUpdate)


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
        fields = ['title', 'client_name', 'status', 'progress', 'deal_type', 'contract_value',
                  'partner_share_percent', 'amc_amount', 'amc_cycle', 'amc_start_date', 'server_amount',
                  'server_cycle', 'server_start_date', 'recurring_end_date',
                  'start_date', 'deadline', 'completed_date', 'linked_project', 'repo_url', 'live_url',
                  'description', 'notes', 'internal_notes']
        widgets = {'start_date': DATE, 'deadline': DATE, 'completed_date': DATE, 'amc_start_date': DATE,
                   'server_start_date': DATE, 'recurring_end_date': DATE}
        labels = {'notes': 'Notes for the partner'}

    deal_toggle = True
    SPLIT_ONLY = ('partner_share_percent',)
    FIXED_ONLY = ('amc_amount', 'amc_cycle', 'amc_start_date', 'server_amount', 'server_cycle',
                  'server_start_date', 'recurring_end_date')

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for name in self.SPLIT_ONLY:
            self.fields[name].widget.attrs['data-deal'] = 'split'
        for name in self.FIXED_ONLY:
            self.fields[name].widget.attrs['data-deal'] = 'fixed'
            self.fields[name].required = False

    def clean(self):
        data = super().clean()
        for key in ('amc', 'server'):
            if data.get(f'{key}_amount') is None:
                data[f'{key}_amount'] = Decimal('0')
            if not data.get(f'{key}_cycle'):
                data[f'{key}_cycle'] = 'yearly'
        if data.get('deal_type') == 'fixed':
            for key, label in (('amc', 'AMC'), ('server', 'server charges')):
                if (data.get(f'{key}_amount') or 0) > 0 and not data.get(f'{key}_start_date'):
                    self.add_error(f'{key}_start_date', f'Pick the date the {label} start.')
        return data
        self.fields['linked_project'].queryset = self.fields['linked_project'].queryset.select_related('client')
        self.fields['linked_project'].required = False


class JointCredentialForm(_Styled):
    class Meta:
        model = JointCredential
        fields = ['kind', 'name', 'url', 'username', 'password', 'notes', 'shared_with_partner']
        # Plain text so an edit shows the saved password instead of blanking it.
        widgets = {'password': forms.TextInput(attrs={'autocomplete': 'off', 'spellcheck': 'false'}),
                   'username': forms.TextInput(attrs={'autocomplete': 'off'})}


class JointQuoteForm(_Styled):
    class Meta:
        model = JointQuote
        fields = ['title', 'amount', 'quote_date', 'valid_until', 'status', 'details', 'file']
        widgets = {'quote_date': DATE, 'valid_until': DATE}


class _ConvertedForm(_Styled):
    """Payment/expense form: type what was paid in the currency it was paid in.

    When that currency differs from the project's, the exchange rate turns it
    into the project currency (`amount`), which the split and totals use.
    """
    converter = True

    def __init__(self, *args, project=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.project = project
        cur = project.currency
        self.project_currency = cur
        f = self.fields
        f['paid_currency'].required = True
        f['paid_currency'].choices = [c for c in f['paid_currency'].choices if c[0]]
        f['paid_currency'].label = 'Paid in'
        f['paid_amount'].required = True
        f['paid_amount'].label = 'Amount paid'
        f['exchange_rate'].label = f'Rate (paid currency per 1 {cur})'
        f['exchange_rate'].help_text = f'e.g. 23.45 if 1 {cur} = 23.45 INR. Ignored when paid in {cur}.'
        f['exchange_rate'].widget.attrs.update({'step': '0.0001', 'min': '0'})
        # model_to_dict has already put blanks in self.initial, so assign, don't setdefault.
        inst = self.instance
        if not inst._state.adding:  # UUID pk is set before save, so pk can't tell
            if not inst.paid_currency:
                self.initial['paid_currency'] = cur
                self.initial['paid_amount'] = inst.amount
        elif not self.is_bound:
            last = self._last_used()
            self.initial['paid_currency'] = last.paid_currency if last else cur
            if last and last.paid_currency != cur and last.exchange_rate:
                self.initial['exchange_rate'] = last.exchange_rate

    def _last_used(self):
        """The latest payment or expense on any of this partner's projects."""
        from .models import JointExpense, JointPayment
        found = []
        for model in (JointPayment, JointExpense):
            obj = (model.objects.filter(project__partner_id=self.project.partner_id)
                   .exclude(paid_currency='').order_by('-created_at').first())
            if obj:
                found.append(obj)
        return max(found, key=lambda o: o.created_at) if found else None

    def clean(self):
        data = super().clean()
        cur, paid = data.get('paid_currency'), data.get('paid_amount')
        if not cur or paid is None:
            return data
        if paid <= 0:
            self.add_error('paid_amount', 'Enter an amount above zero.')
            return data
        if cur == self.project_currency:
            data['exchange_rate'] = Decimal('1')
            amount = paid
        else:
            rate = data.get('exchange_rate')
            if not rate or rate <= 0:
                self.add_error('exchange_rate', f'Enter how many {cur} make 1 {self.project_currency}.')
                return data
            amount = (paid / rate).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
            if amount <= 0:
                self.add_error('exchange_rate', 'That rate makes the amount zero.')
                return data
        self.instance.amount = amount
        return data


class JointPaymentForm(_ConvertedForm):
    class Meta:
        model = JointPayment
        fields = ['kind', 'purpose', 'paid_currency', 'paid_amount', 'exchange_rate', 'payment_date', 'method',
                  'reference', 'notes', 'receipt']
        widgets = {'payment_date': DATE}
        labels = {'kind': 'Who paid whom'}

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['purpose'].required = False
        if self.instance._state.adding and not self.is_bound and self.project.is_fixed:
            self.initial['kind'] = 'partner_to_ralfiz'

    def clean(self):
        data = super().clean()
        if not data.get('purpose'):
            data['purpose'] = 'development'
        return data


class JointExpenseForm(_ConvertedForm):
    class Meta:
        model = JointExpense
        fields = ['description', 'paid_currency', 'paid_amount', 'exchange_rate', 'expense_date', 'paid_by',
                  'receipt']
        widgets = {'expense_date': DATE}


class JointUpdateForm(_Styled):
    class Meta:
        model = JointUpdate
        fields = ['message']
        widgets = {'message': forms.Textarea(attrs={'rows': 2, 'placeholder': 'Write an update…'})}
        labels = {'message': ''}
