from .models import *
from rest_framework import serializers


class UserRegisterSerializer(serializers.ModelSerializer):
    class Meta:
        model = Parent
        fields = '__all__'

class StudentRegisterSerializer(serializers.ModelSerializer):
    class Meta:
        model = Student
        fields = '__all__'

class LoginSerializer(serializers.Serializer):
    email = serializers.EmailField()
    password = serializers.CharField(max_length=100)

class ParentViewChildSerializer(serializers.Serializer):
    class Meta:
        models = Student
        fields = ["name","departmnet"]

class UpdateStudentProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = Student
        fields = ['name', 'email', 'phone_number']

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

# class QuizParticipationSerializer(serializers.ModelSerializer):
#     class Meta:
#         model = QuizParticipation
#         fields = '__all__'

# class ResultSerializer(serializers.ModelSerializer):
#     class Meta:
#         model = Result
#         fields = '__all__'

class ImageSearchSerializer(serializers.Serializer):
    keyword = serializers.CharField(max_length=255)
    image_url = serializers.URLField()
    description = serializers.CharField()

    
class PerformanceReportSerializer(serializers.ModelSerializer):
    class Meta:
        model = PerformanceReport
        fields = '__all__'

class QuizQuestionSerializer(serializers.Serializer):
    question_text = serializers.CharField(max_length=255)
    options = serializers.ListField(child=serializers.CharField(max_length=255))
    correct_answer = serializers.IntegerField()

class QuizSerializer(serializers.ModelSerializer):
    quiz_data = QuizQuestionSerializer(many=True)

    class Meta:
        model = Quiz
        fields = ['topic', 'quiz_data']

class QuizMinimalResponseSerializer(serializers.ModelSerializer):
    class Meta:
        model = Quiz
        fields = ['id', 'response']
