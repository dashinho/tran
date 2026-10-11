from io import BytesIO

from django.core.exceptions import ValidationError
from django.core.files.uploadedfile import SimpleUploadedFile
from django.contrib.auth.models import User
from django.test import TestCase
from PIL import Image
from rest_framework.test import APIClient

from .models import Club, ClubEvent, Department, UserMember, validate_file_size, validate_image_content


class ImageValidationTests(TestCase):
	def test_file_size_limit_is_strictly_under_two_megabytes(self):
		upload = SimpleUploadedFile('avatar.png', b'x' * (2 * 1024 * 1024), content_type='image/png')

		with self.assertRaises(ValidationError):
			validate_file_size(upload)

	def test_image_mime_type_must_match_decoded_content(self):
		image_buffer = BytesIO()
		Image.new('RGB', (1, 1)).save(image_buffer, format='PNG')
		upload = SimpleUploadedFile(
			'avatar.png',
			image_buffer.getvalue(),
			content_type='image/jpeg',
		)

		with self.assertRaises(ValidationError):
			validate_image_content(upload)


class ClubEventFilterTests(TestCase):
	def setUp(self):
		self.client = APIClient()
		self.department = Department.objects.create(title='Technology')
		self.other_department = Department.objects.create(title='Arts')
		ClubEvent.objects.create(
			name='Tech Summit',
			description='Engineering talks',
			parent_id=self.department,
		)
		ClubEvent.objects.create(
			name='Gallery Night',
			description='Technology photography',
			parent_id=self.other_department,
		)

	def test_department_and_category_filters_are_combined(self):
		response = self.client.get(
			'/api/club-events/',
			{'department': self.department.pk, 'category': 'summit'},
		)

		self.assertEqual(response.status_code, 200)
		self.assertEqual(len(response.data), 1)
		self.assertEqual(response.data[0]['name'], 'Tech Summit')


class DepartmentAndMemberApiTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.department = Department.objects.create(title='Technology')

    def test_department_can_be_created_and_listed(self):
        create_response = self.client.post(
            '/api/departments/',
            {'title': 'Arts'},
            format='json',
        )

        self.assertEqual(create_response.status_code, 201)
        self.assertEqual(create_response.data['title'], 'Arts')
        self.assertEqual(Department.objects.count(), 2)

    def test_member_can_be_created_with_department(self):
        response = self.client.post(
            '/api/members/',
            {
                'username': 'alice',
                'department_id': self.department.pk,
                'role': 'President',
            },
            format='json',
        )

        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.data['username'], 'alice')
        self.assertEqual(response.data['department_id'], self.department.pk)
        self.assertEqual(UserMember.objects.get(username='alice').department_id, self.department)

    def test_signup_assigns_department_and_club_without_approval(self):
        club = Club.objects.create(name='Programming', department=self.department)

        response = self.client.post(
            '/api/signup/',
            {
                'username': 'new-user',
                'password': 'safe-password-123',
                'first_name': 'New',
                'last_name': 'User',
                'department_id': self.department.pk,
                'club_id': club.pk,
            },
            format='json',
        )

        self.assertEqual(response.status_code, 201)
        member = UserMember.objects.get(username='new-user')
        self.assertEqual(member.club_id, club)
        self.assertTrue(member.user.check_password('safe-password-123'))
        self.assertIn('token', response.data)
