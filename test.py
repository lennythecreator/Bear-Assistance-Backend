from langchain_core.documents import Document
from morgan_course_data.api import MorganCourseData
from vector_store import vector_store
# Initialize the MorganCourseData with the desired term
morgan_data = MorganCourseData(term="FALL_2024")

# Fetch COSC courses
cosc_courses = morgan_data.get_courses_by_subject_abbreviation("COSC")

# Create documents for each course
course_documents = []

for course in cosc_courses:
    page_content = f"Name: {course.name}\n" \
                   f"Abbreviation: {course.subject_abbreviation}\n" \
                   f"Description: {course.description}\n" \
                   f"Number: {course.number}\n" \
                   f"Prerequisites: {course.prerequisites}"
    
    document = Document(page_content=page_content, metadata={"course_name": course.full_name})
    course_documents.append(document)

# Add course documents to the vector store
vector_store.add_documents(documents=course_documents)