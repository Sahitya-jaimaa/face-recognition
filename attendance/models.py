from django.db import models

class Student(models.Model):
    name = models.CharField(max_length=100)
    image = models.ImageField(upload_to='faces/')

    def __str__(self):
        return self.name

class AttendanceRecord(models.Model):
    student = models.ForeignKey(Student, on_delete=models.CASCADE)
    date = models.DateField(auto_now_add=True)
    time = models.TimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.student.name} - {self.date} {self.time}"

