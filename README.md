# Instruqt Quiz Server

A Flask-based quiz server for Instruqt labs that provides interactive knowledge checks with validation.

## Features

- Course-based organization with multiple labs per course
- YAML-based question configuration
- Regex-based answer validation
- Progress tracking and completion detection
- LocalStorage-based persistence

## Installation
```bash
# Clone the repository
git clone https://github.com/YOUR-USERNAME/instruqt-quiz-server.git /root/instruqt-quiz-server

# Install dependencies
pip3 install -r /root/instruqt-quiz-server/requirements.txt --break-system-packages

# Start the server
python3 /root/instruqt-quiz-server/server/quiz_server.py
```

## Usage in Instruqt

### Setup Script

Add this to your `setup-kubernetes-vm` script:
```bash
#!/bin/bash
set -euxo pipefail

# Clone the quiz server repository
git clone https://github.com/YOUR-USERNAME/instruqt-quiz-server.git /root/instruqt-quiz-server

# Install dependencies
pip3 install -r /root/instruqt-quiz-server/requirements.txt --break-system-packages

# Kill any existing server
pkill -f quiz_server.py || true
sleep 1

# Start the server
python3 /root/instruqt-quiz-server/server/quiz_server.py > /var/log/quiz_server.log 2>&1 &

# Wait for server to start
sleep 3

echo "Quiz server started on port 8008"
```

### Challenge Tab Configuration
```yaml
tabs:
- id: questions-tab
  title: Questions
  type: service
  hostname: kubernetes-vm
  path: /observability-intro/lab1
  port: 8008
```

### Check Script
```bash
#!/bin/bash
set -euxo pipefail

COURSE_NAME="observability-intro"
LAB_ID="lab1"

if [ -f "/root/quiz_complete_${COURSE_NAME}_${LAB_ID}.txt" ]; then
  echo "Quiz completed successfully!"
  exit 0
else
  fail-message "Please complete all quiz questions in the Questions tab before proceeding."
  exit 1
fi
```

## Question File Format

Questions are organized in YAML files under the `questions/` directory. Each file represents a course and contains multiple labs.

Example structure:
```yaml
lab1:
  title: "Lab 1 Title"
  questions:
    - id: 1
      title: "Question Title"
      text: "Question text (HTML allowed)"
      placeholder: "Placeholder text for input..."
      answers:
        - pattern: "regex_pattern"
          flags: "i"  # i for case-insensitive, m for multiline
      correct_message: "Message shown when correct"
      hint: "Hint shown when incorrect"
```

## Routes

- `/` - Lists all available courses and labs
- `/<course_name>/<lab_id>` - Displays quiz for specific lab
- `/validate` (POST) - Validates submitted answers
- `/complete` (POST) - Marks quiz as complete

## License

MIT License
