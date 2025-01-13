import google.generativeai as genai
import os

# Authenticate with the Gemini API
genai.configure(api_key='AIzaSyAtc75Tn9EIWHvEwbFbH2YRHXDUe-m2f7c')

def generate_mcqs(prompt):
  """Generates MCQs from a prompt using the Gemini API."""
  prompt = """Generate multiple-choice questions from the following prompt.

# Get the prompte from the user
prompte = input("Please enter a prompt for generating MCQs: ")
each question must have a different answer
Format each question as follows:

Question: [Question text]

A. [Option A]
B. [Option B]
C. [Option C]
D. [Option D]

Answer: [Correct answer letter]"""

  model = genai.GenerativeModel(
  model_name="gemini-1.5-flash-latest")
  response = model.generate_content(prompt)
  return response.text

def get_user_name():
  """Gets the user's name."""
  name = input("Please enter your name: ")
  return name

def provide_suggestions(score, wrong_answers):
  """Provides suggestions based on the final score and wrong answers."""
  if score < 70:
    print("Your score is below average. Please review the following topics:")
    for answer in wrong_answers:
      print(f"- {answer}")
  else:
    print("Congratulations! Your score is above average.")

# Get the prompt from the user
prompte = input("Please enter a prompt for generating MCQs: ")

# Generate MCQs using the Gemini API
mcqs = generate_mcqs(prompte)

# Get the user's name
name = get_user_name()

# Display the MCQs to the user
print(f"Hello, {name}! Here are your MCQs:")
print(mcqs)

# Get the user's answers
answers = []
for i in range(len(mcqs)):
  answer = input(f"Enter your answer for question {i + 1}: ")
  answers.append(answer)

# Calculate the score
score = sum(1 for answer in answers if answer == 'A') / len(answers) * 100

# Provide suggestions based on the score
wrong_answers = [mcqs[i] for i, answer in enumerate(answers) if answer != 'A']
provide_suggestions(score, wrong_answers)