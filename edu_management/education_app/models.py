from django.db import models
from django.contrib.auth.models import AbstractUser
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.core.validators import MaxValueValidator, MinValueValidator


# Create your models here.


class Parent(models.Model):
    name = models.CharField(max_length=100,default='')
    phone_number = models.CharField(max_length=15,default='')
    email = models.CharField(max_length=100,unique=False)
    password = models.CharField(max_length=100,default='')

class Student(models.Model):
    parent = models.ForeignKey(Parent,on_delete=models.CASCADE,related_name='parent')
    name = models.CharField(max_length=100,default='')
    phone_number = models.CharField(max_length=15,default='')
    email = models.CharField(max_length=100,unique=True)
    password = models.CharField(max_length=100,default='')
    department = models.CharField(max_length=50,default="")
    batch = models.CharField(max_length=100,default="")


class Quiz(models.Model):
    title = models.CharField(max_length=100)
    topic = models.CharField(max_length=100)
    questions = models.JSONField()
    results = models.JSONField(null=True, blank=True) 
    created_by = models.ForeignKey(Parent, on_delete=models.CASCADE, related_name='quizzes')
    created_at = models.DateTimeField(auto_now_add=True)


class Assignment(models.Model):
    quiz = models.ForeignKey(Quiz, on_delete=models.CASCADE, related_name='assignments')
    student = models.ForeignKey(Student, on_delete=models.CASCADE, related_name='assignments')
    parent = models.ForeignKey(Parent, on_delete=models.CASCADE, related_name='assignments')
    assigned_at = models.DateTimeField(auto_now_add=True)


class QuizParticipation(models.Model):
    assignment = models.ForeignKey(Assignment, on_delete=models.CASCADE, related_name='participations')
    score = models.FloatField()
    completed_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Participation for {self.assignment} - Score: {self.score}"


class Result(models.Model):
    participation = models.OneToOneField(QuizParticipation, on_delete=models.CASCADE, related_name='result')
    result_data = models.JSONField()  # Store detailed result data

    def __str__(self):
        return f"Result for Participation ID: {self.participation.id}"

class Image(models.Model):
    title = models.CharField(max_length=255)
    description = models.TextField()
    tags = models.CharField(max_length=255)
    image_url = models.URLField()


class PerformanceReport(models.Model):
    student = models.ForeignKey(Student, on_delete=models.CASCADE, related_name='performance_reports')
    report_data = models.JSONField()  # Store detailed performance data
    generated_at = models.DateTimeField(auto_now_add=True)

