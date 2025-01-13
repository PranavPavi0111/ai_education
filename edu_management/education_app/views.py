from django.shortcuts import render

from education_app.utils import generate_mcqs
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
        


# from django.http import JsonResponse
# from django.conf import settings

# def check_api_key(request):
#     # Print the API key to confirm it's loaded correctly
#     api_key = settings.GOOGLE_API_KEY
#     print(f"API Key: {api_key}")  # In production, consider using logging instead of print()
    
#     if api_key:
#         return JsonResponse({"status": "API Key is set", "api_key": api_key})
#     else:
#         return JsonResponse({"status": "API Key is not set"})


# # def generate_mcqs(prompt):
# #     """Generates MCQs from a prompt using the Gemini API."""
# #     generation_prompt = f"""
# #     Generate multiple-choice questions based on the following text:

# #     {prompt}

# #     Format:
# #     Question: [Your question here]
# #     A. [Option A]
# #     B. [Option B]
# #     C. [Option C]
# #     D. [Option D]
# #     Answer: [Correct answer]
# #     """
# #     try:
# #         # Use the Gemini model to generate MCQs
# #         model = genai.GenerativeModel(model_name="gemini-1.5-flash-latest")
# #         response = model.generate_content(generation_prompt)
# #         return response.text
# #     except Exception as e:
# #         return f"Error generating MCQs: {e}"

# # @csrf_exempt
# # def generate_mcqs_view(request):
# #     """Django view to handle MCQ generation."""
# #     if request.method == "POST":
# #         try:
# #             # Parse the incoming JSON payload
# #             body = json.loads(request.body)
# #             prompt = body.get("prompt")

# #             if not prompt:
# #                 return JsonResponse({"error": "Prompt is required."}, status=400)

# #             # Generate MCQs
# #             mcqs = generate_mcqs(prompt)

# #             # Return the MCQs as a response
# #             return JsonResponse({"status": "success", "mcqs": mcqs})

# #         except json.JSONDecodeError:
# #             return JsonResponse({"error": "Invalid JSON payload."}, status=400)
    
# #     return JsonResponse({"error": "Invalid request method."}, status=405)

# import google.generativeai as genai
# import re
# from django.http import JsonResponse
# from django.views.decorators.csrf import csrf_exempt

# # Authenticate with the Gemini API
# genai.configure(api_key="AIzaSyAtc75Tn9EIWHvEwbFbH2YRHXDUe-m2f7c")

# # Function to generate MCQs
# def generate_questions(topic, num_questions=5):
#     """Generates MCQ questions using the Gemini API."""
#     model_prompt = f"""Generate {num_questions} multiple-choice questions about {topic}, with 4 options for each question.
#     Indicate the correct answer by prefixing it with an asterisk (*).
#     Separate each question and its options with a newline.
#     Example:
#     Q: What is the capital of France?
#     1. Berlin
#     2. London
#     *3. Paris
#     4. Rome"""
    
#     model = genai.GenerativeModel(model_name="gemini-1.5-flash-latest")
#     response = model.generate_content(model_prompt)
#     return response.text

# def parse_questions(response_text):
#     """Parse the generated questions and options from the AI response."""
#     questions = []
#     question_blocks = response_text.split('\n\n')  # Split by double newline for each question block
    
#     for block in question_blocks:
#         # Match the question and options using regex
#         match = re.match(r'Q: (.+)', block)
#         if match:
#             question = match.group(1).strip()
#             options = []
#             correct_answer = None

#             # Extract options and identify the correct one
#             for i in range(1, 5):
#                 option_match = re.search(f"({i})\. (.+)", block)
#                 if option_match:
#                     option_text = option_match.group(2).strip()
#                     options.append(option_text)
#                     if option_text.startswith('*'):  # Check if the option is correct
#                         correct_answer = i

#             # Remove '*' from correct answer option
#             if correct_answer:
#                 options[correct_answer - 1] = options[correct_answer - 1][1:].strip()  # Remove '*' from option

#             questions.append({
#                 "question": question,
#                 "options": options,
#                 "correct_answer": correct_answer
#             })
    
#     return questions

# # Main endpoint to handle quiz generation and submission
# @csrf_exempt
# def quiz_view(request):
#     if request.method == 'POST':
#         topic = request.POST.get('topic')
#         questions_text = generate_questions(topic)
#         questions = parse_questions(questions_text)

#         # Start the quiz logic
#         user_answers = []
#         for question_data in questions:
#             # Here you can return the questions as JSON to the frontend
#             # For simplicity, let's print them for now
#             print(f"Question: {question_data['question']}")
#             for i, option in enumerate(question_data['options']):
#                 print(f"{i + 1}. {option}")

#         return JsonResponse({
#             'questions': questions
#         })

#     return JsonResponse({
#         'error': 'Invalid request method. Please use POST.'
#     }, status=400)

# def check_answer(question_data, user_answer):
#     """Checks if the user's answer is correct."""
#     return user_answer == question_data["correct_answer"]

# def provide_suggestions(questions, user_answers):
#     """Provides suggestions for incorrect answers."""
#     feedback = []
#     for i, question_data in enumerate(questions):
#         if user_answers[i] != question_data["correct_answer"]:
#             feedback.append({
#                 "question": question_data['question'],
#                 "your_answer": question_data["options"][user_answers[i] - 1],
#                 "correct_answer": question_data["options"][question_data['correct_answer'] - 1]
#             })
#     return feedback

# def generate_feedback(question_data, user_answer):
#     """Generate personalized feedback using Gemini API."""
#     prompt = f"""
#     A student answered the following quiz question incorrectly. Analyze their answer and provide personalized feedback to help them understand the mistake and improve their knowledge:
#     Question: {question_data['question']}
#     User's Answer: {question_data['options'][user_answer - 1]}
#     Correct Answer: {question_data['options'][question_data['correct_answer'] - 1]}
#     Focus on why the user's answer was incorrect and suggest specific areas or concepts they need to review.
#     """
#     model = genai.GenerativeModel(model_name="gemini-1.5-flash-latest")
#     response = model.generate_content(prompt)
#     feedback_area = response.text.strip()

#     # Parse feedback and suggestions
#     try:
#         feedback, area = feedback_area.split('\n', 1)  # Assuming feedback and area are separated by a newline
#         return feedback, area
#     except ValueError:
#         return feedback_area, None


import google.generativeai as genai
import os

# Authenticate with the Gemini API
genai.configure(api_key='AIzaSyAtc75Tn9EIWHvEwbFbH2YRHXDUe-m2f7c')

def generate_mcqs(prompt):
    """Generates MCQs from a prompt using the Gemini API."""
    model_prompt = f"""Generate multiple-choice questions based on the following prompt: {prompt}.
Each question should have four options and one correct answer. Format each question as follows:

Question: [Question text]
A. [Option A]
B. [Option B]
C. [Option C]
D. [Option D]
Answer: [Correct answer letter]"""

    model = genai.GenerativeModel(model_name="gemini-1.5-flash-latest")
    response = model.generate_content(model_prompt)
    return response.text



def provide_suggestions(score, wrong_answers):
    """Provides suggestions based on the final score and wrong answers."""
    if score < 70:
        print("Your score is below average. Please review the following topics:")
        for answer in wrong_answers:
            print(f"- {answer}")
    else:
        print("Congratulations! Your score is above average.")

def display_mcqs(mcqs_text):
    """Displays MCQs from the generated text."""
    questions = mcqs_text.split('\n')
    mcqs = []
    for i in range(0, len(questions), 6):  # Assuming 6 lines per question (question + 4 options + answer)
        question = questions[i].split(":")[1].strip()  # Extract question
        options = [questions[i + j].split(".")[1].strip() for j in range(1, 5)]  # Extract options
        answer = questions[i + 5].split(":")[1].strip()  # Extract the answer
        mcqs.append({
            "question": question,
            "options": options,
            "correct_answer": answer
        })
    return mcqs

def main():
    # Get the prompt from the user
    prompt = input("Please enter a prompt for generating MCQs: ")

    # Generate MCQs using the Gemini API
    mcqs_text = generate_mcqs(prompt)

    # Get the user's name
    name = get_user_name()

    # Display the MCQs to the user
    print(f"Hello, {name}! Here are your MCQs:")

    mcqs = display_mcqs(mcqs_text)

    # Get the user's answers
    answers = []
    for i, mcq in enumerate(mcqs):
        print(f"Question {i + 1}: {mcq['question']}")
        for idx, option in enumerate(mcq['options'], 1):
            print(f"{idx}. {option}")
        user_answer = input("Enter your answer (1-4): ")
        answers.append(user_answer)

    # Calculate the score
    score = 0
    wrong_answers = []
    for i, mcq in enumerate(mcqs):
        if answers[i] == mcq["correct_answer"]:
            score += 1
        else:
            wrong_answers.append(mcq["question"])

    # Provide suggestions based on the score
    provide_suggestions(score, wrong_answers)

    # Final score
    print(f"\nYour final score is: {score}/{len(mcqs)}")

if __name__ == "__main__":
    main()







