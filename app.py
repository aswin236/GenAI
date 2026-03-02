from flask import Flask, request, jsonify
import json
import os
from datetime import datetime

app = Flask(__name__)

DATA_FILE = "courses.json"

# Allowed status values
ALLOWED_STATUS = ["Not Started", "In Progress", "Completed"]


# ---------------------------------------------------
# Utility Functions
# ---------------------------------------------------

def initialize_file():
    """
    Create courses.json file automatically if it doesn't exist.
    """
    if not os.path.exists(DATA_FILE):
        try:
            with open(DATA_FILE, "w") as f:
                json.dump([], f)
        except Exception as e:
            print(f"Error creating file: {e}")


def load_courses():
    """
    Load all courses from JSON file.
    Returns list of courses.
    """
    try:
        with open(DATA_FILE, "r") as f:
            return json.load(f)
    except Exception as e:
        return None


def save_courses(courses):
    """
    Save course list back to JSON file.
    """
    try:
        with open(DATA_FILE, "w") as f:
            json.dump(courses, f, indent=4)
        return True
    except Exception as e:
        return False


def validate_course_data(data, is_update=False):
    """
    Validate course input data.
    - Checks required fields
    - Validates date format
    - Validates status value
    """

    required_fields = ["name", "description", "target_date", "status"]

    # For POST request (creation), all fields required
    if not is_update:
        for field in required_fields:
            if field not in data:
                return f"Missing required field: {field}"

    # Validate status
    if "status" in data and data["status"] not in ALLOWED_STATUS:
        return f"Invalid status. Allowed values: {ALLOWED_STATUS}"

    # Validate date format YYYY-MM-DD
    if "target_date" in data:
        try:
            datetime.strptime(data["target_date"], "%Y-%m-%d")
        except ValueError:
            return "Invalid target_date format. Use YYYY-MM-DD."

    return None


# ---------------------------------------------------
# REST API Endpoints
# ---------------------------------------------------

# 1️⃣ GET all courses
@app.route("/api/courses", methods=["GET"])
def get_all_courses():
    courses = load_courses()
    if courses is None:
        return jsonify({"error": "Error reading data file"}), 500
    return jsonify(courses), 200


# 2️⃣ GET specific course by ID
@app.route("/api/courses/<int:course_id>", methods=["GET"])
def get_course(course_id):
    courses = load_courses()
    if courses is None:
        return jsonify({"error": "Error reading data file"}), 500

    course = next((c for c in courses if c["id"] == course_id), None)
    if not course:
        return jsonify({"error": "Course not found"}), 404

    return jsonify(course), 200


# 3️⃣ POST create new course
@app.route("/api/courses", methods=["POST"])
def create_course():
    courses = load_courses()
    if courses is None:
        return jsonify({"error": "Error reading data file"}), 500

    data = request.get_json()

    if not data:
        return jsonify({"error": "Invalid JSON body"}), 400

    # Validate input
    error = validate_course_data(data)
    if error:
        return jsonify({"error": error}), 400

    # Auto-generate ID (incremental)
    new_id = 1
    if courses:
        new_id = max(course["id"] for course in courses) + 1

    # Create new course object
    new_course = {
        "id": new_id,
        "name": data["name"],
        "description": data["description"],
        "target_date": data["target_date"],
        "status": data["status"],
        "created_at": datetime.utcnow().isoformat()
    }

    courses.append(new_course)

    if not save_courses(courses):
        return jsonify({"error": "Error saving data"}), 500

    return jsonify(new_course), 201


# 4️⃣ PUT update course
@app.route("/api/courses/<int:course_id>", methods=["PUT"])
def update_course(course_id):
    courses = load_courses()
    if courses is None:
        return jsonify({"error": "Error reading data file"}), 500

    data = request.get_json()

    if not data:
        return jsonify({"error": "Invalid JSON body"}), 400

    # Validate (partial allowed, but must validate if provided)
    error = validate_course_data(data, is_update=True)
    if error:
        return jsonify({"error": error}), 400

    course = next((c for c in courses if c["id"] == course_id), None)
    if not course:
        return jsonify({"error": "Course not found"}), 404

    # Update only provided fields
    for key in ["name", "description", "target_date", "status"]:
        if key in data:
            course[key] = data[key]

    if not save_courses(courses):
        return jsonify({"error": "Error saving data"}), 500

    return jsonify(course), 200


# 5️⃣ DELETE course
@app.route("/api/courses/<int:course_id>", methods=["DELETE"])
def delete_course(course_id):
    courses = load_courses()
    if courses is None:
        return jsonify({"error": "Error reading data file"}), 500

    course = next((c for c in courses if c["id"] == course_id), None)
    if not course:
        return jsonify({"error": "Course not found"}), 404

    courses.remove(course)

    if not save_courses(courses):
        return jsonify({"error": "Error saving data"}), 500

    return jsonify({"message": "Course deleted successfully"}), 200

# 6️⃣ GET course statistics
@app.route("/api/courses/stats", methods=["GET"])
def get_course_stats():
    courses = load_courses()
    if courses is None:
        return jsonify({"error": "Error reading data file"}), 500

    # Initialize counters
    total_courses = len(courses)
    status_counts = {
        "Not Started": 0,
        "In Progress": 0,
        "Completed": 0
    }

    # Count courses by status
    for course in courses:
        status = course.get("status")
        if status in status_counts:
            status_counts[status] += 1

    # Build response
    stats = {
        "total_courses": total_courses,
        "status_breakdown": status_counts
    }

    return jsonify(stats), 200

# ---------------------------------------------------
# App Entry Point
# ---------------------------------------------------

if __name__ == "__main__":
    initialize_file()  # Ensure JSON file exists
    app.run(debug=True)
