from django.shortcuts import render
#
# from education_app.utils import generate_mcqs
from .models import *
from .serializers import *
from rest_framework.permissions import IsAuthenticated,AllowAny
from rest_framework.response import Response
from rest_framework import status,viewsets,generics
from rest_framework.views import APIView
from rest_framework.decorators import api_view
import requests

# Create your views here.


class ParentRegistrationView(viewsets.ModelViewSet):
    queryset = Parent.objects.all()
    permission_classes = [AllowAny]
    serializer_class = UserRegisterSerializer
    http_method_names = ['post','patch']

    def create(self,request,*args,**kwargs):
        serializer = self.get_serializer(data=request.data)
        if serializer.is_valid():
            self.perform_create(serializer)
            response_data = {
                "status": "success",
                "message": "Parent created successfuly"
            }
            return Response(response_data,status=status.HTTP_200_OK)
        else:
            response_data = {
                "status": "failed",
                "message": "Invalid Details"
            }
            return Response(response_data,status=status.HTTP_400_BAD_REQUEST)


class ParentAddStudentView(viewsets.ModelViewSet):
    queryset = Student.objects.all()
    serializer_class = StudentRegisterSerializer
    http_method_names = ['post','patch']
    def create(self, request, *args, **kwargs):
        parent_id = request.data.get('parent') # Get parent ID from session
        
        # Add parent ID to the request data
        data = request.data.copy()
        data['parent'] = parent_id 

        serializer = self.get_serializer(data=data)
        if serializer.is_valid():
            self.perform_create(serializer)
            response_data = {
                "status": "success",
                "message": "Student created successfully"
            }
            return Response(response_data, status=status.HTTP_201_CREATED)
        else:
            response_data = {
                "status": "failed",
                "message": "Invalid details",
                "errors": serializer.errors
            }
            return Response(response_data, status=status.HTTP_400_BAD_REQUEST)


class LoginView(APIView):
    permission_classes = [AllowAny]

    def post(self, request, *args, **kwargs):
        serializer = LoginSerializer(data=request.data)
        if serializer.is_valid():
            email = serializer.validated_data.get('email')
            password = serializer.validated_data.get('password')

            # Check for Parent
            try:
                parent = Parent.objects.get(email=email)
                if password == parent.password:  # Ensure password is hashed in production
                    response_data = {
                        "status": "success",
                        "message": "Login Successful",
                        "user": {
                            "id": parent.id,
                            "name": parent.name,  # Assuming `name` is a field in Parent model
                            "email": parent.email,
                            "role": "parent",
                        }
                    }
                    request.session['id'] = parent.id
                    request.session['role'] = 'parent'
                    return Response(response_data, status=status.HTTP_200_OK)
                else:
                    return Response(
                        {"status": "failed", "message": "Invalid credentials"},
                        status=status.HTTP_401_UNAUTHORIZED,
                    )
            except Parent.DoesNotExist:
                pass

            # Check for Student
            try:
                student = Student.objects.get(email=email)
                if password == student.password:  # Ensure password is hashed in production
                    response_data = {
                        "status": "success",
                        "message": "Login Successful",
                        "user": {
                            "id": student.id,
                            "name": student.name,  # Assuming `name` is a field in Student model
                            "email": student.email,
                            "role": "student",
                        }
                    }
                    request.session['id'] = student.id
                    request.session['role'] = 'student'
                    return Response(response_data, status=status.HTTP_200_OK)
                else:
                    return Response(
                        {"status": "failed", "message": "Invalid credentials"},
                        status=status.HTTP_401_UNAUTHORIZED,
                    )
            except Student.DoesNotExist:
                pass

            # If no user found with the provided email
            return Response(
                {"status": "failed", "message": "User not found with the given email"},
                status=status.HTTP_404_NOT_FOUND,
            )

        else:
            return Response(
                {"status": "failed", "message": "Invalid input", "errors": serializer.errors},
                status=status.HTTP_400_BAD_REQUEST,
            )


class ParentViewChild(viewsets.ReadOnlyModelViewSet):
    queryset = Student.objects.all()
    serializer_class = ParentViewChildSerializer

    def list(self, request, *args, **kwargs):
        parent_id = request.query_params.get('parent_id')
        
        if not parent_id:
            return Response(
                {"detail": "Parent ID is required."}, 
                status=status.HTTP_400_BAD_REQUEST
            )
            
        try:
            parent = Parent.objects.get(id=parent_id)
        except Parent.DoesNotExist:
            return Response(
                {"detail": "Parent not found."}, 
                status=status.HTTP_404_NOT_FOUND
            )
            
        children = Student.objects.filter(parent=parent)
        serializer = self.get_serializer(children, many=True)
        
        return Response({
            "status": "success",
            "children": serializer.data
        }, status=status.HTTP_200_OK)

    def retrieve(self, request, pk=None, *args, **kwargs):
        parent_id = request.query_params.get('parent_id')
        
        if not parent_id:
            return Response(
                {"detail": "Parent ID is required."}, 
                status=status.HTTP_400_BAD_REQUEST
            )
            
        try:
            parent = Parent.objects.get(id=parent_id)
        except Parent.DoesNotExist:
            return Response(
                {"detail": "Parent not found."}, 
                status=status.HTTP_404_NOT_FOUND
            )
            
        try:
            child = Student.objects.get(id=pk, parent=parent)
        except Student.DoesNotExist:
            return Response(
                {"detail": "Student not found or does not belong to the parent."}, 
                status=status.HTTP_404_NOT_FOUND
            )
            
        serializer = self.get_serializer(child)
        return Response({
            "status": "success",
            "child": serializer.data
        }, status=status.HTTP_200_OK)
    
         
            
class StudentViewProfile(viewsets.ReadOnlyModelViewSet):
    queryset = Student.objects.all()
    serializer_class = StudentRegisterSerializer

    def list(self, request, *args, **kwargs):
        student_id = request.query_params.get('id')
        
        if student_id:
            student = Student.objects.filter(id=student_id).first()
            
            if student:  # If a student with the given ID exists
                serializer = self.get_serializer(student)
                return Response(serializer.data, status=status.HTTP_200_OK)
            else:  # If no student matches the given ID
                return Response({'error': 'Student not found'}, status=status.HTTP_404_NOT_FOUND)
        
        # If no student_id is provided, proceed with the default behavior
        return super().list(request, *args, **kwargs)


 
class AssignmentView(viewsets.ModelViewSet):
    queryset = Assignment.objects.all()
    serializer_class = AssignmentSerializer
    http_method_names = ['post']

    def create(self, request, *args, **kwargs):
        # Retrieve parent_id directly from the request data
        parent_id = request.data.get('parent_id')
        if not parent_id:
            return Response({"detail": "Parent ID is required."}, status=status.HTTP_400_BAD_REQUEST)

        try:
            parent = Parent.objects.get(id=parent_id)
        except Parent.DoesNotExist:
            return Response({"detail": "Parent not found."}, status=status.HTTP_404_NOT_FOUND)

        # Retrieve quiz_id from the request data
        quiz_id = request.data.get('quiz_id')
        if not quiz_id:
            return Response({"detail": "Quiz ID is required."}, status=status.HTTP_400_BAD_REQUEST)

        try:
            quiz = Quiz.objects.get(id=quiz_id)
        except Quiz.DoesNotExist:
            return Response({"detail": "Quiz not found."}, status=status.HTTP_404_NOT_FOUND)

        # Retrieve student_id from the request data
        student_id = request.data.get('student_id')
        if not student_id:
            return Response({"detail": "Student ID is required."}, status=status.HTTP_400_BAD_REQUEST)

        try:
            student = Student.objects.get(id=student_id)
        except Student.DoesNotExist:
            return Response({"message": "Student not found."}, status=status.HTTP_404_NOT_FOUND)

        # Create the assignment
        assignment = Assignment.objects.create(
            quiz=quiz,
            student=student,
            parent=parent
        )

        serializer = self.get_serializer(assignment)
        return Response(
            {"message": "Quiz assigned successfully.", "assignment": serializer.data},
            status=status.HTTP_201_CREATED
        )


class UpdateStudentProfileView(generics.UpdateAPIView):
    serializer_class = UpdateStudentProfileSerializer
    queryset = Student.objects.all()

    def update(self, request, *args, **kwargs):
        # Retrieve parent ID from session
        parent_id = request.data.get('parent_id')
        if not parent_id:
            return Response({"detail": "Parent ID is required."}, status=status.HTTP_400_BAD_REQUEST)

        try:
            parent = Parent.objects.get(id=parent_id)
        except Parent.DoesNotExist:
            return Response({"detail": "Parent not found."}, status=status.HTTP_404_NOT_FOUND)

        student_id = request.data.get('id')
        if not student_id:
            return Response({"detail": "Student ID is required."}, status=status.HTTP_400_BAD_REQUEST)

        try:
            student = Student.objects.get(id=student_id, parent=parent)
        except Student.DoesNotExist:
            return Response({"detail": "Student not found or does not belong to the parent."}, status=status.HTTP_404_NOT_FOUND)

        serializer = self.get_serializer(student, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        self.perform_update(serializer)

        return Response({"detail": "Student profile updated successfully."}, status=status.HTTP_200_OK)
    

class RemoveStudentView(viewsets.ModelViewSet):
    queryset = Student.objects.all()
    serializer_class = RemoveStudentSerializer

    def destroy(self, request, *args, **kwargs):
        student_id = request.data.get('id')
        try:
            student = Student.objects.get(id=student_id)
            student.delete()
            return Response({"detail": "Student removed successfully."}, status=status.HTTP_200_OK)
        except Student.DoesNotExist:
            return Response({"detail": "Student not found."}, status=status.HTTP_404_NOT_FOUND)
        

class ImageSearchView(APIView):
    def get(self, request, *args, **kwargs):
        # Retrieve the search keyword from the query parameters
        keyword = request.query_params.get('keyword')
        if not keyword:
            return Response({"detail": "Keyword is required."}, status=status.HTTP_400_BAD_REQUEST)

        # Search for the image and description using Wikimedia API
        search_results = self.search_online(keyword)
        if not search_results:
            return Response({"detail": "No results found."}, status=status.HTTP_404_NOT_FOUND)

        # Serialize the response
        serializer = ImageSearchSerializer(data=search_results)
        if serializer.is_valid():
            return Response(serializer.data, status=status.HTTP_200_OK)
        else:
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def search_online(self, keyword):
        """
        Function to search online for images and descriptions using Wikimedia API.
        """
        try:
            search_url = f"https://en.wikipedia.org/api/rest_v1/page/summary/{keyword}"
            response = requests.get(search_url)

            if response.status_code == 200:
                data = response.json()
                image_url = data.get('thumbnail', {}).get('source', None)
                description = data.get('extract', '')

                if not image_url or not description:
                    return None

                return {
                    "keyword": keyword,
                    "image_url": image_url,
                    "description": description,
                }
            else:
                return None
        except Exception as e:
            print(f"Error during search: {e}")
            return None
        


from django.http import JsonResponse
from django.conf import settings

def check_api_key(request):
    # Print the API key to confirm it's loaded correctly
    api_key = settings.GOOGLE_API_KEY
    print(f"API Key: {api_key}")  # In production, consider using logging instead of print()
    
    if api_key:
        return JsonResponse({"status": "API Key is set", "api_key": api_key})
    else:
        return JsonResponse({"status": "API Key is not set"})


from rest_framework import viewsets, status
from rest_framework.response import Response
from rest_framework.decorators import api_view

import google.generativeai as genai
genai.configure(api_key='AIzaSyAtc75Tn9EIWHvEwbFbH2YRHXDUe-m2f7c')

def generate_questions(topic, num_questions=5):
    """Generates MCQ questions using the Gemini API."""
    model_prompt = f"""Generate {num_questions} multiple-choice questions about {topic}, with 4 options for each question.
    Indicate the correct answer by prefixing it with an asterisk (*).
    Separate each question and its options with a newline.
    Example:
    Q: What is the capital of France?
    1. Berlin
    2. London
    *3. Paris
    4. Rome"""
    model = genai.GenerativeModel(
        model_name="gemini-1.5-flash-latest")
    response = model.generate_content(model_prompt)
    return response.text

def parse_questions(questions_text):
    questions = []
    lines_iter = iter(questions_text.split('\n'))
    for line in lines_iter:
        if line.startswith("Q:"):
            question = line[2:].strip()
            options = []
            correct_answer_index = None
            for i in range(1, 5):
                option_line = next(lines_iter, '')
                if option_line.startswith(f"{i}."):
                    options.append(option_line[2:].strip())
                if option_line.startswith(f"*{i}."):
                    options.append(option_line[3:].strip())
                    correct_answer_index = i
            questions.append({
                "question": question,
                "options": options,
                "correct_answer": correct_answer_index
            })
    return questions
@api_view(['POST'])
def quiz_view(request):
    if request.method == 'POST':
        try:
            topic = request.data['topic']
            num_questions = request.data.get('num_questions', 5)
            student_id = request.data['student_id']  # Assuming you pass the student ID in the request

            questions_text = generate_questions(topic, num_questions)
            questions = parse_questions(questions_text)

            # Create a quiz entry in the database
            student = Student.objects.get(id=student_id)  # Fetch the student object
            
            # Include the topic in the quiz_data
            quiz_data = {
                "topic": topic,
                "questions": questions
            }
            
            quiz = Quiz.objects.create(student=student, quiz_data=quiz_data)

            return Response({'quiz_id': quiz.id, 'quiz_data': quiz_data}, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

@api_view(['POST'])
def check_answers_view(request):
    if request.method == 'POST':
        try:
            questions = request.data['questions']
            user_answers = request.data['user_answers']

            score = 0
            for i, question_data in enumerate(questions):
                if user_answers[i] == question_data["correct_answer"]:
                    score += 1

            return Response({'score': score}, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

@api_view(['POST'])
def feedback_view(request):
    if request.method == 'POST':
        try:
            questions = request.data['questions']
            user_answers = request.data['user_answers']

            feedbacks = []
            areas = []
            for i, question_data in enumerate(questions):
                if user_answers[i] != question_data["correct_answer"]:
                    prompt = f"""
                    A student answered the following quiz question incorrectly. Analyze their answer and provide personalized feedback to help them understand the mistake and improve their knowledge:
                    Question: {question_data['question']}
                    User's Answer: {question_data['options'][user_answers[i] - 1]}
                    Correct Answer: {question_data['options'][question_data['correct_answer'] - 1]}
                    Focus on why the user's answers were incorrect and suggest specific areas or concepts they need to review.
                    """

                    model = genai.GenerativeModel(model_name="gemini-1.5-flash-latest")
                    response = model.generate_content(prompt)
                    feedback_area = response.text.strip()

                    try:
                        feedback, area = feedback_area.split('\n', 1)  # Assuming feedback and area are separated by a newline
                    except ValueError:
                        feedback = feedback_area
                        area = ""  # Set area to empty string if splitting fails

                    feedbacks.append(feedback)
                    areas.append(area)

            return Response({'feedbacks': feedbacks, 'areas': areas}, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)



@api_view(['POST'])
def store_response_view(request, quiz_id):
    if request.method == 'POST':
        try:
            # Fetch the quiz instance by ID
            quiz = Quiz.objects.get(id=quiz_id)
            
            # Get the response data from the request
            response_data = {
                "quiz": request.data.get('quiz'),
                "total_time": request.data.get('total_time'),
            }
            
            # Update the response field
            quiz.response = response_data
            quiz.save()  # Save the updated quiz instance
            
            # Serialize the updated quiz instance
            serializer = QuizSerializer(quiz)
            
            return Response(serializer.data, status=status.HTTP_200_OK)
        except Quiz.DoesNotExist:
            return Response({'error': 'Quiz not found'}, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)



@api_view(['GET'])
def student_assigned_quizzes(request, student_id):
    try:
        # Fetch assignments for the given student
        assignments = Assignment.objects.filter(student_id=student_id)

        if not assignments.exists():
            return Response({"detail": "No quizzes assigned to this student."}, status=status.HTTP_404_NOT_FOUND)

        # Serialize the data
        serializer = AssignmentSerializer(assignments, many=True)
        return Response({"assigned_quizzes": serializer.data}, status=status.HTTP_200_OK)
    except Exception as e:
        return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    

@api_view(['GET'])
def student_quiz_responses(request, student_id):
    try:
        # Fetch all quizzes assigned to the student
        quizzes = Quiz.objects.filter(student_id=student_id)

        if not quizzes.exists():
            return Response({"detail": "No quizzes found for this student."}, status=status.HTTP_404_NOT_FOUND)

        # Serialize the data
        serializer = QuizMinimalResponseSerializer(quizzes, many=True)
        return Response({"quizzes": serializer.data}, status=status.HTTP_200_OK)
    except Exception as e:
        return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)