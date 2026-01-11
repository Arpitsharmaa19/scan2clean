from django import forms
from .models import WasteReport, SupportTicket
from decimal import Decimal, ROUND_HALF_UP


class WasteReportForm(forms.ModelForm):
    class Meta:
        model = WasteReport
        fields = [
            "image",
            "waste_type",
            "severity",
            "description",
            "latitude",
            "longitude",
            "location_source",
        ]

    # ✅ FIX: normalize latitude to 6 decimal places
    def clean_latitude(self):
        lat = self.cleaned_data.get("latitude")

        if lat is None:
            return lat

        return Decimal(lat).quantize(
            Decimal("0.000001"),
            rounding=ROUND_HALF_UP
        )

    # ✅ FIX: normalize longitude to 6 decimal places
    def clean_longitude(self):
        lng = self.cleaned_data.get("longitude")

        if lng is None:
            return lng

        return Decimal(lng).quantize(
            Decimal("0.000001"),
            rounding=ROUND_HALF_UP
        )


class WasteReportEditForm(forms.ModelForm):
    class Meta:
        model = WasteReport
        fields = [
            "image",
            "description",
            "latitude",
            "longitude",
        ]

    def clean_latitude(self):
        lat = self.cleaned_data.get("latitude")
        if lat is None:
            return lat
        return Decimal(lat).quantize(Decimal("0.000001"), rounding=ROUND_HALF_UP)

    def clean_longitude(self):
        lng = self.cleaned_data.get("longitude")
        if lng is None:
            return lng
        return Decimal(lng).quantize(Decimal("0.000001"), rounding=ROUND_HALF_UP)


class SupportTicketForm(forms.ModelForm):
    class Meta:
        model = SupportTicket
        fields = ["subject", "message"]
        widgets = {
            'subject': forms.TextInput(attrs={
                'class': 'w-full bg-white dark:bg-gray-800 text-gray-900 dark:text-white border border-gray-200 dark:border-gray-700 rounded-xl px-4 py-3 outline-none focus:ring-2 focus:ring-red-400 transition-all',
                'placeholder': 'Summary of the issue...'
            }),
            'message': forms.Textarea(attrs={
                'class': 'w-full bg-white dark:bg-gray-800 text-gray-900 dark:text-white border border-gray-200 dark:border-gray-700 rounded-xl px-4 py-3 outline-none focus:ring-2 focus:ring-red-400 transition-all h-32',
                'placeholder': 'Please describe the problem in detail...'
            }),
        }
