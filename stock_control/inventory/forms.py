# forms.py
from django import forms
from services.data_storage.models import Withdrawal, Product, PurchaseOrder, ProductItem
from django.contrib.auth.models import User
from django.contrib.auth.forms import UserCreationForm
from django.utils.timezone import now

class WithdrawalForm(forms.ModelForm):
    # Extra fields for manual mode (not mapped to model directly)

    barcode_manual = forms.CharField(
        required=False,
        label="Barcode (Manual)",
        widget=forms.TextInput(attrs={'readonly': 'readonly', 'id': 'id_barcode_manual'})
    )

    lot_number = forms.CharField(
        required=False,
        label="Lot Number",
        widget=forms.TextInput(attrs={'readonly': 'readonly', 'id': 'id_lot_number'})
    )

    expiry_date = forms.DateField(
        required=False,
        label="Expiry Date",
        widget=forms.TextInput(attrs={'readonly': 'readonly', 'id': 'id_expiry_date'})
    )

    units_per_quantity = forms.IntegerField(
        required=False,
        widget=forms.HiddenInput(attrs={'id': 'id_units_per_quantity'})
    )

    class Meta:
        model = Withdrawal
        fields = ['barcode', 'quantity', 'withdrawal_type', 'parts_withdrawn']
        widgets = {
            'barcode': forms.TextInput(attrs={'placeholder': 'Scan Barcode', 'autocomplete': 'off', 'id': 'id_barcode'}),
            'quantity': forms.NumberInput(attrs={'min': 0, 'step': '0.01'}),
        }


class ProductForm(forms.ModelForm):
    class Meta:
        model = Product
        fields = [
            'product_code',
            'name',
            'supplier',
            'threshold',
            'lead_time',
        ]


class ProductItemForm(forms.ModelForm):
    class Meta:
        model = ProductItem
        fields = [
            'lot_number',
            'expiry_date',
            'current_stock',
            'units_per_quantity',
            'accumulated_partial',
            'product_feature',
        ]



class AdminUserCreationForm(UserCreationForm):
    is_staff = forms.BooleanField(required=False, label="Admin Privileges")

    class Meta:
        model = User
        fields = ['username', 'email', 'is_staff', 'password1', 'password2']


class AdminUserEditForm(forms.ModelForm):
    is_active = forms.BooleanField(required=False, label="Active User")
    is_staff = forms.BooleanField(required=False, label="Admin Privileges")

    class Meta:
        model = User
        fields = ['username', 'email', 'is_active', 'is_staff']


class PurchaseOrderForm(forms.ModelForm):
    product_name = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={"readonly": "readonly", "id": "order-product-name"})
    )
    product_code = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={"readonly": "readonly", "id": "order-product-code"})
    )

    class Meta:
        model = PurchaseOrder
        fields = [
            'product_name',
            'product_code',
            'quantity_ordered',
            'expected_delivery',
            'status',
            
        ]
        widgets = {
            'expected_delivery': forms.DateTimeInput(attrs={'type': 'datetime-local'}),
            'status': forms.Select(choices=[('Ordered', 'Ordered'), ('Delivered', 'Delivered')]),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['product_name'].label = "Product Name"
        self.fields['product_code'].label = "Product Code"
        if not self.initial.get('expected_delivery'):
            self.initial['expected_delivery'] = now().strftime('%Y-%m-%dT%H:%M')



class PurchaseOrderCompletionForm(forms.Form):
    barcode = forms.CharField(widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Scan or enter barcode'}))
    product_code = forms.CharField(widget=forms.TextInput(attrs={'class': 'form-control'}))
    product_name = forms.CharField(widget=forms.TextInput(attrs={'class': 'form-control'}))
    lot_number = forms.CharField(widget=forms.TextInput(attrs={'class': 'form-control'}))
    expiry_date = forms.DateField(widget=forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}))
    quantity_ordered = forms.IntegerField(widget=forms.NumberInput(attrs={'class': 'form-control'}))
    # expected_delivery = forms.DateTimeField(widget=forms.DateTimeInput(attrs={'type': 'datetime-local', 'class': 'form-control'}))
    status = forms.ChoiceField(choices=[('Delivered', 'Delivered')], widget=forms.Select(attrs={'class': 'form-control'}))



# class PurchaseOrderCompletionForm(forms.ModelForm):
#     barcode = forms.CharField(
#         required=False,
#         widget=forms.TextInput(attrs={"placeholder": "Scan or enter barcode", "id": "complete-barcode"})
#     )
#     product_name = forms.CharField(
#         required=False,
#         widget=forms.TextInput(attrs={"readonly": "readonly", "id": "complete-product-name"})
#     )
#     product_code = forms.CharField(
#         required=False,
#         widget=forms.TextInput(attrs={"readonly": "readonly", "id": "complete-product-code"})
#     )
#     lot_number = forms.CharField(
#         required=False,
#         widget=forms.TextInput(attrs={"readonly": "readonly", "id": "complete-lot-number"})
#     )
#     expiry_date = forms.DateField(
#         required=False,
#         widget=forms.DateInput(attrs={"type": "date", "readonly": "readonly", "id": "complete-expiry-date"})
#     )

#     class Meta:
#         model = PurchaseOrder
#         fields = [
#             'barcode',
#             'product_name',
#             'product_code',
#             'lot_number',
#             'expiry_date',
#             'quantity_ordered',
#             'expected_delivery',
#             'status'
#         ]
#         widgets = {
#             'expected_delivery': forms.DateTimeInput(attrs={'type': 'datetime-local'}),
#             'status': forms.Select(choices=[('Ordered', 'Ordered'), ('Delivered', 'Delivered')]),
#         }
