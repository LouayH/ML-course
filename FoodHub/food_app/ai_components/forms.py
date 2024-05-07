from django import forms


class MultipleFileInput(forms.ClearableFileInput):
    allow_multiple_selected = True


class MultipleFileField(forms.FileField):
    def __init__(self, *args, **kwargs):
        kwargs.setdefault("widget", MultipleFileInput())
        super().__init__(*args, **kwargs)

    def clean(self, data, initial=None):
        single_file_clean = super().clean
        if isinstance(data, (list, tuple)):
            result = [single_file_clean(d, initial) for d in data]
        else:
            result = single_file_clean(data, initial)
        return result


class IngredientsImagesForm(forms.Form):
    images = MultipleFileField() # attrs={'multiple': True}

    def clean(self):
        cleaned_data = super().clean()
        if len(cleaned_data["images"]) < 3:
            self.add_error("images", "عليك تحميل 3 صور على الأقل")


class MealsImagesForm(forms.Form):
    image = forms.FileField()
