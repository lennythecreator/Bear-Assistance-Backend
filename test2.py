from morgan_course_data.api import MorganCourseData
morgan_data = MorganCourseData(term="FALL_2024")

cosc_courses = morgan_data.get_courses_by_subject_abbreviation("COSC")

for course in cosc_courses:
    print(course.name, course.prerequisites, course.description)
