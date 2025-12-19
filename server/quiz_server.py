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
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', 'Roboto', 'Oxygen', 'Ubuntu', 'Cantarell', 'Fira Sans', 'Droid Sans', 'Helvetica Neue', sans-serif;
            padding: 40px;
            max-width: 1200px;
            margin: 0 auto;
            background: #1a1d24;
            color: #e5e7eb;
            line-height: 1.6;
        }
        h1 {
            color: #f9fafb;
            margin-bottom: 30px;
            font-size: 28px;
            font-weight: 600;
        }
        .question { 
            margin: 20px 0;
            padding: 25px;
            background: #272b33;
            border-radius: 8px;
            border: 1px solid #3b4048;
            transition: all 0.3s ease;
        }
        .question.completed {
            background: #1a3a2e;
            border-color: #2d5f4a;
        }
        .question h3 {
            margin-top: 0;
            color: #f9fafb;
            font-size: 18px;
            font-weight: 600;
        }
        .question.completed h3 {
            color: #86efac;
        }
        .question p {
            color: #d1d5db;
            margin: 10px 0;
        }
        input[type="text"], textarea { 
            width: 100%; 
            padding: 12px; 
            font-family: 'Monaco', 'Menlo', 'Ubuntu Mono', 'Consolas', 'source-code-pro', monospace;
            font-size: 14px;
            background: #1a1d24;
            color: #e5e7eb;
            border: 1px solid #3b4048;
            border-radius: 6px;
            margin-top: 10px;
            box-sizing: border-box;
        }
        input[type="text"]:focus, textarea:focus {
            outline: none;
            border-color: #6366f1;
            box-shadow: 0 0 0 2px rgba(99, 102, 241, 0.1);
        }
        textarea {
            min-height: 100px;
            resize: vertical;
        }
        .question.completed input[type="text"],
        .question.completed textarea {
            background: #1a3a2e;
            border-color: #2d5f4a;
        }
        button { 
            padding: 10px 20px; 
            color: white; 
            border: none; 
            cursor: pointer;
            border-radius: 6px;
            font-size: 14px;
            font-weight: 500;
            margin-top: 10px;
            transition: all 0.2s ease;
        }
        button:hover {
            transform: translateY(-1px);
            box-shadow: 0 4px 6px rgba(0, 0, 0, 0.3);
        }
        button:active {
            transform: translateY(0);
        }
        .question button {
            background: #7c3aed;
        }
        .question button:hover {
            background: #6d28d9;
        }
        button.hidden {
            display: none;
        }
        .feedback { 
            margin-top: 15px; 
            padding: 15px; 
            border-radius: 6px;
            display: none;
        }
        .correct { 
            background: #1a3a2e;
            color: #86efac;
            border: 1px solid #2d5f4a;
        }
        .incorrect { 
            background: #3a1a1a;
            color: #fca5a5;
            border: 1px solid #5f2d2d;
        }
        .checkmark {
            color: #86efac;
            font-size: 20px;
            font-weight: bold;
            margin-left: 10px;
        }
        .progress {
            margin: 30px 0;
            padding: 20px;
            background: #272b33;
            border-radius: 8px;
            border: 1px solid #3b4048;
            text-align: center;
        }
        .progress h2 {
            margin: 0 0 10px 0;
            color: #f9fafb;
            font-size: 20px;
            font-weight: 600;
        }
        .progress-text {
            font-size: 16px;
            color: #9ca3af;
        }
        .progress.complete {
            background: #1a3a2e;
            border-color: #2d5f4a;
        }
        .progress.complete h2 {
            color: #86efac;
        }
        .progress.complete .progress-text {
            color: #f0fdf4;
        }
        .progress.complete .progress-text strong {
            color: #f0fdf4;
        }
        .header-container {
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 20px;
        }
        .header-container h1 {
            margin: 0;
        }
        .reset-btn {
            background: #dc2626;
            padding: 10px 20px;
        }
        .reset-btn:hover {
            background: #b91c1c;
        }
        code {
            background: #1a1d24;
            color: #86efac;
            padding: 2px 6px;
            border-radius: 3px;
            font-family: 'Monaco', 'Menlo', 'Ubuntu Mono', 'Consolas', 'source-code-pro', monospace;
            font-size: 13px;
        }
    </style>
</head>
<body>
    <div class="header-container">
        <h1>{{ quiz.title }}</h1>
        <button class="reset-btn" onclick="resetQuiz()">Reset Quiz</button>
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
                location.reload();
            })
            .catch(error => {
                console.error('Error resetting quiz:', error);
                // Still clear localStorage and reload even if server call fails
                const storageKey = `quizProgress_${COURSE_NAME}_${LAB_ID}`;
                localStorage.removeItem(storageKey);
                location.reload();
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
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', 'Roboto', 'Oxygen', 'Ubuntu', 'Cantarell', 'Fira Sans', 'Droid Sans', 'Helvetica Neue', sans-serif;
            padding: 40px;
            max-width: 900px;
            margin: 0 auto;
            background: #1a1d24;
            color: #e5e7eb;
        }
        .error {
            padding: 20px;
            background: #3a1a1a;
            color: #fca5a5;
            border: 1px solid #5f2d2d;
            border-radius: 8px;
        }
        h1 { color: #fca5a5; font-weight: 600; }
        h2 { color: #f9fafb; margin-top: 30px; font-weight: 600; }
        ul { margin-top: 10px; }
        li { margin: 5px 0; }
        a { color: #60a5fa; text-decoration: none; }
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
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', 'Roboto', 'Oxygen', 'Ubuntu', 'Cantarell', 'Fira Sans', 'Droid Sans', 'Helvetica Neue', sans-serif;
            padding: 40px;
            max-width: 700px;
            margin: 0 auto;
            background: #1a1d24;
            color: #e5e7eb;
        }
        .reset-box {
            padding: 30px;
            background: #272b33;
            border-radius: 8px;
            border: 1px solid #3b4048;
            text-align: center;
        }
        h1 {
            color: #f9fafb;
            margin-bottom: 10px;
            font-size: 28px;
            font-weight: 600;
        }
        .quiz-info {
            color: #9ca3af;
            margin-bottom: 30px;
            font-size: 18px;
        }
        .warning {
            background: #3a2a1a;
            border: 1px solid #5f4a2d;
            color: #fbbf24;
            padding: 15px;
            border-radius: 6px;
            margin: 20px 0;
        }
        button {
            padding: 12px 24px;
            font-size: 14px;
            font-weight: 500;
            border: none;
            border-radius: 6px;
            cursor: pointer;
            margin: 10px;
            transition: all 0.2s ease;
        }
        button:hover {
            transform: translateY(-1px);
            box-shadow: 0 4px 6px rgba(0, 0, 0, 0.3);
        }
        .btn-reset {
            background: #dc2626;
            color: white;
        }
        .btn-reset:hover {
            background: #b91c1c;
        }
        .btn-cancel {
            background: #4b5563;
            color: white;
        }
        .btn-cancel:hover {
            background: #374151;
        }
        .message {
            margin-top: 20px;
            padding: 15px;
            border-radius: 6px;
            display: none;
        }
        .message.success {
            background: #1a3a2e;
            color: #86efac;
            border: 1px solid #2d5f4a;
        }
        .message.error {
            background: #3a1a1a;
            color: #fca5a5;
            border: 1px solid #5f2d2d;
        }
        ul {
            text-align: left;
            display: inline-block;
            color: #d1d5db;
        }
        a {
            color: #60a5fa;
            text-decoration: none;
        }
        a:hover {
            text-decoration: underline;
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
        <ul>
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
                
                // Still clear localStorage even if server call fails
                const storageKey = `quizProgress_${COURSE_NAME}_${LAB_ID}`;
                localStorage.removeItem(storageKey);
                
                messageDiv.className = 'message success';
                messageDiv.style.display = 'block';
                messageDiv.innerHTML = `
                    <strong>✓ Browser Storage Cleared!</strong><br>
                    <p>Server file deletion may have failed, but your progress has been reset.</p>
                    <p><a href="/${COURSE_NAME}/${LAB_ID}">Return to quiz</a></p>
                `;
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