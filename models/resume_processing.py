def build_prompt():
  return """extract the following essential details from the given student's resume/CV. The output should be formatted as a JSON object with the specified keys. This information will help in matching the student with suitable job opportunities.

Required Information:

    name: The full name of the student.
    contact_information: An object containing the student's email address and phone number.
    education: A list of objects detailing the student's educational background.
    skills: A list of the student's key skills.
    work_experience: A list of objects detailing the student's work experience.
    projects: A list of objects detailing any relevant projects.
    certifications: A list of certifications the student has obtained.
    extracurricular_activities: A list of any extracurricular activities.
    languages: A list of languages the student speaks.
    personal_projects_and_hobbies: A list of personal projects and hobbies.
    publications_and_research: A list of publications and research.
    volunteer_experience: A list of volunteer experiences.
    awards_and_honors: A list of awards and honors.
    professional_development: A list of additional courses, workshops, or bootcamps attended.
    portfolio_or_github_link: URLs to the student's online portfolio or GitHub profile.
    soft_skills: A list of the student's soft skills.
    availability: The student's availability to start working."""