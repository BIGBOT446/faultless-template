import os

from django.db import models


# Create your models here.
class rules(models.Model):
    name = models.CharField(max_length=30)
    scale = models.IntegerField()
    description = models.TextField()

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


