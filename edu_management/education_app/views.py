from django.shortcuts import render
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
    http_method_names = ['post']

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
    http_method_names = ['post']
    def create(self, request, *args, **kwargs):
        parent_id = request.session.get('id')  # Get parent ID from session
        # if not parent_id:
        #     return Response(
        #         {"status": "failed", "message": "Parent not authenticated or session expired"},
        #         status=status.HTTP_401_UNAUTHORIZED
        #     )
        
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
        parent = request.session.get('id')
        children = Student.objects.filter(parent=parent)
        return super().list(children , *args, **kwargs) 
         
            
class QuizView(viewsets.ModelViewSet):
    queryset = Quiz.objects.all()
    serializer_class = QuizSerializer

    def create(self, request, *args, **kwargs):
        # Retrieve parent session ID
        parent_id = request.session.get('id')
        if not parent_id:
            return Response({"detail": "Parent authentication required."}, status=status.HTTP_401_UNAUTHORIZED)

        try:
            parent = Parent.objects.get(id=parent_id)
        except Parent.DoesNotExist:
            return Response({"detail": "Parent not found."}, status=status.HTTP_404_NOT_FOUND)

        # Get title and topic from the request
        title = request.data.get('title')
        topic = request.data.get('topic')

        if not title or not topic:
            return Response({"detail": "Title and topic are required."}, status=status.HTTP_400_BAD_REQUEST)

        # AI component generates questions
        questions = self.generate_ai_questions(topic)

        # Create the quiz
        quiz = Quiz.objects.create(
            title=title,
            topic=topic,
            questions=questions,
            created_by=parent
        )

        return Response({"detail": "Quiz created successfully.", "quiz": QuizSerializer(quiz).data}, status=status.HTTP_201_CREATED)


class QuizParticipationView(viewsets.ModelViewSet):
    queryset = QuizParticipation.objects.all()
    serializer_class = QuizParticipationSerializer

    def create(self, request, *args, **kwargs):
        quiz_id = request.data.get('quiz_id')
        student_id = request.data.get('student_id')

        if not quiz_id or not student_id:
            return Response({"detail": "Quiz ID and Student ID are required."}, status=status.HTTP_400_BAD_REQUEST)

        # Fetch the quiz and assignment
        try:
            quiz = Quiz.objects.get(id=quiz_id)
        except Quiz.DoesNotExist:
            return Response({"detail": "Quiz not found."}, status=status.HTTP_404_NOT_FOUND)

        try:
            assignment = Assignment.objects.get(quiz=quiz, student_id=student_id)
        except Assignment.DoesNotExist:
            return Response({"detail": "Assignment not found for the student and quiz."}, status=status.HTTP_404_NOT_FOUND)

        # Create the participation record
        participation = QuizParticipation.objects.create(
            assignment=assignment,
            score=0  # Initial score can be 0; it will be updated in the results.
        )

        return Response({"detail": "Participation created successfully.", "participation": QuizParticipationSerializer(participation).data}, status=status.HTTP_201_CREATED)
    

class ResultView(viewsets.ModelViewSet):
    queryset = Result.objects.all()
    serializer_class = ResultSerializer

    def update_results(self, request, *args, **kwargs):
        quiz_id = request.data.get('quiz_id')
        student_id = request.data.get('student_id')
        answers = request.data.get('answers')

        if not quiz_id or not student_id or not answers:
            return Response({"detail": "Quiz ID, Student ID, and answers are required."}, status=status.HTTP_400_BAD_REQUEST)

        # Fetch the quiz and assignment
        try:
            quiz = Quiz.objects.get(id=quiz_id)
        except Quiz.DoesNotExist:
            return Response({"detail": "Quiz not found."}, status=status.HTTP_404_NOT_FOUND)

        try:
            assignment = Assignment.objects.get(quiz=quiz, student_id=student_id)
        except Assignment.DoesNotExist:
            return Response({"detail": "Assignment not found for the student and quiz."}, status=status.HTTP_404_NOT_FOUND)

        # Calculate the score
        correct_answers = {q["question"]: q["answer"] for q in quiz.questions}
        score = sum(1 for question, answer in answers.items() if correct_answers.get(question) == answer)

        # Fetch or create a participation record
        participation, created = QuizParticipation.objects.get_or_create(
            assignment=assignment,
            defaults={"score": score}
        )

        # Store detailed results in the Result model
        result_data = {
            "quiz_id": quiz_id,
            "student_id": student_id,
            "score": score,
            "answers": answers,
            "correct_answers": correct_answers
        }
        result, created = Result.objects.get_or_create(
            participation=participation,
            defaults={"result_data": result_data}
        )

        # Update score if participation already existed
        if not created:
            participation.score = score
            participation.save()
            result.result_data = result_data
            result.save()

        return Response({"detail": "Results updated successfully.", "result": ResultSerializer(result).data}, status=status.HTTP_200_OK)


class AssignmentView(viewsets.ModelViewSet):
    queryset = Assignment.objects.all()
    serializer_class = AssignmentSerializer
    http_method_names = ['post']

    def create(self, request, *args, **kwargs):
        # Retrieve parent session ID
        parent_id = request.session.get('id')
        if not parent_id:
            return Response({"detail": "Parent authentication required."}, status=status.HTTP_401_UNAUTHORIZED)

        try:
            parent = Parent.objects.get(id=parent_id)
        except Parent.DoesNotExist:
            return Response({"detail": "Parent not found."}, status=status.HTTP_404_NOT_FOUND)

        # Validate the data and create the assignment using the serializer
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        # Save the assignment with the parent field populated
        serializer.save(parent=parent)

        return Response({"detail": "Quiz assigned successfully.", "assignment": serializer.data}, status=status.HTTP_201_CREATED)


class UpdateStudentProfileView(generics.UpdateAPIView):
    serializer_class = UpdateStudentProfileSerializer
    queryset = Student.objects.all()

    def update(self, request, *args, **kwargs):
        # Retrieve parent ID from session
        parent_id = request.session.get('id')  # Ensure this matches the key used to store parent ID

        if parent_id is None:
            return Response({"detail": "Parent ID not found in session."}, status=status.HTTP_403_FORBIDDEN)

        try:
            parent = Parent.objects.get(id=parent_id)
        except Parent.DoesNotExist:
            return Response({"detail": "Parent not found."}, status=status.HTTP_404_NOT_FOUND)

        # Retrieve the student ID from the request data
        student_id = request.data.get('id')
        if not student_id:
            return Response({"detail": "Student ID is required."}, status=status.HTTP_400_BAD_REQUEST)

        try:
            student = Student.objects.get(id=student_id, parent=parent)
        except Student.DoesNotExist:
            return Response({"detail": "Student not found or does not belong to the parent."}, status=status.HTTP_404_NOT_FOUND)

        # Proceed with profile update
        serializer = self.get_serializer(student, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        self.perform_update(serializer)

        return Response({"detail": "Student profile updated successfully."}, status=status.HTTP_200_OK)
    

class RemoveStudentView(viewsets.ModelViewSet):
    queryset = Student.objects.all()
    serializer_class = RemoveStudentSerializer

    def destroy(self, request, *args, **kwargs):
        student_id = request.data.get('id')
        student = student.objects.filter(id=student_id)
        student.delete()
        return Response({"detail": "Student removed successfully."}, status=status.HTTP_200_OK)
    

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
        
