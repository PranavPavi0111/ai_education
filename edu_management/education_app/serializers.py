from .models import *
from rest_framework import serializers

class UserRegisterSerializer(serializers.ModelSerializer):
    class Meta:
        model = Parent
        fields = '__all__'
        read_only_fields = ['id']

    def validate_email(self, value):
        """
        Custom validation for the email field to ensure uniqueness.
        """
        # if self.instance:  # Check during updates
        #     if Parent.objects.filter(email=value).exclude(id=self.instance.id).exists():
        #         raise serializers.ValidationError("A parent with this email already exists.")
        # else:  # Check during creation
        #     if Parent.objects.filter(email=value).exists():
        #         raise serializers.ValidationError("A parent with this email already exists.")
        return value


class StudentRegisterSerializer(serializers.ModelSerializer):
    class Meta:
        model = Student
        fields = '__all__'

class LoginSerializer(serializers.Serializer):
    email = serializers.EmailField()
    password = serializers.CharField(max_length=100)

class ParentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Parent
        fields = ['id', 'name', 'phone_number', 'email']  

class StudentSerializer(serializers.ModelSerializer):
    parent = ParentSerializer()  

    class Meta:
        model = Student
        fields = ['id', 'name', 'phone_number', 'email', 'department', 'batch', 'parent']

class UpdateStudentProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = Student
        fields = ['name', 'email', 'phone_number', 'department', 'batch']

class RemoveStudentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Student
        fields = '__all__'

class QuizSerializer(serializers.ModelSerializer):
    class Meta:
        model = Quiz
        fields = '__all__'

class AssignmentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Assignment
        fields = '__all__'

class QuizParticipationSerializer(serializers.ModelSerializer):
    class Meta:
        model = QuizParticipation
        fields = '__all__'

class ResultSerializer(serializers.ModelSerializer):
    class Meta:
        model = Result
        fields = '__all__'

class ImageSearchSerializer(serializers.Serializer):
    keyword = serializers.CharField(max_length=255)
    image_url = serializers.URLField()
    description = serializers.CharField()

    
class PerformanceReportSerializer(serializers.ModelSerializer):
    class Meta:
        model = PerformanceReport
        fields = '__all__'
