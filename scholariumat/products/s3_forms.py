from s3upload.widgets import S3UploadWidget
from django import forms
from .models import FileAttachment


class S3UploadForm(forms.ModelForm):
    file = forms.URLField(widget=S3UploadWidget(dest='default'))

    class Meta:
        model = FileAttachment
        exclude = []
