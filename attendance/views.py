import logging
from django.shortcuts import render, redirect
from django.http import StreamingHttpResponse, JsonResponse
from .models import Student, AttendanceRecord
from .forms import StudentForm,CustomAuthenticationForm
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth import login, logout
from django.contrib.auth.decorators import login_required
import face_recognition
import cv2
import numpy as np
from datetime import datetime
from django.contrib.auth.decorators import user_passes_test
from django.contrib.auth.models import User


# Configure logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

class VideoCamera:
    def __init__(self):
        self.video = None
        self.known_face_encodings = []
        self.known_face_names = []
        self.running = False
        self.load_known_faces()

    def __del__(self):
        self.release()

    def release(self):
        if self.video and self.video.isOpened():
            self.video.release()
            logger.debug("Released video capture")

    def load_known_faces(self):
        students = Student.objects.all()
        for student in students:
            try:
                image = face_recognition.load_image_file(student.image.path)
                encoding = face_recognition.face_encodings(image)[0]
                self.known_face_encodings.append(encoding)
                self.known_face_names.append(student.name)
                logger.debug(f"Loaded face encoding for {student.name}")
            except Exception as e:
                logger.error(f"Error loading student image for {student.name}: {e}")

    def get_frame(self):
        if self.video is None or not self.video.isOpened():
            logger.error("Video capture device is not initialized or not opened.")
            return b''

        success, frame = self.video.read()
        if not success:
            logger.error("Failed to capture frame from video stream")
            return b''

        small_frame = cv2.resize(frame, (0, 0), fx=0.25, fy=0.25)
        rgb_small_frame = cv2.cvtColor(small_frame, cv2.COLOR_BGR2RGB)

        face_locations = face_recognition.face_locations(rgb_small_frame)
        face_encodings = face_recognition.face_encodings(rgb_small_frame, face_locations)

        for face_encoding in face_encodings:
            matches = face_recognition.compare_faces(self.known_face_encodings, face_encoding)
            face_distance = face_recognition.face_distance(self.known_face_encodings, face_encoding)
            best_match_index = np.argmin(face_distance)

            if matches[best_match_index]:
                name = self.known_face_names[best_match_index]

                font = cv2.FONT_HERSHEY_SIMPLEX
                bottomLeftCornerOfText = (10, 100)
                fontScale = 1.5
                fontColor = (255, 0, 0)
                thickness = 3
                lineType = 2

                cv2.putText(frame, name + " Present", bottomLeftCornerOfText, font, fontScale, fontColor, thickness, lineType)

                try:
                    student = Student.objects.get(name=name)
                    today = datetime.today().date()
                    if not AttendanceRecord.objects.filter(student=student, date=today).exists():
                        AttendanceRecord.objects.create(student=student)
                        logger.debug(f"Recorded attendance for {student.name} on {today}")
                except Student.DoesNotExist:
                    logger.error(f"Student with name {name} does not exist.")
                except Exception as e:
                    logger.error(f"Error creating attendance record for {name}: {e}")

        _, jpeg = cv2.imencode('.jpg', frame)
        return jpeg.tobytes()

    def start_camera(self):
        if self.video is None:
            self.video = cv2.VideoCapture(0)
        if not self.video.isOpened():
            self.video.open(0)
        self.running = True
        logger.debug("Started video capture")

    def stop_camera(self):
        self.running = False
        self.release()
        logger.debug("Stopped video capture")

def index(request):
    students = Student.objects.all()
    return render(request, 'attendance/index.html', {'students': students})

camera = VideoCamera()

def gen(camera):
    try:
        while camera.running:
            frame = camera.get_frame()
            yield (b'--frame\r\n'
                   b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n\r\n')
    finally:
        camera.release()

def video_feed(request):
    if camera.running:
        return StreamingHttpResponse(gen(camera), content_type='multipart/x-mixed-replace; boundary=frame')
    else:
        return JsonResponse({'status': 'Camera is not running'})

def start_camera(request):
    camera.start_camera()
    return JsonResponse({'status': 'Camera started'})

def stop_camera(request):
    camera.stop_camera()
    return JsonResponse({'status': 'Camera stopped'})

def success(request):
    return render(request, 'attendance/success.html')

def upload_student(request):
    if request.method == 'POST':
        form = StudentForm(request.POST, request.FILES)
        if form.is_valid():
            form.save()
            return redirect('success')
    else:
        form = StudentForm()
    return render(request, 'attendance/upload_student.html', {'form': form})

# def attendance_view(request):
#     # Retrieve attendance records
#     attendance_records = AttendanceRecord.objects.all()

#     # Prepare data to pass to template
#     context = {
#         'attendance_records': attendance_records,
#     }

#     return render(request, 'attendance/attendance.html', context)


def register(request):
    if request.method == 'POST':
        form = UserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            return redirect('index')
    else:
        form = UserCreationForm()
    return render(request, 'attendance/register.html', {'form': form})

def login_view(request):
    if request.method == 'POST':
        form = CustomAuthenticationForm(data=request.POST)
        if form.is_valid():
            user = form.get_user()
            login(request, user)
            return redirect('index')  # Replace 'index' with your desired redirect URL after login
    else:
        form = CustomAuthenticationForm()
    return render(request, 'attendance/login.html', {'form': form})
@login_required
def logout_view(request):
    if request.method == 'POST':
        logout(request)
        return redirect('login')
    return render(request, 'attendance/logged_out.html')

def attendance_view(request):
    records = AttendanceRecord.objects.all()

    name_filter = request.GET.get('name')
    date_filter = request.GET.get('date')

    if name_filter:
        records = records.filter(student__name__icontains=name_filter)
    if date_filter:
        records = records.filter(date=date_filter)

    return render(request, 'attendance/attendance.html', {
        'attendance_records': records,
    })
@user_passes_test(lambda u: u.is_superuser)
def admin_users(request):
    users = User.objects.all()
    return render(request, 'attendance/users.html', {'users': users})

