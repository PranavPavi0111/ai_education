from django.db import models
from django.contrib.auth.models import AbstractUser
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.core.validators import MaxValueValidator, MinValueValidator
from django.forms import JSONField


# Create your models here.


class Parent(models.Model):
    name = models.CharField(max_length=100,default='')
    phone_number = models.CharField(max_length=15,default='')
    email = models.CharField(max_length=100,unique=True)
    password = models.CharField(max_length=100,default='')

class Student(models.Model):
    parent = models.ForeignKey(Parent,on_delete=models.CASCADE,related_name='parent')
    name = models.CharField(max_length=100,default='')
    phone_number = models.CharField(max_length=15,default='')
    email = models.CharField(max_length=100,unique=True)
    password = models.CharField(max_length=100,default='')
    department = models.CharField(max_length=50,default="")
    batch = models.CharField(max_length=100,default="")



class Image(models.Model):
    title = models.CharField(max_length=255)
    description = models.TextField()
    tags = models.CharField(max_length=255)
    image_url = models.URLField()


class PerformanceReport(models.Model):
    student = models.ForeignKey(Student, on_delete=models.CASCADE, related_name='performance_reports')
    report_data = models.JSONField()  # Store detailed performance data
    generated_at = models.DateTimeField(auto_now_add=True)


from django.db.models import JSONField



class Quiz(models.Model):
    student = models.ForeignKey(Student, on_delete=models.CASCADE, related_name='quizzes',blank=True)
    quiz_data = models.JSONField()  # To store the generated quiz, options, and correct answers
    response = models.JSONField(null=True, blank=True)  # To store the user's answers or feedback

    def __str__(self):
        return f"Quiz for {self.student.name}"
    

class Assignment(models.Model):
    quiz = models.ForeignKey(Quiz, on_delete=models.CASCADE, related_name='assignments')
    student = models.ForeignKey(Student, on_delete=models.CASCADE, related_name='assignments')
    parent = models.ForeignKey(Parent, on_delete=models.CASCADE, related_name='assignments')
    assigned_at = models.DateTimeField(auto_now_add=True)
