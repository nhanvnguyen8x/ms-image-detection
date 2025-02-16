def build_prompt(raw_content):
  return "What are the details of this job description: '" + str(raw_content) + """"'? 

Output this as a JSON object that can be readily processed in python with fixed keys of the following if you deem they exist:
Return each finding as a {} JSON structured output
job_title
listing_id (may be a job id or listing id from the given content, leave blank if none)
company_name
company_address
posted_by (this may be the company name, or recruitment agency/service)
posted_time (do your best to obtain in the format of '%Y-%m-%d %H:%M:%S' for python)
job_description (separate each description with [DESC] or take the whole paragraph)
job_responsibilities (separate each responsibility with [RESP] or take the whole paragraph)
questions_asked (separate each question with [QUESTION])
expectations (such as Minimum qualifications, culture fit, licenses or certifications required. If there are many segment them with [EXP] or take the whole paragraph)
job_location
contact_name
contact_handphone (determined from contact's name)
contact_email (determined from contact's name)
"""