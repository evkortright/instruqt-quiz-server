#!/usr/bin/env python3
from flask import Flask, render_template_string, jsonify, request
import yaml
import re
import os
import glob

app = Flask(__name__)

# Determine the base directory (works whether running from repo or installed location)
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
QUESTIONS_DIR = os.path.join(BASE_DIR, 'questions')

def load_questions(course_name):
    """Load quiz questions from course-specific YAML file"""
    questions_file = os.path.join(QUESTIONS_DIR, f'{course_name}.yaml')
    
    try:
        with open(questions_file, 'r') as f:
            return yaml.safe_load(f)
    except FileNotFoundError:
        print(f"Questions file not found: {questions_file}")
        return None
    except Exception as e:
        print(f"Error loading questions from {questions_file}: {e}")
        return None

def get_available_courses():
    """Get list of available courses from question files"""
    courses = []
    pattern = os.path.join(QUESTIONS_DIR, '*.yaml')
    for filepath in glob.glob(pattern):
        course_name = os.path.basename(filepath).replace('.yaml', '')
        courses.append(course_name)
    return sorted(courses)

# HTML template
HTML_TEMPLATE = '''
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>{{ quiz.title }}</title>
    <style>
        body { 
            font-family: Arial, sans-serif; 
            padding: 40px;
            max-width: 900px;
            margin: 0 auto;
            background: #f9f9f9;
        }
        h1 {
            color: #333;
            margin-bottom: 30px;
        }
        .question { 
            margin: 20px 0;
            padding: 25px;
            background: white;
            border-radius: 8px;
            border: 2px solid #ddd;
            transition: all 0.3s ease;
        }
        .question.completed {
            background: #d4edda;
            border-color: #28a745;
        }
        .question h3 {
            margin-top: 0;
            color: #333;
        }
        .question.completed h3 {
            color: #155724;
        }
        input[type="text"], textarea { 
            width: 100%; 
            padding: 12px; 
            font-family: monospace;
            font-size: 14px;
            border: 2px solid #ddd;
            border-radius: 4px;
            margin-top: 10px;
            box-sizing: border-box;
        }
        textarea {
            min-height: 100px;
            resize: vertical;
        }
        .question.completed input[type="text"],
        .question.completed textarea {
            background: #f0f8f0;
            border-color: #28a745;
        }
        button { 
            padding: 12px 24px; 
            background: #0077cc; 
            color: white; 
            border: none; 
            cursor: pointer;
            border-radius: 4px;
            font-size: 16px;
            margin-top: 10px;
        }
        button:hover {
            background: #005fa3;
        }
        button.hidden {
            display: none;
        }
        .feedback { 
            margin-top: 15px; 
            padding: 15px; 
            border-radius: 4px;
            display: none;
        }
        .correct { 
            background: #d4edda; 
            color: #155724;
            border: 1px solid #c3e6cb;
        }
        .incorrect { 
            background: #f8d7da; 
            color: #721c24;
            border: 1px solid #f5c6cb;
        }
        .checkmark {
            color: #28a745;
            font-size: 20px;
            font-weight: bold;
            margin-left: 10px;
        }
        .progress {
            margin: 30px 0;
            padding: 20px;
            background: white;
            border-radius: 8px;
            border: 2px solid #ddd;
            text-align: center;
        }
        .progress h2 {
            margin: 0 0 10px 0;
            color: #333;
        }
        .progress-text {
            font-size: 18px;
            color: #666;
        }
        .progress.complete {
            background: #d4edda;
            border-color: #28a745;
        }
        .progress.complete h2 {
            color: #155724;
        }
    </style>
</head>
<body>
    <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 20px;">
        <h1 style="margin: 0;">{{ quiz.title }}</h1>
        <button onclick="resetQuiz()" style="background: #dc3545; padding: 10px 20px;">Reset Quiz</button>
    </div>
    
    <div class="progress" id="progress">
        <h2>Progress</h2>
        <p class="progress-text"><span id="completed">0</span> of {{ quiz.questions|length }} questions completed</p>
    </div>

    {% for question in quiz.questions %}
    <div class="question" id="q{{ question.id }}">
        <h3>Question {{ question.id }}: {{ question.title }}</h3>
        <p>{{ question.text|safe }}</p>
        {% if question.multiline %}
        <textarea id="answer{{ question.id }}" placeholder="{{ question.placeholder }}" rows="{{ question.rows|default(5) }}"></textarea>
        {% else %}
        <input type="text" id="answer{{ question.id }}" placeholder="{{ question.placeholder }}">
        {% endif %}
        <button onclick="checkAnswer({{ question.id }})" id="button{{ question.id }}">Check Answer</button>
        <div id="feedback{{ question.id }}" class="feedback"></div>
    </div>
    {% endfor %}

    <script>
        const TOTAL_QUESTIONS = {{ quiz.questions|length }};
        const COURSE_NAME = "{{ course_name }}";
        const LAB_ID = "{{ lab_id }}";
        let completedQuestions = new Set();

        function checkAnswer(questionNum) {
            const answer = document.getElementById('answer' + questionNum).value.trim();
            const feedback = document.getElementById('feedback' + questionNum);
            const questionDiv = document.getElementById('q' + questionNum);
            const button = document.getElementById('button' + questionNum);
            
            fetch('/validate', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    course_name: COURSE_NAME,
                    lab_id: LAB_ID,
                    question_id: questionNum,
                    answer: answer
                })
            })
            .then(response => response.json())
            .then(data => {
                feedback.style.display = 'block';
                
                if (data.correct) {
                    feedback.className = 'feedback correct';
                    
                    const heading = questionDiv.querySelector('h3');
                    if (!heading.querySelector('.checkmark')) {
                        heading.innerHTML += ' <span class="checkmark">&#10003;</span>';
                    }
                    
                    questionDiv.classList.add('completed');
                    completedQuestions.add(questionNum);
                    
                    button.classList.add('hidden');
                    document.getElementById('answer' + questionNum).disabled = true;
                    
                    feedback.innerHTML = '<strong>Correct!</strong> ' + data.message;
                    
                    updateProgress();
                } else {
                    feedback.className = 'feedback incorrect';
                    feedback.innerHTML = '<strong>Not quite.</strong> ' + data.message;
                }
            })
            .catch(error => {
                console.error('Error:', error);
                feedback.style.display = 'block';
                feedback.className = 'feedback incorrect';
                feedback.innerHTML = '<strong>Error:</strong> Could not validate answer.';
            });
        }

        function updateProgress() {
            const completed = completedQuestions.size;
            document.getElementById('completed').textContent = completed;
            
            const progressDiv = document.getElementById('progress');
            if (completed === TOTAL_QUESTIONS) {
                progressDiv.classList.add('complete');
                progressDiv.querySelector('.progress-text').innerHTML = 
                    '<strong style="color: #155724;">&#127881; All questions completed! Great work!</strong>';
                
                writeCompletionFile();
            }
        }

        function writeCompletionFile() {
            fetch('/complete', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    course_name: COURSE_NAME,
                    lab_id: LAB_ID
                })
            })
            .then(response => response.json())
            .then(data => {
                console.log('Quiz completion recorded:', data);
            })
            .catch(error => {
                console.error('Error recording completion:', error);
            });
        }

        function resetQuiz() {
            if (!confirm('Are you sure you want to reset this quiz? All progress will be lost.')) {
                return;
            }

            fetch('/reset', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    course_name: COURSE_NAME,
                    lab_id: LAB_ID
                })
            })
            .then(response => response.json())
            .then(data => {
                // Clear localStorage
                const storageKey = `quizProgress_${COURSE_NAME}_${LAB_ID}`;
                localStorage.removeItem(storageKey);
                
                // Reload the page to show fresh quiz
                alert('Quiz reset successfully!');
                location.reload();
            })
            .catch(error => {
                console.error('Error resetting quiz:', error);
                alert('Failed to reset quiz: ' + error.message);
            });
        }

        for (let i = 1; i <= TOTAL_QUESTIONS; i++) {
            const input = document.getElementById('answer' + i);
            if (input) {
                input.addEventListener('keypress', function(event) {
                    // Only submit on Enter for text inputs, not textareas
                    if (event.key === 'Enter' && this.tagName === 'INPUT') {
                        checkAnswer(i);
                    }
                });
            }
        }

        window.addEventListener('load', function() {
            const saved = localStorage.getItem('quizProgress_' + COURSE_NAME + '_' + LAB_ID);
            if (saved) {
                const savedAnswers = JSON.parse(saved);
                for (let qNum in savedAnswers) {
                    const input = document.getElementById('answer' + qNum);
                    if (input) {
                        input.value = savedAnswers[qNum];
                        checkAnswer(parseInt(qNum));
                    }
                }
            }
        });

        function saveProgress() {
            const answers = {};
            for (let i = 1; i <= TOTAL_QUESTIONS; i++) {
                const input = document.getElementById('answer' + i);
                if (input && input.value) {
                    answers[i] = input.value;
                }
            }
            localStorage.setItem('quizProgress_' + COURSE_NAME + '_' + LAB_ID, JSON.stringify(answers));
        }

        for (let i = 1; i <= TOTAL_QUESTIONS; i++) {
            const input = document.getElementById('answer' + i);
            if (input) {
                input.addEventListener('input', saveProgress);
            }
        }
    </script>
</body>
</html>
'''

ERROR_TEMPLATE = '''
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>Quiz Not Found</title>
    <style>
        body { 
            font-family: Arial, sans-serif; 
            padding: 40px;
            max-width: 900px;
            margin: 0 auto;
            background: #f9f9f9;
        }
        .error {
            padding: 20px;
            background: #f8d7da;
            color: #721c24;
            border: 1px solid #f5c6cb;
            border-radius: 8px;
        }
        h1 { color: #721c24; }
        h2 { color: #333; margin-top: 30px; }
        ul { margin-top: 10px; }
        li { margin: 5px 0; }
        a { color: #0077cc; text-decoration: none; }
        a:hover { text-decoration: underline; }
    </style>
</head>
<body>
    <div class="error">
        <h1>Quiz Not Found</h1>
        <p>The quiz "{{ course_name }}/{{ lab_id }}" could not be found.</p>
        
        {% if available_courses %}
        <h2>Available Courses:</h2>
        <ul>
        {% for course in available_courses %}
            <li><a href="/">{{ course }}</a></li>
        {% endfor %}
        </ul>
        {% else %}
        <p><strong>No courses available.</strong> Please check the questions directory.</p>
        {% endif %}
    </div>
</body>
</html>
'''

RESET_TEMPLATE = '''
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>Reset Quiz - {{ course_name }}/{{ lab_id }}</title>
    <style>
        body { 
            font-family: Arial, sans-serif; 
            padding: 40px;
            max-width: 700px;
            margin: 0 auto;
            background: #f9f9f9;
        }
        .reset-box {
            padding: 30px;
            background: white;
            border-radius: 8px;
            border: 2px solid #ddd;
            text-align: center;
        }
        h1 {
            color: #333;
            margin-bottom: 10px;
        }
        .quiz-info {
            color: #666;
            margin-bottom: 30px;
            font-size: 18px;
        }
        .warning {
            background: #fff3cd;
            border: 1px solid #ffc107;
            color: #856404;
            padding: 15px;
            border-radius: 4px;
            margin: 20px 0;
        }
        button {
            padding: 15px 30px;
            font-size: 16px;
            border: none;
            border-radius: 4px;
            cursor: pointer;
            margin: 10px;
        }
        .btn-reset {
            background: #dc3545;
            color: white;
        }
        .btn-reset:hover {
            background: #c82333;
        }
        .btn-cancel {
            background: #6c757d;
            color: white;
        }
        .btn-cancel:hover {
            background: #5a6268;
        }
        .message {
            margin-top: 20px;
            padding: 15px;
            border-radius: 4px;
            display: none;
        }
        .message.success {
            background: #d4edda;
            color: #155724;
            border: 1px solid #c3e6cb;
        }
        .message.error {
            background: #f8d7da;
            color: #721c24;
            border: 1px solid #f5c6cb;
        }
    </style>
</head>
<body>
    <div class="reset-box">
        <h1>Reset Quiz Progress</h1>
        <div class="quiz-info">
            <strong>{{ course_name }}</strong> / {{ lab_id }}
        </div>
        
        <div class="warning">
            <strong>⚠️ Warning:</strong> This will permanently delete your progress for this quiz.
            You will need to answer all questions again.
        </div>
        
        <p>This will reset:</p>
        <ul style="text-align: left; display: inline-block;">
            <li>Your saved answers in the browser</li>
            <li>The completion status on the server</li>
        </ul>
        
        <div>
            <button class="btn-reset" onclick="resetQuiz()">Reset Quiz</button>
            <button class="btn-cancel" onclick="goBack()">Cancel</button>
        </div>
        
        <div id="message" class="message"></div>
    </div>

    <script>
        const COURSE_NAME = "{{ course_name }}";
        const LAB_ID = "{{ lab_id }}";

        function resetQuiz() {
            if (!confirm('Are you sure you want to reset this quiz? This cannot be undone.')) {
                return;
            }

            const messageDiv = document.getElementById('message');
            messageDiv.style.display = 'none';

            fetch('/reset', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    course_name: COURSE_NAME,
                    lab_id: LAB_ID,
                    reset_all: false
                })
            })
            .then(response => response.json())
            .then(data => {
                // Clear localStorage
                const storageKey = `quizProgress_${COURSE_NAME}_${LAB_ID}`;
                localStorage.removeItem(storageKey);

                // Show success message
                messageDiv.className = 'message success';
                messageDiv.style.display = 'block';
                messageDiv.innerHTML = `
                    <strong>✓ Quiz Reset Successfully!</strong><br>
                    <p>Deleted files: ${data.deleted_files.length > 0 ? data.deleted_files.join(', ') : 'None'}</p>
                    <p>Browser storage cleared.</p>
                    <p><a href="/${COURSE_NAME}/${LAB_ID}">Return to quiz</a></p>
                `;
            })
            .catch(error => {
                console.error('Error:', error);
                messageDiv.className = 'message error';
                messageDiv.style.display = 'block';
                messageDiv.innerHTML = '<strong>✗ Error:</strong> Failed to reset quiz. ' + error.message;
            });
        }

        function goBack() {
            window.location.href = `/${COURSE_NAME}/${LAB_ID}`;
        }
    </script>
</body>
</html>
'''

@app.route('/')
def index():
    """Show available courses and labs"""
    courses = get_available_courses()
    
    if not courses:
        return f'<h1>No courses available</h1><p>Please check the questions directory at {QUESTIONS_DIR}</p>'
    
    html = '<html><head><meta charset="UTF-8"><title>Quiz Server</title><style>body{font-family:Arial,sans-serif;padding:40px;max-width:900px;margin:0 auto;}h1{color:#333;}ul{list-style:none;padding:0;}li{margin:10px 0;}a{color:#0077cc;text-decoration:none;font-size:16px;}a:hover{text-decoration:underline;}.course{font-weight:bold;font-size:18px;margin-top:20px;}.lab{margin-left:20px;}</style></head><body><h1>Quiz Server</h1><p>Available courses and labs:</p>'
    
    for course in courses:
        questions = load_questions(course)
        if questions:
            html += f'<div class="course">{course}</div><ul>'
            for lab_id in questions.keys():
                html += f'<li class="lab"><a href="/{course}/{lab_id}">{lab_id}</a> - {questions[lab_id]["title"]}</li>'
            html += '</ul>'
    html += '</body></html>'
    
    return html

@app.route('/<course_name>/<lab_id>')
def quiz(course_name, lab_id):
    """Serve quiz for specific course and lab"""
    questions = load_questions(course_name)
    
    if not questions:
        return render_template_string(ERROR_TEMPLATE, 
                                     course_name=course_name,
                                     lab_id=lab_id,
                                     available_courses=get_available_courses()), 404
    
    if lab_id not in questions:
        return render_template_string(ERROR_TEMPLATE, 
                                     course_name=course_name,
                                     lab_id=lab_id,
                                     available_courses=get_available_courses()), 404
    
    quiz_data = questions[lab_id]
    return render_template_string(HTML_TEMPLATE, 
                                 quiz=quiz_data, 
                                 course_name=course_name,
                                 lab_id=lab_id)

@app.route('/validate', methods=['POST'])
def validate():
    """Validate an answer"""
    data = request.json
    course_name = data.get('course_name')
    lab_id = data.get('lab_id')
    question_id = data.get('question_id')
    answer = data.get('answer', '').strip()
    
    questions = load_questions(course_name)
    
    if not questions or lab_id not in questions:
        return jsonify({'correct': False, 'message': 'Lab not found'}), 404
    
    quiz = questions[lab_id]
    question = next((q for q in quiz['questions'] if q['id'] == question_id), None)
    
    if not question:
        return jsonify({'correct': False, 'message': 'Question not found'}), 404
    
    for answer_pattern in question['answers']:
        pattern = answer_pattern['pattern']
        flags = answer_pattern.get('flags', '')
        
        regex_flags = 0
        if 'i' in flags:
            regex_flags |= re.IGNORECASE
        if 'm' in flags:
            regex_flags |= re.MULTILINE
        if 's' in flags:
            regex_flags |= re.DOTALL
        
        if re.search(pattern, answer, regex_flags):
            return jsonify({
                'correct': True,
                'message': question['correct_message']
            })
    
    return jsonify({
        'correct': False,
        'message': question['hint']
    })

@app.route('/complete', methods=['POST'])
def complete():
    """Mark quiz as complete and write completion file"""
    data = request.json
    course_name = data.get('course_name')
    lab_id = data.get('lab_id')
    
    completion_file = f'/root/quiz_complete_{course_name}_{lab_id}.txt'
    
    try:
        with open(completion_file, 'w') as f:
            f.write(f'Quiz {course_name}/{lab_id} completed successfully\n')
        
        return jsonify({
            'success': True,
            'message': f'Quiz {course_name}/{lab_id} marked as complete',
            'file': completion_file
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'message': str(e)
        }), 500

@app.route('/reset', methods=['POST'])
def reset():
    """Reset quiz progress - deletes completion file and clears localStorage"""
    data = request.json
    course_name = data.get('course_name')
    lab_id = data.get('lab_id')
    reset_all = data.get('reset_all', False)
    
    deleted_files = []
    errors = []
    
    try:
        if reset_all:
            # Delete all completion files
            import glob
            for filepath in glob.glob('/root/quiz_complete_*.txt'):
                try:
                    os.remove(filepath)
                    deleted_files.append(os.path.basename(filepath))
                except Exception as e:
                    errors.append(f"Failed to delete {filepath}: {str(e)}")
        else:
            # Delete specific completion file
            completion_file = f'/root/quiz_complete_{course_name}_{lab_id}.txt'
            if os.path.exists(completion_file):
                os.remove(completion_file)
                deleted_files.append(os.path.basename(completion_file))
        
        return jsonify({
            'success': True,
            'message': f'Quiz reset completed',
            'deleted_files': deleted_files,
            'errors': errors if errors else None,
            'localStorage_key': f'quizProgress_{course_name}_{lab_id}' if not reset_all else 'quizProgress_*'
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'message': str(e)
        }), 500

@app.route('/reset-page/<course_name>/<lab_id>')
def reset_page(course_name, lab_id):
    """Provide a simple page to reset a specific quiz"""
    return render_template_string(RESET_TEMPLATE, 
                                 course_name=course_name, 
                                 lab_id=lab_id)

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 8010))
    app.run(host='0.0.0.0', port=port, debug=False)