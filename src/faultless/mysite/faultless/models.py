import os
import json
from django.db import models


# Create your models here.
class Rules(models.Model):
    id = models.AutoField(primary_key=True)
    name = models.CharField(max_length=30)
    scale = models.IntegerField()
    description = models.TextField()

    def default_output_format():
        data = {
            'matches': [
                {
                    'error_type': 'error name(only use the name i gave you)',
                    'message': 'simple description of the error and how to correct it',
                    'original': 'the error word or phrase or sentence(depend on different type of error)',
                    'occurrence_index': 'occurrence times of the error',
                },
            ]
        }

        return data
    
    output_format = models.JSONField(default=default_output_format)

    def __str__(self):
        return self.name


class Document(models.Model):
    file = models.FileField(upload_to="documents/")
    path = models.CharField(max_length=255)
    uploaded_at = models.DateTimeField(auto_now_add=True)

    # Delete file
    def save(self, *args, **kwargs):
        print("Saving document:", self.file.name)
        super().save(*args, **kwargs)
        if self.file:
            self.path = self.file.path
            Document.objects.filter(pk=self.pk).update(path=self.path)

    def delete(self, *args, **kwargs):
        if self.file:
            if os.path.isfile(self.file.path):
                os.remove(self.file.path)

        super().delete(*args, **kwargs)

    def __str__(self):
        return self.file.name

class Trace(models.Model):
    id = models.AutoField(primary_key=True)
    file_name = models.CharField(max_length=255, blank=True, default='')
    review_output = models.JSONField(default={"matches": []}, blank=True)
    record_at = models.DateTimeField(auto_now_add=True)

