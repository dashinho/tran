from django.core.exceptions import ValidationError
from django.db import models
from django.contrib.auth.models import User
from PIL import Image, UnidentifiedImageError


MAX_IMAGE_SIZE = 2 * 1024 * 1024
ALLOWED_IMAGE_FORMATS = {'JPEG': 'image/jpeg', 'PNG': 'image/png', 'WEBP': 'image/webp'}

def validate_file_size(value):
    if value.size >= MAX_IMAGE_SIZE:
        raise ValidationError('File size must be strictly under 2MB.')


def validate_image_content(value):
    content_type = getattr(value, 'content_type', None)
    if content_type and content_type not in ALLOWED_IMAGE_FORMATS.values():
        raise ValidationError('Only JPEG, PNG, and WebP images are supported.')

    try:
        with Image.open(value) as image:
            image.verify()
            image_format = image.format
    except (UnidentifiedImageError, OSError):
        raise ValidationError('The uploaded file is not a valid image.')
    finally:
        value.seek(0)

    expected_content_type = ALLOWED_IMAGE_FORMATS.get(image_format)
    if expected_content_type is None or (content_type and content_type != expected_content_type):
        raise ValidationError('The uploaded MIME type does not match the image content.')


class Department(models.Model):
    title = models.CharField(max_length=255)

    class Meta:
        ordering = ['title']
        indexes = [models.Index(fields=['title'])]

    def __str__(self):
        return self.title


class Club(models.Model):
    name = models.CharField(max_length=255)
    department = models.ForeignKey(
        Department,
        on_delete=models.CASCADE,
        related_name='clubs',
    )
    head = models.ForeignKey(
        'UserMember',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='headed_clubs',
    )
    class Meta:
        ordering = ['name']
        constraints = [
            models.UniqueConstraint(
                fields=['department', 'name'],
                name='unique_club_name_per_department',
            ),
        ]

    def __str__(self):
        return self.name


class ClubEvent(models.Model):
    name = models.CharField(max_length=255)
    description = models.TextField()
    parent_id = models.ForeignKey(
        Department,
        on_delete=models.CASCADE,
        related_name='clubs_events',
        db_index=False,
    )
    club = models.ForeignKey(
        Club,
        on_delete=models.CASCADE,
        related_name='events',
        null=True,
        blank=True,
    )

    class Meta:
        ordering = ['name']
        indexes = [models.Index(fields=['parent_id', 'name'])]

    def __str__(self):
        return self.name


class UserMember(models.Model):
    username = models.CharField(max_length=150, unique=True)
    user = models.OneToOneField(User, on_delete=models.CASCADE, null=True, blank=True)
    first_name = models.CharField(max_length=150, blank=True)
    last_name = models.CharField(max_length=150, blank=True)
    department_id = models.ForeignKey(
        Department,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='members',
    )
    club_id = models.ForeignKey(
        Club,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='members',
    )
    event_date = models.DateTimeField(null=True, blank=True)
    role = models.CharField(max_length=50, null=True, blank=True)
    image_path = models.ImageField(
        upload_to='avatars/',
        validators=[validate_file_size, validate_image_content],
        blank=True,
    )

    class Meta:
        indexes = [
            models.Index(fields=['department_id']),
            models.Index(fields=['club_id']),
            models.Index(fields=['event_date']),
        ]

    def __str__(self):
        return self.username