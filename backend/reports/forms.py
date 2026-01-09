from django import forms
from .models import WasteReport
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
