import os
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
import docx

CVS_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "sample_data", "cvs")
os.makedirs(CVS_DIR, exist_ok=True)

# 18 Realistic Synthetic Candidate Profiles
CANDIDATES_DATA = [
    {
        "code": "CND-91022",
        "first_name": "Ritika",
        "last_name": "Bansal",
        "email": "ritika.bansal@synthetic-talent.com",
        "phone": "+91 9811234567",
        "role": "Senior Java Developer",
        "total_exp": 6.5,
        "rel_exp": 6.0,
        "skills": ["Java", "Spring Boot", "Microservices", "REST APIs", "Kafka", "PostgreSQL", "Docker", "Git"],
        "notice": 60,
        "location": "Noida",
        "education": "B.Tech in Computer Science, AKTU (2018)",
        "file_ext": "pdf",
        "highlights": [
            "Over 6.5 years of hands-on experience designing and developing distributed enterprise Java systems.",
            "Architected high-throughput microservices using Spring Boot, Spring Cloud, and Apache Kafka.",
            "Led backend migration to REST APIs handling over 4 million requests daily with PostgreSQL database.",
            "Strong advocate of clean code, CI/CD pipelines, Docker containerization, and unit test coverage."
        ]
    },
    {
        "code": "CND-91047",
        "first_name": "Arjun",
        "last_name": "Rawat",
        "email": "arjun.rawat@synthetic-talent.com",
        "phone": "+91 9822345678",
        "role": "KYC Analyst",
        "total_exp": 3.0,
        "rel_exp": 0.0,
        "skills": ["KYC", "AML Checks", "Excel", "Compliance", "Customer Due Diligence"],
        "notice": 30,
        "location": "Noida",
        "education": "B.Com, Delhi University (2021)",
        "file_ext": "docx",
        "highlights": [
            "3 years of professional experience conducting KYC, Customer Due Diligence, and AML verification.",
            "Advanced Excel reporting, VLOOKUP, pivot tables, and compliance transaction auditing.",
            "Collaborated with risk and compliance teams to prevent fraudulent onboarding.",
            "Notice period is 30 days serving with immediate joining possible."
        ]
    },
    {
        "code": "CND-91088",
        "first_name": "Pooja",
        "last_name": "Nair",
        "email": "pooja.nair@synthetic-talent.com",
        "phone": "+91 9833456789",
        "role": "Java Developer",
        "total_exp": 4.0,
        "rel_exp": 4.0,
        "skills": ["Java", "Hibernate", "REST APIs", "Spring MVC", "MySQL", "Maven"],
        "notice": 90,
        "location": "Gurgaon",
        "education": "B.E. in Information Technology, Pune University (2020)",
        "file_ext": "pdf",
        "highlights": [
            "4 years total experience building Java enterprise web applications with Hibernate and Spring MVC.",
            "Developed REST APIs and optimized complex SQL queries on relational databases.",
            "Notice period is 90 days as per company employment contract.",
            "Hands-on experience in Maven build automation, JUnit testing, and Git version control."
        ]
    },
    {
        "code": "CND-91105",
        "first_name": "Vikram",
        "last_name": "Malhotra",
        "email": "vikram.malhotra@synthetic-talent.com",
        "phone": "+91 9844567890",
        "role": "Senior Java Developer",
        "total_exp": 7.5,
        "rel_exp": 7.0,
        "skills": ["Java", "Spring Boot", "Microservices", "Kafka", "Docker", "Kubernetes", "AWS", "Redis"],
        "notice": 45,
        "location": "Noida",
        "education": "B.Tech in Computer Science, IIT Roorkee (2017)",
        "file_ext": "pdf",
        "highlights": [
            "7.5 years of comprehensive software development experience in Java, Spring Boot, and Microservices.",
            "Implemented event-driven microservices architecture using Apache Kafka and Redis distributed cache.",
            "Deployed containerized services to AWS EKS with Kubernetes and automated GitOps pipelines.",
            "Notice period 45 days. Successfully mentored junior engineers on cloud-native practices."
        ]
    },
    {
        "code": "CND-91120",
        "first_name": "Sneha",
        "last_name": "Kulkarni",
        "email": "sneha.kulkarni@synthetic-talent.com",
        "phone": "+91 9855678901",
        "role": "Full Stack Engineer",
        "total_exp": 5.0,
        "rel_exp": 4.5,
        "skills": ["Java", "Spring Boot", "React", "TypeScript", "Microservices", "PostgreSQL"],
        "notice": 30,
        "location": "Bangalore",
        "education": "B.Tech in Information Science, VTU (2019)",
        "file_ext": "docx",
        "highlights": [
            "5 years of full stack engineering building robust Java Spring Boot backend services and React frontends.",
            "Designed scalable RESTful microservices integrated with PostgreSQL and modern UI components.",
            "Available to join within 30 days notice period. Open to relocation to Noida."
        ]
    },
    {
        "code": "CND-91142",
        "first_name": "Ananya",
        "last_name": "Deshmukh",
        "email": "ananya.deshmukh@synthetic-talent.com",
        "phone": "+91 9866789012",
        "role": "Frontend Architect",
        "total_exp": 8.5,
        "rel_exp": 8.0,
        "skills": ["React", "TypeScript", "Tailwind", "Next.js", "Redux", "System Architecture", "GraphQL"],
        "notice": 30,
        "location": "Bangalore",
        "education": "B.Tech, NIT Surathkal (2016)",
        "file_ext": "pdf",
        "highlights": [
            "8.5 years of industry experience architecting large-scale React and TypeScript web applications.",
            "Established enterprise UI design systems using Tailwind CSS and micro-frontend architectures.",
            "Reduced client-side bundle size by 42% through code-splitting and progressive hydration.",
            "Notice period is 30 days. Experienced in leading 12+ frontend engineers."
        ]
    },
    {
        "code": "CND-91163",
        "first_name": "Rohan",
        "last_name": "Gupta",
        "email": "rohan.gupta@synthetic-talent.com",
        "phone": "+91 9877890123",
        "role": "Senior Backend Engineer",
        "total_exp": 6.0,
        "rel_exp": 5.5,
        "skills": ["Java", "Spring Boot", "Microservices", "PostgreSQL", "Kafka", "CI/CD"],
        "notice": 60,
        "location": "Noida",
        "education": "M.Tech in Software Systems, BITS Pilani (2018)",
        "file_ext": "docx",
        "highlights": [
            "6 years of backend engineering expertise focusing on Java, Spring Boot, and scalable microservices.",
            "Extensive experience with message streaming via Kafka and database optimization in PostgreSQL.",
            "Comfortable with 60 days standard notice period."
        ]
    },
    {
        "code": "CND-91180",
        "first_name": "Divya",
        "last_name": "Venkatesh",
        "email": "divya.venkatesh@synthetic-talent.com",
        "phone": "+91 9888901234",
        "role": "Lead Java Developer",
        "total_exp": 8.0,
        "rel_exp": 8.0,
        "skills": ["Java", "Spring Boot", "Microservices", "Docker", "Kubernetes", "AWS", "System Design"],
        "notice": 60,
        "location": "Noida",
        "education": "B.Tech in Computer Science, Anna University (2016)",
        "file_ext": "pdf",
        "highlights": [
            "8 years of total experience leading technical teams in Java, Spring Boot, and cloud microservices.",
            "Spearheaded enterprise architecture modernization on AWS with Docker and Kubernetes.",
            "Notice period is 60 days. Proven track record in high-concurrency payment gateways."
        ]
    },
    {
        "code": "CND-91195",
        "first_name": "Karan",
        "last_name": "Mehta",
        "email": "karan.mehta@synthetic-talent.com",
        "phone": "+91 9899012345",
        "role": "Java Backend Developer",
        "total_exp": 5.2,
        "rel_exp": 5.0,
        "skills": ["Java", "Spring Boot", "Microservices", "REST APIs", "MongoDB"],
        "notice": 30,
        "location": "Delhi",
        "education": "B.Tech in IT, GGSIPU Delhi (2019)",
        "file_ext": "pdf",
        "highlights": [
            "5.2 years of dedicated backend engineering in core Java and Spring Boot microservices.",
            "Implemented authenticated REST APIs and resilient service-to-service communication.",
            "Notice period is 30 days. Located in Delhi NCR, immediate commute to Noida."
        ]
    },
    {
        "code": "CND-91210",
        "first_name": "Meera",
        "last_name": "Iyer",
        "email": "meera.iyer@synthetic-talent.com",
        "phone": "+91 9911223344",
        "role": "Senior Frontend Developer",
        "total_exp": 7.0,
        "rel_exp": 7.0,
        "skills": ["React", "TypeScript", "Tailwind", "System Architecture", "Next.js", "Redux"],
        "notice": 30,
        "location": "Bangalore",
        "education": "B.E. in Computer Science, RVCE Bangalore (2017)",
        "file_ext": "docx",
        "highlights": [
            "7 years building high-performing single page applications and dashboards in React and TypeScript.",
            "Authored component libraries with Tailwind CSS and styled-system guidelines.",
            "30 days notice period. Excellent collaborative and architecture review skills."
        ]
    },
    {
        "code": "CND-91225",
        "first_name": "Siddharth",
        "last_name": "Verma",
        "email": "siddharth.verma@synthetic-talent.com",
        "phone": "+91 9922334455",
        "role": "DevOps & Cloud Engineer",
        "total_exp": 5.5,
        "rel_exp": 2.0,
        "skills": ["Docker", "Kubernetes", "AWS", "Terraform", "CI/CD", "Linux", "Python"],
        "notice": 45,
        "location": "Noida",
        "education": "B.Tech in Electronics, Thapar University (2019)",
        "file_ext": "pdf",
        "highlights": [
            "5.5 years in DevOps infrastructure, container orchestration with Kubernetes, and AWS cloud.",
            "Automated multi-stage CI/CD deployment pipelines using GitLab CI and Docker.",
            "Notice period is 45 days. Basic working familiarity with Java runtimes."
        ]
    },
    {
        "code": "CND-91240",
        "first_name": "Tanvi",
        "last_name": "Sharma",
        "email": "tanvi.sharma@synthetic-talent.com",
        "phone": "+91 9933445566",
        "role": "Java Microservices Specialist",
        "total_exp": 6.8,
        "rel_exp": 6.8,
        "skills": ["Java", "Spring Boot", "Microservices", "Kafka", "PostgreSQL", "Docker"],
        "notice": 60,
        "location": "Noida",
        "education": "B.Tech in Computer Science, Amity University (2018)",
        "file_ext": "pdf",
        "highlights": [
            "6.8 years of extensive software development in Java, Spring Boot, and event-driven microservices.",
            "Delivered resilient microservices backed by Apache Kafka and PostgreSQL database clusters.",
            "Standard notice period of 60 days. Passionate about domain-driven design."
        ]
    },
    {
        "code": "CND-91255",
        "first_name": "Aditya",
        "last_name": "Chopra",
        "email": "aditya.chopra@synthetic-talent.com",
        "phone": "+91 9944556677",
        "role": "Junior Java Developer",
        "total_exp": 2.2,
        "rel_exp": 2.0,
        "skills": ["Java", "Spring Boot", "REST APIs", "MySQL", "Git"],
        "notice": 15,
        "location": "Noida",
        "education": "B.Tech in Computer Science, Galgotias (2022)",
        "file_ext": "docx",
        "highlights": [
            "2.2 years of working experience developing REST APIs in Java with Spring Boot.",
            "Maintained backend endpoints and executed integration tests with JUnit and Mockito.",
            "Immediate availability with only 15 days notice period."
        ]
    },
    {
        "code": "CND-91270",
        "first_name": "Pallavi",
        "last_name": "Sen",
        "email": "pallavi.sen@synthetic-talent.com",
        "phone": "+91 9955667788",
        "role": "Python Backend Engineer",
        "total_exp": 4.5,
        "rel_exp": 1.0,
        "skills": ["Python", "FastAPI", "PostgreSQL", "Docker", "Redis"],
        "notice": 30,
        "location": "Gurgaon",
        "education": "B.Tech in Information Technology, Jadavpur University (2020)",
        "file_ext": "pdf",
        "highlights": [
            "4.5 years engineering high-speed asynchronous APIs with Python and FastAPI.",
            "Worked on caching strategies with Redis and data modeling in PostgreSQL.",
            "30 days notice period. Open to learning Spring Boot."
        ]
    },
    {
        "code": "CND-91285",
        "first_name": "Harsh",
        "last_name": "Vardhan",
        "email": "harsh.vardhan@synthetic-talent.com",
        "phone": "+91 9966778899",
        "role": "Senior Fullstack Developer",
        "total_exp": 7.0,
        "rel_exp": 6.5,
        "skills": ["Java", "Spring Boot", "Microservices", "React", "TypeScript", "Kafka", "AWS"],
        "notice": 60,
        "location": "Noida",
        "education": "B.Tech in Computer Science, Jamia Millia Islamia (2017)",
        "file_ext": "pdf",
        "highlights": [
            "7 years delivering enterprise cloud web apps using Java, Spring Boot, Microservices, and React.",
            "Proven ability to lead technical design, implement Kafka pipelines, and deploy on AWS.",
            "Available on 60 days notice period. Resides locally in Noida."
        ]
    },
    {
        "code": "CND-91300",
        "first_name": "Bhavna",
        "last_name": "Pandey",
        "email": "bhavna.pandey@synthetic-talent.com",
        "phone": "+91 9977889900",
        "role": "UI/UX & Frontend Developer",
        "total_exp": 4.0,
        "rel_exp": 3.5,
        "skills": ["React", "JavaScript", "HTML/CSS", "Figma", "Tailwind"],
        "notice": 30,
        "location": "Noida",
        "education": "B.Des in Interaction Design, NID (2020)",
        "file_ext": "docx",
        "highlights": [
            "4 years combining design systems in Figma with frontend React implementation and Tailwind CSS.",
            "Passionate about accessible, high-fidelity UI components and user testing.",
            "30 days notice period."
        ]
    }
]


def create_pdf_cv(candidate: dict, file_path: str):
    c = canvas.Canvas(file_path, pagesize=letter)
    width, height = letter

    # Header
    c.setFont("Helvetica-Bold", 18)
    c.drawString(50, height - 50, f"{candidate['first_name']} {candidate['last_name']}")
    
    c.setFont("Helvetica", 11)
    c.setFillColorRGB(0.2, 0.3, 0.5)
    c.drawString(50, height - 68, f"{candidate['role']} | Candidate ID: {candidate['code']}")
    c.drawString(50, height - 83, f"Email: {candidate['email']} | Phone: {candidate['phone']} | Location: {candidate['location']}")

    c.setStrokeColorRGB(0.8, 0.8, 0.8)
    c.line(50, height - 95, width - 50, height - 95)

    y = height - 120
    c.setFillColorRGB(0.1, 0.1, 0.2)

    # Professional Summary
    c.setFont("Helvetica-Bold", 13)
    c.drawString(50, y, "Professional Summary")
    y -= 18
    c.setFont("Helvetica", 10)
    summary_text = (
        f"Professional with {candidate['total_exp']} years total experience ({candidate['rel_exp']} years relevant) "
        f"specializing as {candidate['role']}. Notice period: {candidate['notice']} days. "
        f"Synthetic CV created for HireAI platform parsing and verification."
    )
    c.drawString(50, y, summary_text[:110])
    if len(summary_text) > 110:
        y -= 14
        c.drawString(50, y, summary_text[110:])
    y -= 25

    # Core Technical Skills
    c.setFont("Helvetica-Bold", 13)
    c.drawString(50, y, "Core Technical Skills")
    y -= 18
    c.setFont("Helvetica", 10)
    skills_line = " • " + " • ".join(candidate['skills'])
    c.drawString(50, y, skills_line)
    y -= 25

    # Experience & Career Highlights
    c.setFont("Helvetica-Bold", 13)
    c.drawString(50, y, f"Experience Highlights ({candidate['total_exp']} Years)")
    y -= 18
    c.setFont("Helvetica", 10)
    for highlight in candidate['highlights']:
        c.drawString(60, y, f"• {highlight}")
        y -= 18

    y -= 10
    # Education & Notice Period
    c.setFont("Helvetica-Bold", 13)
    c.drawString(50, y, "Education & Logistics")
    y -= 18
    c.setFont("Helvetica", 10)
    c.drawString(60, y, f"• Education: {candidate['education']}")
    y -= 16
    c.drawString(60, y, f"• Official Notice Period: {candidate['notice']} days")
    y -= 16
    c.drawString(60, y, f"• Current Base Location: {candidate['location']}")

    c.save()


def create_docx_cv(candidate: dict, file_path: str):
    doc = docx.Document()
    
    # Title & Subtitle
    h = doc.add_heading(f"{candidate['first_name']} {candidate['last_name']}", level=0)
    p_sub = doc.add_paragraph(f"{candidate['role']} | Candidate ID: {candidate['code']}")
    p_contact = doc.add_paragraph(f"Email: {candidate['email']} | Phone: {candidate['phone']} | Location: {candidate['location']}")
    
    doc.add_heading("Professional Summary", level=1)
    doc.add_paragraph(
        f"Professional with {candidate['total_exp']} years total experience and {candidate['rel_exp']} years relevant experience. "
        f"Notice period: {candidate['notice']} days. Synthetic CV profile created for HireAI verification."
    )

    doc.add_heading("Core Technical Skills", level=1)
    doc.add_paragraph(" | ".join(candidate['skills']))

    doc.add_heading("Experience Highlights", level=1)
    for highlight in candidate['highlights']:
        doc.add_paragraph(highlight, style='List Bullet')

    doc.add_heading("Education & Availability", level=1)
    doc.add_paragraph(f"Education: {candidate['education']}")
    doc.add_paragraph(f"Notice Period: {candidate['notice']} days")
    doc.add_paragraph(f"Location: {candidate['location']}")

    doc.save(file_path)


def generate_all_sample_cvs():
    generated_files = []
    for cand in CANDIDATES_DATA:
        filename = f"{cand['code']}_{cand['first_name']}_{cand['last_name']}.{cand['file_ext']}"
        filepath = os.path.join(CVS_DIR, filename)
        if cand['file_ext'] == "pdf":
            create_pdf_cv(cand, filepath)
        else:
            create_docx_cv(cand, filepath)
        generated_files.append((cand, filepath))
    print(f"Generated {len(generated_files)} realistic synthetic CV files in {CVS_DIR}")
    return generated_files


if __name__ == "__main__":
    generate_all_sample_cvs()

