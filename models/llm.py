import json
import shutil
import traceback
import uuid
import pandas as pd
from langchain_community.callbacks.manager import get_openai_callback
from langchain_community.vectorstores import Chroma

from models import claims_processing, jd_processing, resume_processing
from models.claims_processing import process_total_amount, process_receipt_datetime

import os

from models.modules import EMBEDDINGS_BGE_BASE
from models.modules.database import KnowledgeBase
from dotenv import load_dotenv
from models.modules.main import Chatbase
from langchain.schema import Document
from langchain.text_splitter import CharacterTextSplitter
from typing import List
from docx import Document as Doc

from service.aws_ocr import AwsOcrService
import pandas as pd
import json
import traceback
from concurrent.futures import ThreadPoolExecutor, as_completed
import openpyxl

load_dotenv()

kb = KnowledgeBase()
aws_ocr = AwsOcrService()


def init_chat_obj():
    Chat = Chatbase(EMBEDDINGS_BGE_BASE)
    return Chat


def init_vector_db(EMBEDDINGS_BGE_BASE, persist_dir):
    vectordb = Chroma(persist_directory=persist_dir, embedding_function=EMBEDDINGS_BGE_BASE)
    return vectordb


def ask(query, chat_obj):
    with get_openai_callback() as cb:
        chain_resp = chat_obj.ask(query)
        # print(chain_resp)

        resp = {
            "response": chain_resp.content,
            "prompt": cb.prompt_tokens,
            "completion": cb.completion_tokens,
            "cost": cb.total_cost,
            # "source_documents": []
            # "source_documents": chain_resp.
        }
        return resp

def ask_chat(query, chat_obj, vectordb):
    with get_openai_callback() as cb:
        chain_resp, source_documents = chat_obj.doc_chat(query, vectordb)
        # print(chain_resp)

        resp = {
            "response": chain_resp,
            "prompt": cb.prompt_tokens,
            "completion": cb.completion_tokens,
            "cost": cb.total_cost,
            "source_documents": source_documents
            # "source_documents": chain_resp.
        }
        return resp


def get_text_chunks_langchain(text, source='adhoc'):
    text_splitter = CharacterTextSplitter(chunk_size=500, chunk_overlap=100)
    docs = [Document(page_content=x, metadata={'source': source}) for x in text_splitter.split_text(text)]

    return docs


def process_text_string(text: str, source: str) -> List[Document]:
    return get_text_chunks_langchain(text, source)


def embed_textstr_type(text_str, persist_path, source):
    texts = process_text_string(text_str, source)
    cb = Chatbase()
    embed = cb.embed(persist_path, texts)
    return embed


def ingest_text_str(text_str, job_name):
    # text_path = "{}.txt".format(save_path)
    persist_path = os.environ.get("PERSIST_PATH") + "/{}".format(job_name)

    # this saves it as a temporary text file
    # embed_text(text_path, persist_path)
    embed_textstr_type(text_str, persist_path, 'Adhoc')

    # how to remove embedded?
    # if kb.entry_exists(job_name):
    #     print("Entry already exists..")
    #     kb.insert_entry(job_name, persist_path)
    #
    # else:
    #     kb.insert_entry(job_name, persist_path)

    return persist_path


def remove_kb_entry(job_name, persist_path):
    try:
        kb.delete_entry(job_name, persist_path)
    except:
        traceback.print_exc()
        return False

    return True

def extract_text_values_from_api_resp(json_obj, text_values=None):
    if text_values is None:
        text_values = []

    if isinstance(json_obj, dict):
        for key, value in json_obj.items():
            if key == "Text":
                text_values.append(value)
            else:
                extract_text_values_from_api_resp(value, text_values)
    elif isinstance(json_obj, list):
        for item in json_obj:
            extract_text_values_from_api_resp(item, text_values)

    return text_values


def retrieve_claims_info(chat_obj, s3_file_path):

    # read from file
    job_name = None
    persist_path = None

    api_response = aws_ocr.detect_from_s3_file(s3_file_path)
    list_of_text_str = extract_text_values_from_api_resp(api_response)
    file_content = "\n".join(list_of_text_str)

    actual_output = None
    json_resp = None

    print("--- Test file ---")
    print(s3_file_path)
    print(file_content[:50])
    try:
        job_name = "Test OCR Text"
        if s3_file_path is not None:
            job_name = str(uuid.uuid5(uuid.NAMESPACE_OID, s3_file_path))

        # persist_path = ingest_text_str("",job_name)
        # receipt_question = "This my receipt data'" + file_content + "'. " + question
        persist_path = ingest_text_str(file_content, job_name)

        # run the question on the embedding
        # chat_obj, vectordb = init_chat(persist_path)
        vectordb = init_vector_db(EMBEDDINGS_BGE_BASE, persist_path)
        receipt_question = claims_processing.question

        # re-use chat_obj
        resp = ask_chat(receipt_question, chat_obj, vectordb)
        json_resp = json.loads(resp['response']['result'])

        print(json_resp)
        actual_output = json_resp

        # adjust those that requires some cleaning
        actual_output['receipt_total_amount'] = process_total_amount(json_resp['receipt_total_amount']),
        actual_output['receipt_datetime_of_purchase'] = process_receipt_datetime(json_resp['receipt_datetime_of_purchase']),

        return file_content, api_response, json_resp, actual_output
    except:
        traceback.print_exc()
        return file_content, api_response, json_resp, actual_output
    finally:
        # always delete entry
        # print("Deleting entry")
        # remove_kb_entry(job_name, persist_path)
        # print("Deleting path")
        try:
            if persist_path is None:
                return file_content, api_response, None, actual_output

            if os.path.isfile(persist_path):
                os.remove(persist_path)
            elif os.path.isdir(persist_path):
                shutil.rmtree(persist_path)
        except OSError as e:
            print(f"Error deleting file {persist_path}: {e.strerror}")

def receipt_prompt_test():
    # initialize the chat_objected (connected to openAI) - we can always re-use this later
    chat_obj = init_chat_obj()

    # fake data- We can change this to any text string
    file_content = "Test document these are details within any text document or string"
    job_name = "Test OCR Text"

    # embed to text string, save the embedding vector as job_name (should be unique)
    persist_path = ingest_text_str(file_content, job_name)

    # question to ask the AI model
    question = "What is the summary of this text?"

    # run the question on the embedding
    # pass embedding sentence transformer and persistence path of where it is saving it (sqlite)
    vectordb = init_vector_db(EMBEDDINGS_BGE_BASE, persist_path)

    # response from model e.g. openAI

    resp = ask_chat(question, chat_obj, vectordb)
    print(resp)

def jd_prompt_test(file_content):
    # initialize the chat_objected (connected to openAI) - we can always re-use this later
    chat_obj = init_chat_obj()

    if file_content is None:
        # fake data- We can change this to any text string
        file_content = """Research & Design Engineer (Electronics MFG Industry/East Area) Job in East Region - JobstreetResearch & Design Engineer (Electronics MFG Industry/East Area)Skip to contentJobstreetMenuJob searchProfileCareer adviceExplore companiesSign inSingaporeAustraliaHong KongIndonesiaMalaysiaNew ZealandPhilippinesSingaporeThailandEmployer siteSign inEmployer siteJob searchProfileCareer adviceExplore companiesEmailFacebookTwitterLinkedInReport job adResearch & Design Engineer (Electronics MFG Industry/East Area)TempServ Pte LtdView all jobsEast RegionElectrical/Electronic Engineering (Engineering)Full timeAdd expected salary to your profile for insightsPosted 2d agoQuick applySaveElectronics MFG IndustryLoyang Area (Tpt pick up at designated area)

Section 2:
Perform design for manufacturability in all new projects.Provide PCB manufacturing technical advice to customers on their new projects.Perform feasibility studies and reviews for all new data received from customers.Adhoc duties as assigned.Requirements:Degree/Diploma in Electrical & Electronics Engineering in Printed Wiring Board manufacturing environmentGood communication, report writing and presentation skillsGood analytical skill with ability to work independentlyAbility to communicate with all levels of staffsEntry level are welcome to apply as training will be provided.

Section 3:
Tempserv Pte LtdLicense No: 06C3745Attention: Audris Teo / EA Personnel No: R1102063Employer questionsYour application will include the following questions:Which of the following statements best describes your right to work in Singapore?Company profileTempServ Pte LtdHuman Resources & Recruitment11-50 employeesTempserv is a recruitment firm that delivers reliable manpower solutions to meet our clients' needs. Established in 1999, we've been catering to a rich diversity of corporations in various business fields: government, banking, manufacturing, IT and healthcare etc. We pride over our diverse recruitment categories under the three main themes: Temporary & Contract, Permanent Placement and Executive Recruitment.Corporate missionTo deliver seamless manpower solutions for both our clients and jobseekers by attracting and sourcing potential candidates to fulfil every level of our clients\u2019 recruitment requests.Corporate objectiveTo foster positive and lasting relationships by facilitating successful criteria between our clients and jobseekers.Tempserv Pte LtdEA License No. 06C3745Tempserv is a recruitment firm that delivers reliable manpower solutions to meet our clients' needs. Established in 1999, we've been catering to a rich diversity of corporations in various business fields: government, banking, manufacturing, IT and healthcare etc. We pride over our diverse recruitment categories under the three main themes: Temporary & Contract, Permanent Placement and Executive Recruitment.Corporate missionTo deliver seamless manpower solutions for both our clients and jobseekers by attracting and sourcing potential candidates to fulfil every level of our clients\u2019 recruitment requests.Corporate objectiveTo foster positive and lasting relationships by facilitating successful criteria between our clients and jobseekers.Tempserv Pte LtdEA License No. 06C3745Show more\u2060More about this company\u2060Company informationRegistration No.06C3745EA No.06C3745Report this job advertBe carefulDon\u2019t provide your bank or credit card details when applying for jobs.Learn how to protect yourselfReport this job ad\u2060Your email addressReason for reporting jobPlease selectUnable to applyFraudulentDiscriminationMisleadingOtherAdditional commentsReport jobCancelWhat can I earn as an Electronics EngineerSee more detailed salary informationJob seekersJob searchProfileRecommended jobsSaved searchesSaved jobsJob applicationsCareer adviceExplore careersExplore salariesExplore companiesDownload appsJobstreet @ Google PlayJobstreet @ App StoreEmployersRegister for freePost a job adProducts & pricesCustomer serviceHiring adviceMarket insightsRecruitment software partnersAbout JobstreetAbout usWork for JobstreetInternational partnersBdjobs (Bangladesh)Jobsdb (SE Asia)Jora (Australia)Jora (Worldwide)SEEK (Australia)SEEK (New Zealand)Partner servicesCertsyGradConnectionJora LocalSidekickerGO1FutureLearnEmployment HeroJobAdderContactHelp centreContact usProduct & tech blogSocialFacebookInstagramTwitterYouTubeSingaporeAustraliaHong KongIndonesiaMalaysiaNew ZealandPhilippinesSingaporeThailandTerms & conditionsSecurity & PrivacyCopyright \u00a9 2024, JobstreetShare or report ad"""

    job_name = "NewJDTest"

    # embed to text string, save the embedding vector as job_name (should be unique)
    # persist_path = ingest_text_str(file_content, job_name)

    # question to ask the AI model
    question = jd_processing.build_prompt(file_content)
    # print(question)

    # run the question on the embedding
    # pass embedding sentence transformer and persistence path of where it is saving it (sqlite)
    # vectordb = init_vector_db(EMBEDDINGS_BGE_BASE, persist_path)

    # response from model e.g. openAI

    resp = ask(question, chat_obj) #no source docs required
    # resp = ask_chat(question, chat_obj, vectordb)
    # print(resp)
    # json_resp = json.loads(resp['response'])
    # print(json_resp)
    return resp

def read_docx(file_path):
    doc = Doc(file_path)
    full_text = []
    for paragraph in doc.paragraphs:
        full_text.append(paragraph.text)
    return '\n'.join(full_text)


def resume_prompt_test():
    chat_obj = init_chat_obj()
    job_name = "NewResumeTest"

    file_content =read_docx('/Users/thomt/Desktop/Dev/GHQ_ML_Foundation_Layer/test_data/resume.docx')

    # print(file_content[:100])

    persist_path = ingest_text_str(file_content, job_name)
    vectordb = init_vector_db(EMBEDDINGS_BGE_BASE, persist_path)

    question = resume_processing.build_prompt()

    resp = ask_chat(question, chat_obj, vectordb)
    print(resp)



def MT_process_scraped_results():
    # Load the scrape results CSV
    df = pd.read_csv('/Users/thomt/Desktop/Dev/Scrapers/scrape_results.csv')
    df = df.iloc[5:]

    # Function to process each row
    def process_row(row):
        try:
            # Parse the content_data as JSON
            content_data = row['content_data']

            # Extract the value under the 'content_' key
            # file_content = json.loads(content_data).get('content_', "")

            # Run the jd_prompt_test function
            result = jd_prompt_test(content_data)

            # Add original row data to the result
            # row_data = row.to_dict()
            # row_data.update(result)

            return result['response']
        except Exception as e:
            traceback.print_exc()
            # In case of any errors, capture the error message
            # error_result = row.to_dict()
            # error_result['error'] = str(e)
            return {'error':str(e)}

    # Use ThreadPoolExecutor to parallelize the processing
    final_results = []
    with ThreadPoolExecutor(max_workers=10) as executor:
        futures = [executor.submit(process_row, row) for _, row in df.iterrows()]
        for future in as_completed(futures):
            final_results.append(future.result())

    # Create a new DataFrame from the list of dictionaries
    results_df = pd.DataFrame(final_results)

    # Save the results DataFrame to a new Excel file
    results_df.to_excel('processed_scrape_results.xlsx', index=False)


def run():
    MT_process_scraped_results()
    # jd_prompt_test()
    # resume_prompt_test()
    # receipt_prompt_test()


if __name__ == "__main__":
    run()
