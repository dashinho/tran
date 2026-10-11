from rest_framework import serializers

from django.contrib.auth.models import User
from rest_framework import serializers

from .models import Club, ClubEvent, Department, UserMember


class DepartmentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Department
        fields = ['id', 'title']


class ClubSerializer(serializers.ModelSerializer):
    class Meta:
        model = Club
        fields = ['id', 'name', 'department', 'head']
        read_only_fields = ['head']


class ClubEventSerializer(serializers.ModelSerializer):
    parent = serializers.CharField(source='parent_id.title', read_only=True)

    class Meta:
        model = ClubEvent
        fields = ['id', 'name', 'description', 'parent_id', 'club', 'parent']


class UserMemberSerializer(serializers.ModelSerializer):
    class Meta:
        model = UserMember
        fields = [
            'id',
            'username',
            'first_name',
            'last_name',
            'department_id',
            'club_id',
            'event_date',
            'role',
            'image_path',
        ]


class SignupSerializer(serializers.Serializer):
    username = serializers.CharField(max_length=150)
    password = serializers.CharField(write_only=True, min_length=8)
    first_name = serializers.CharField(max_length=150)
    last_name = serializers.CharField(max_length=150)
    department_id = serializers.PrimaryKeyRelatedField(
        queryset=Department.objects.all(),
    )
    club_id = serializers.PrimaryKeyRelatedField(
        queryset=Club.objects.all(),
    )

    def validate(self, attrs):
        if User.objects.filter(username=attrs['username']).exists():
            raise serializers.ValidationError({'username': 'This username is already in use.'})
        if attrs['club_id'].department_id != attrs['department_id'].id:
            raise serializers.ValidationError(
                {'club_id': 'The club must belong to the selected department.'}
            )
        return attrs

    def create(self, validated_data):
        password = validated_data.pop('password')
        department = validated_data.pop('department_id')
        club = validated_data.pop('club_id')
        username = validated_data.pop('username')
        user = User.objects.create_user(username=username, password=password, **validated_data)
        member = UserMember.objects.create(
            user=user,
            username=username,
            first_name=user.first_name,
            last_name=user.last_name,
            department_id=department,
            club_id=club,
        )
        member.club_id = club
        member.save(update_fields=['club_id'])
        return member