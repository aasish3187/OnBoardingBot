"""
OnboardBot — Real-Time Company Data Engine
Fetches real MNC company data from public sources (Wikipedia, web),
generates realistic onboarding documents using the LLM, and builds
per-company vector stores on the fly.

Usage:
    from src.company_engine import CompanyKnowledgeBase
    kb = CompanyKnowledgeBase()
    vector_store, company_info = kb.build_realtime("Google")
"""

import os
import re
import json
import hashlib
import time
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Generator
from datetime import datetime

import requests
from langchain_core.documents import Document

from src.config import (
    CHROMA_DB_DIR,
    CHUNK_SIZE,
    CHUNK_OVERLAP,
    COLLECTION_NAME,
)
from src.embeddings import get_embeddings


# ============================================================================
# COMPANY CACHE DIRECTORY
# ============================================================================
COMPANY_CACHE_DIR = Path(__file__).parent.parent / "company_cache"
COMPANY_CACHE_DIR.mkdir(exist_ok=True)


def _safe_collection_name(company_name: str) -> str:
    """Generate a safe ChromaDB collection name from company name."""
    slug = re.sub(r"[^a-zA-Z0-9]", "_", company_name.lower()).strip("_")
    slug = re.sub(r"_+", "_", slug)
    # ChromaDB requires 3-63 chars, start/end with alphanum
    slug = f"ob_{slug}"[:60]
    if not slug[-1].isalnum():
        slug = slug.rstrip("_") or "ob_default"
    return slug


# ============================================================================
# COMPANY DATA FETCHER — Wikipedia + Web Scraping
# ============================================================================
class CompanyDataFetcher:
    """Fetches real company information from public sources."""

    # Known MNC metadata for instant enrichment (avoids network for popular companies)
    KNOWN_COMPANIES = {
        "google": {
            "full_name": "Google LLC (Alphabet Inc.)",
            "industry": "Technology, Internet Services, Cloud Computing, AI",
            "founded": "1998",
            "headquarters": "Mountain View, California, USA",
            "ceo": "Sundar Pichai",
            "employees": "180,000+",
            "tech_stack": "Go, Python, Java, C++, Kubernetes, TensorFlow, GCP",
            "careers_url": "https://careers.google.com",
            "work_culture": "Innovation-driven, 20% time projects, open offices, flat hierarchy",
            "benefits_highlights": "Free meals, on-site wellness, generous parental leave, 401k matching, education reimbursement",
        },
        "microsoft": {
            "full_name": "Microsoft Corporation",
            "industry": "Technology, Cloud Computing, Software, AI",
            "founded": "1975",
            "headquarters": "Redmond, Washington, USA",
            "ceo": "Satya Nadella",
            "employees": "220,000+",
            "tech_stack": "C#, .NET, Azure, TypeScript, Python, VS Code",
            "careers_url": "https://careers.microsoft.com",
            "work_culture": "Growth mindset, hybrid work, inclusive culture, hackathons",
            "benefits_highlights": "Health insurance, stock awards, 401k, parental leave, wellness programs, education assistance",
        },
        "amazon": {
            "full_name": "Amazon.com, Inc.",
            "industry": "E-commerce, Cloud Computing (AWS), AI, Logistics",
            "founded": "1994",
            "headquarters": "Seattle, Washington, USA",
            "ceo": "Andy Jassy",
            "employees": "1,500,000+",
            "tech_stack": "Java, Python, AWS, React, DynamoDB, Lambda",
            "careers_url": "https://www.amazon.jobs",
            "work_culture": "Leadership principles, customer obsession, bias for action, day-one mentality",
            "benefits_highlights": "Health coverage from day 1, stock vesting, career choice program, parental leave",
        },
        "tcs": {
            "full_name": "Tata Consultancy Services Limited",
            "industry": "IT Services, Consulting, Digital Solutions",
            "founded": "1968",
            "headquarters": "Mumbai, Maharashtra, India",
            "ceo": "K. Krithivasan",
            "employees": "600,000+",
            "tech_stack": "Java, Python, SAP, Salesforce, Azure, AWS, .NET",
            "careers_url": "https://www.tcs.com/careers",
            "work_culture": "Values-driven, learning culture, global diversity, Tata values",
            "benefits_highlights": "PF, gratuity, health insurance, ESOPs, learning platforms (iEvolve), gym reimbursement",
        },
        "infosys": {
            "full_name": "Infosys Limited",
            "industry": "IT Services, Consulting, Digital Transformation",
            "founded": "1981",
            "headquarters": "Bengaluru, Karnataka, India",
            "ceo": "Salil Parekh",
            "employees": "310,000+",
            "tech_stack": "Java, Python, SAP, Cloud, AI/ML, ServiceNow",
            "careers_url": "https://www.infosys.com/careers",
            "work_culture": "C-LIFE values (Customer, Leadership, Integrity, Fairness, Excellence), Infosys campus life",
            "benefits_highlights": "Health insurance, NPS, gratuity, relocation support, Lex learning platform, parental leave",
        },
        "wipro": {
            "full_name": "Wipro Limited",
            "industry": "IT Services, Consulting, Business Process Services",
            "founded": "1945",
            "headquarters": "Bengaluru, Karnataka, India",
            "ceo": "Srini Pallia",
            "employees": "240,000+",
            "tech_stack": "Java, .NET, SAP, Oracle, Cloud, AI",
            "careers_url": "https://careers.wipro.com",
            "work_culture": "Spirit of Wipro, integrity, customer-first, innovation",
            "benefits_highlights": "Medical insurance, PF, gratuity, EAP, wellness programs, learning academy",
        },
        "meta": {
            "full_name": "Meta Platforms, Inc.",
            "industry": "Social Media, Technology, VR/AR, AI",
            "founded": "2004",
            "headquarters": "Menlo Park, California, USA",
            "ceo": "Mark Zuckerberg",
            "employees": "67,000+",
            "tech_stack": "React, Hack/PHP, Python, PyTorch, C++, GraphQL",
            "careers_url": "https://www.metacareers.com",
            "work_culture": "Move fast, be bold, open culture, hackathons, bootcamp onboarding",
            "benefits_highlights": "Free meals, health coverage, RSUs, generous parental leave, wellness stipend",
        },
        "apple": {
            "full_name": "Apple Inc.",
            "industry": "Consumer Electronics, Software, Services",
            "founded": "1976",
            "headquarters": "Cupertino, California, USA",
            "ceo": "Tim Cook",
            "employees": "160,000+",
            "tech_stack": "Swift, Objective-C, Python, ML frameworks, macOS/iOS ecosystem",
            "careers_url": "https://www.apple.com/careers",
            "work_culture": "Secrecy, attention to detail, cross-functional teams, excellence",
            "benefits_highlights": "Product discounts, health insurance, stock purchase plan, wellness centers, education reimbursement",
        },
        "accenture": {
            "full_name": "Accenture plc",
            "industry": "IT Services, Consulting, Strategy, Digital",
            "founded": "1989",
            "headquarters": "Dublin, Ireland",
            "ceo": "Julie Sweet",
            "employees": "730,000+",
            "tech_stack": "SAP, Salesforce, AWS, Azure, AI/ML, ServiceNow",
            "careers_url": "https://www.accenture.com/us-en/careers",
            "work_culture": "360-degree value, inclusion & diversity, innovation, continuous learning",
            "benefits_highlights": "Health insurance, 401k/PF, parental leave, learning boards, wellness programs, EAP",
        },
        "deloitte": {
            "full_name": "Deloitte Touche Tohmatsu Limited",
            "industry": "Professional Services, Consulting, Audit, Tax, Advisory",
            "founded": "1845",
            "headquarters": "London, United Kingdom",
            "ceo": "Joe Ucuzoglu (Global CEO)",
            "employees": "450,000+",
            "tech_stack": "SAP, Oracle, Cloud platforms, Python, Power BI, Tableau",
            "careers_url": "https://www2.deloitte.com/careers",
            "work_culture": "Purpose-driven, well-being focused, inclusive, professional development",
            "benefits_highlights": "Health/dental/vision, 401k, sabbatical program, CPA support, wellness subsidies",
        },
    }

    def fetch_company_info(self, company_name: str, progress_callback=None) -> Dict:
        """
        Fetch company information. Tries in order:
        1. Known companies cache (instant)
        2. Wikipedia API (fast)
        3. DuckDuckGo Instant Answers (fallback)
        
        Returns a dict with company metadata.
        """
        key = company_name.lower().strip()

        # 1. Check known companies
        if progress_callback:
            progress_callback("Checking known company database...", 0.1)

        for known_key, known_data in self.KNOWN_COMPANIES.items():
            if known_key in key or key in known_key:
                if progress_callback:
                    progress_callback(f"Found {known_data['full_name']} in database!", 0.3)
                return {**known_data, "source": "known_database", "query_name": company_name}

        # 2. Try Wikipedia
        if progress_callback:
            progress_callback("Searching Wikipedia for company info...", 0.2)

        wiki_info = self._fetch_wikipedia(company_name)
        if wiki_info:
            if progress_callback:
                progress_callback("Retrieved company data from Wikipedia!", 0.4)
            return {**wiki_info, "source": "wikipedia", "query_name": company_name}

        # 3. Try DuckDuckGo Instant Answers
        if progress_callback:
            progress_callback("Searching web for company details...", 0.3)

        ddg_info = self._fetch_duckduckgo(company_name)
        if ddg_info:
            if progress_callback:
                progress_callback("Found company info from web search!", 0.4)
            return {**ddg_info, "source": "web_search", "query_name": company_name}

        # 4. Fallback: create basic info from name
        if progress_callback:
            progress_callback("Creating profile for " + company_name + "...", 0.4)

        return {
            "full_name": company_name.title(),
            "industry": "Technology / Professional Services",
            "founded": "N/A",
            "headquarters": "Global",
            "ceo": "N/A",
            "employees": "1,000+",
            "tech_stack": "Various modern technologies",
            "careers_url": f"https://www.{company_name.lower().replace(' ', '')}.com/careers",
            "work_culture": "Professional, collaborative environment",
            "benefits_highlights": "Health insurance, retirement plans, professional development",
            "source": "fallback",
            "query_name": company_name,
        }

    def _fetch_wikipedia(self, company_name: str) -> Optional[Dict]:
        """Fetch company info from Wikipedia API."""
        try:
            # Search for the company page
            search_url = "https://en.wikipedia.org/api/rest_v1/page/summary/" + \
                         requests.utils.quote(company_name.replace(" ", "_"))
            resp = requests.get(search_url, timeout=8, headers={
                "User-Agent": "OnboardBot/1.0 (Educational Project)"
            })

            if resp.status_code != 200:
                # Try with " (company)" suffix
                search_url = "https://en.wikipedia.org/api/rest_v1/page/summary/" + \
                             requests.utils.quote(company_name.replace(" ", "_") + "_(company)")
                resp = requests.get(search_url, timeout=8, headers={
                    "User-Agent": "OnboardBot/1.0 (Educational Project)"
                })

            if resp.status_code == 200:
                data = resp.json()
                extract = data.get("extract", "")

                if len(extract) < 50:
                    return None

                # Parse basic info from the extract
                info = self._parse_wiki_extract(extract, company_name)
                info["wiki_summary"] = extract[:1500]
                return info

        except Exception as e:
            print(f"Wikipedia fetch error: {e}")
        return None

    def _parse_wiki_extract(self, extract: str, company_name: str) -> Dict:
        """Parse key facts from Wikipedia summary text."""
        info = {
            "full_name": company_name.title(),
            "industry": "Technology",
            "founded": "N/A",
            "headquarters": "Global",
            "ceo": "N/A",
            "employees": "N/A",
            "tech_stack": "Various technologies",
            "careers_url": f"https://www.{company_name.lower().replace(' ', '')}.com/careers",
            "work_culture": "Professional environment",
            "benefits_highlights": "Competitive benefits package",
        }

        text = extract.lower()

        # Try to extract founding year
        year_match = re.search(r"(?:founded|established|incorporated)\s+(?:in\s+)?(\d{4})", text)
        if year_match:
            info["founded"] = year_match.group(1)

        # Try to extract headquarters
        hq_match = re.search(r"headquartered\s+in\s+([^.]+)", text)
        if hq_match:
            info["headquarters"] = hq_match.group(1).strip().title()

        # Try to extract employee count
        emp_match = re.search(r"([\d,]+)\s*employees", text)
        if emp_match:
            info["employees"] = emp_match.group(1)

        # Industry detection from keywords
        industries = []
        if any(w in text for w in ["software", "technology", "tech", "computing"]):
            industries.append("Technology")
        if any(w in text for w in ["consulting", "advisory", "services"]):
            industries.append("Consulting")
        if any(w in text for w in ["financial", "banking", "finance"]):
            industries.append("Financial Services")
        if any(w in text for w in ["pharmaceutical", "healthcare", "medical"]):
            industries.append("Healthcare")
        if any(w in text for w in ["manufacturing", "industrial"]):
            industries.append("Manufacturing")
        if any(w in text for w in ["telecom", "communications"]):
            industries.append("Telecommunications")
        if industries:
            info["industry"] = ", ".join(industries)

        return info

    def _fetch_duckduckgo(self, company_name: str) -> Optional[Dict]:
        """Fetch company info from DuckDuckGo Instant Answers API."""
        try:
            url = "https://api.duckduckgo.com/"
            params = {
                "q": f"{company_name} company",
                "format": "json",
                "no_html": 1,
                "skip_disambig": 1,
            }
            resp = requests.get(url, params=params, timeout=8)
            if resp.status_code == 200:
                data = resp.json()
                abstract = data.get("Abstract", "")
                if len(abstract) > 50:
                    info = self._parse_wiki_extract(abstract, company_name)
                    info["wiki_summary"] = abstract[:1500]
                    return info
        except Exception as e:
            print(f"DuckDuckGo fetch error: {e}")
        return None


# ============================================================================
# ONBOARDING DOCUMENT GENERATOR — Uses LLM to create realistic docs
# ============================================================================
class OnboardingDocGenerator:
    """Generates realistic onboarding documents using real company facts + LLM."""

    def generate_all_documents(
        self,
        company_info: Dict,
        llm=None,
        progress_callback=None,
    ) -> List[Document]:
        """
        Generate complete onboarding document set for a company.
        Returns LangChain Documents ready for vector store ingestion.
        """
        documents = []
        company_name = company_info.get("full_name", company_info.get("query_name", "Unknown"))

        # Generate each document type
        generators = [
            ("HR Employee Handbook", self._generate_hr_handbook, 0.5),
            ("IT Setup Guide", self._generate_it_setup_guide, 0.65),
            ("Leave & Attendance Policy", self._generate_leave_policy, 0.8),
            ("Employee Benefits Guide", self._generate_benefits_guide, 0.9),
        ]

        for doc_name, gen_func, progress in generators:
            if progress_callback:
                progress_callback(f"Generating {doc_name}...", progress)

            content = gen_func(company_info, llm)
            if content:
                # Split into chunks
                chunks = self._split_into_chunks(content, doc_name, company_name)
                documents.extend(chunks)

        if progress_callback:
            progress_callback("All documents generated!", 0.95)

        return documents

    def _split_into_chunks(
        self, content: str, doc_name: str, company_name: str
    ) -> List[Document]:
        """Split content into overlapping chunks for vector store."""
        from langchain_text_splitters import RecursiveCharacterTextSplitter

        splitter = RecursiveCharacterTextSplitter(
            chunk_size=CHUNK_SIZE,
            chunk_overlap=CHUNK_OVERLAP,
            separators=["\n\n", "\n", ". ", " ", ""],
        )

        texts = splitter.split_text(content)
        documents = []

        for i, text in enumerate(texts):
            doc = Document(
                page_content=text,
                metadata={
                    "source_name": doc_name,
                    "file_name": f"{doc_name.lower().replace(' ', '_')}.txt",
                    "company": company_name,
                    "chunk_index": i,
                    "total_chunks": len(texts),
                },
            )
            documents.append(doc)

        return documents

    def _generate_hr_handbook(self, info: Dict, llm=None) -> str:
        """Generate a realistic HR handbook for the company."""
        company = info.get("full_name", "The Company")
        hq = info.get("headquarters", "Global")
        ceo = info.get("ceo", "the CEO")
        founded = info.get("founded", "N/A")
        employees = info.get("employees", "thousands of")
        industry = info.get("industry", "Technology")
        culture = info.get("work_culture", "professional and collaborative")
        wiki_summary = info.get("wiki_summary", "")

        if llm:
            try:
                prompt = f"""Generate a realistic and detailed Employee HR Handbook for {company}.
Use these REAL facts about the company:
- Full Name: {company}
- Founded: {founded}
- Headquarters: {hq}
- CEO: {ceo}
- Employees: {employees}
- Industry: {industry}
- Culture: {culture}
- Background: {wiki_summary[:500]}

The handbook should include these sections with realistic content:
1. Welcome & Company Overview (use real facts)
2. Mission, Vision & Core Values
3. Code of Conduct
4. Workplace Ethics & Anti-Harassment Policy
5. Dress Code Policy
6. Working Hours & Attendance
7. Performance Review Process
8. Grievance & Complaint Procedures
9. Separation & Exit Policy
10. HR Department Contact Information

Make it professional, detailed (at least 2000 words), and realistic for a company of this size and industry.
Use specific numbers, email formats like hr@{company.lower().replace(' ', '').replace('.', '').replace(',', '')}.com, and realistic policies.
Do NOT say this is AI-generated. Write it as an actual company document."""
                response = llm.invoke(prompt)
                if response and len(response) > 500:
                    return response
            except Exception as e:
                print(f"LLM generation failed for HR handbook: {e}")

        # Fallback: template-based generation with real facts
        return self._template_hr_handbook(info)

    def _generate_it_setup_guide(self, info: Dict, llm=None) -> str:
        """Generate a realistic IT setup guide for the company."""
        company = info.get("full_name", "The Company")
        tech_stack = info.get("tech_stack", "Various technologies")
        industry = info.get("industry", "Technology")

        if llm:
            try:
                prompt = f"""Generate a detailed IT Setup & Onboarding Guide for new employees at {company}.
The company uses these technologies: {tech_stack}
Industry: {industry}

Include these sections with specific, realistic details:
1. Day-1 IT Checklist (laptop, accounts, badges)
2. Email & Communication Tools Setup (specific tools used in {industry})
3. VPN & Network Access
4. Development Environment Setup (based on {tech_stack})
5. Security Policies (2FA, password rules, data handling)
6. Software & Licenses
7. IT Support Contacts & Helpdesk
8. Remote Work IT Setup
9. Data Security & Compliance
10. FAQ / Troubleshooting

Make it specific to {company}'s tech stack and industry. Use realistic helpdesk emails, extension numbers, and tool names.
At least 1500 words. Write as an actual company IT document."""
                response = llm.invoke(prompt)
                if response and len(response) > 500:
                    return response
            except Exception as e:
                print(f"LLM generation failed for IT guide: {e}")

        return self._template_it_guide(info)

    def _generate_leave_policy(self, info: Dict, llm=None) -> str:
        """Generate a realistic leave & attendance policy."""
        company = info.get("full_name", "The Company")
        hq = info.get("headquarters", "Global")
        employees = info.get("employees", "N/A")

        # Detect if Indian or US company for region-specific policies
        is_indian = any(
            loc in hq.lower()
            for loc in ["india", "mumbai", "bangalore", "bengaluru", "hyderabad", "pune", "chennai", "delhi", "noida", "gurgaon"]
        )

        if llm:
            try:
                region = "India (with Indian labor law compliance)" if is_indian else "United States"
                prompt = f"""Generate a comprehensive Leave & Attendance Policy document for {company}.
Headquarters: {hq}
Region: {region}
Employees: {employees}

Include these sections with specific, realistic details:
1. Leave Types & Entitlements (Casual, Sick, Earned/PTO, Maternity/Paternity, Bereavement, etc.)
2. Leave Application Process
3. Leave Approval Workflow
4. Attendance Tracking & Reporting
5. Work From Home Policy
6. Overtime Policy
7. Holiday Calendar (list realistic holidays for {region})
8. Compensatory Off Policy
9. Leave Encashment
10. Contact Information for Leave Management

{"Include Indian labor law references (Shops & Establishments Act, Maternity Benefit Act, etc.)" if is_indian else "Include US FMLA references and state-specific notes."}
At least 1500 words. Write as an actual company policy document for {company}."""
                response = llm.invoke(prompt)
                if response and len(response) > 500:
                    return response
            except Exception as e:
                print(f"LLM generation failed for leave policy: {e}")

        return self._template_leave_policy(info, is_indian)

    def _generate_benefits_guide(self, info: Dict, llm=None) -> str:
        """Generate a realistic employee benefits guide."""
        company = info.get("full_name", "The Company")
        hq = info.get("headquarters", "Global")
        benefits = info.get("benefits_highlights", "Competitive package")

        is_indian = any(
            loc in hq.lower()
            for loc in ["india", "mumbai", "bangalore", "bengaluru", "hyderabad", "pune", "chennai", "delhi", "noida", "gurgaon"]
        )

        if llm:
            try:
                prompt = f"""Generate a detailed Employee Benefits Guide for {company}.
Known benefits: {benefits}
Headquarters: {hq}
{"Region: India" if is_indian else "Region: United States"}

Include these sections:
1. Health Insurance (specific plans, coverage amounts, providers)
2. Life & Disability Insurance
3. Retirement Benefits ({"PF, Gratuity, NPS" if is_indian else "401k, Pension"})
4. Wellness Programs (gym, mental health, annual checkups)
5. Learning & Development Budget
6. Stock Options / RSUs / ESOPs
7. Meal & Transport Benefits
8. Relocation Assistance
9. Employee Assistance Program
10. Contact Information for Benefits

Use specific amounts ({"INR" if is_indian else "USD"}), realistic provider names, and detailed eligibility criteria.
At least 1200 words. Write as an actual company benefits document."""
                response = llm.invoke(prompt)
                if response and len(response) > 500:
                    return response
            except Exception as e:
                print(f"LLM generation failed for benefits guide: {e}")

        return self._template_benefits_guide(info, is_indian)

    # ========================================================================
    # TEMPLATE FALLBACKS (used when LLM is unavailable or fails)
    # ========================================================================

    def _template_hr_handbook(self, info: Dict) -> str:
        company = info.get("full_name", "The Company")
        hq = info.get("headquarters", "Global")
        ceo = info.get("ceo", "the CEO")
        founded = info.get("founded", "N/A")
        employees = info.get("employees", "thousands of")
        industry = info.get("industry", "Technology")
        culture = info.get("work_culture", "professional and collaborative")
        domain = company.lower().replace(" ", "").replace(".", "").replace(",", "")[:20]

        return f"""
================================================================================
                        {company.upper()}
                           EMPLOYEE HANDBOOK {datetime.now().year}
================================================================================

                         CONFIDENTIAL — FOR INTERNAL USE ONLY

================================================================================
CHAPTER 1: WELCOME & COMPANY OVERVIEW
================================================================================

Welcome to {company}! We are thrilled to have you join our team.
Founded in {founded}, {company} has grown into one of the leading organizations
in the {industry} sector with {employees} employees worldwide.

Our headquarters are located in {hq}, and we operate across multiple
global locations. Under the leadership of {ceo}, we continue to push
the boundaries of innovation.

Our work culture is built around being {culture}.

================================================================================
CHAPTER 2: MISSION, VISION & CORE VALUES
================================================================================

MISSION STATEMENT:
To deliver world-class {industry.lower()} solutions that create lasting value
for our clients, employees, and communities.

VISION:
To be the most trusted and innovative partner in the {industry.lower()} space.

CORE VALUES:
1. INNOVATION — We embrace change and continuously improve
2. INTEGRITY — We conduct business with the highest ethical standards
3. COLLABORATION — We work together to achieve extraordinary results
4. CUSTOMER FOCUS — Our clients' success drives everything we do
5. EXCELLENCE — We strive for the highest quality in all we do

================================================================================
CHAPTER 3: CODE OF CONDUCT
================================================================================

All employees are expected to maintain the highest standards of professional conduct:

PROFESSIONAL BEHAVIOR:
- Treat all colleagues, clients, and vendors with respect and dignity
- Maintain confidentiality of proprietary information and client data
- Avoid conflicts of interest and disclose any potential conflicts
- Use company resources responsibly and only for business purposes
- Comply with all applicable laws, regulations, and company policies

WORKPLACE COMMUNICATION:
- Use professional language in all communications
- Be responsive to messages within 4 business hours
- Keep meetings focused and time-bound
- Practice active listening and provide constructive feedback

SOCIAL MEDIA POLICY:
- Do not share confidential company information on social media
- Clearly state that personal views do not represent the company
- Seek approval before posting about the company officially

================================================================================
CHAPTER 4: WORKPLACE ETHICS & ANTI-HARASSMENT POLICY
================================================================================

{company} is committed to providing a safe, inclusive, and
harassment-free workplace for everyone.

ZERO TOLERANCE POLICY:
- Sexual harassment (verbal, physical, or visual)
- Bullying, intimidation, or threats
- Discrimination in hiring, promotion, or compensation
- Retaliation against anyone who reports misconduct

REPORTING PROCEDURES:
1. Report to your immediate manager
2. Contact HR directly at ethics@{domain}.com
3. Use the anonymous Ethics Hotline
4. File a formal complaint through the HR portal

================================================================================
CHAPTER 5: DRESS CODE POLICY
================================================================================

{company} follows a SMART CASUAL dress code for regular workdays.

GENERAL GUIDELINES:
- Smart casual attire Monday through Thursday
- Casual Fridays allow jeans and sneakers
- Business formal required for client meetings
- Traditional/ethnic wear is welcome and encouraged

================================================================================
CHAPTER 6: WORKING HOURS & ATTENDANCE
================================================================================

STANDARD WORKING HOURS:
- Regular hours: 9:00 AM to 6:00 PM (Monday to Friday)
- Core hours (mandatory): 10:00 AM to 4:00 PM
- Flexible timing: Start between 8:00 AM and 10:00 AM
- Lunch break: 1 hour

ATTENDANCE TRACKING:
- Log attendance via the HRMS portal or biometric system
- Remote employees must check in by 10:00 AM
- Unplanned absences must be reported before 9:30 AM

WORK FROM HOME:
- Up to 2-3 WFH days per week (role dependent)
- WFH requests submitted via HRMS
- New employees: 90 days before availing WFH

================================================================================
CHAPTER 7: PERFORMANCE REVIEW PROCESS
================================================================================

REVIEW CYCLE:
- Annual Performance Review: March-April
- Mid-Year Check-in: September-October
- Quarterly 1-on-1s with manager
- 360-Degree Feedback collected annually

RATING SCALE:
- 5 (Exceptional): Consistently exceeds expectations
- 4 (Exceeds): Frequently goes above and beyond
- 3 (Meets): Consistently meets requirements
- 2 (Needs Improvement): Partially meets expectations
- 1 (Unsatisfactory): Fails to meet minimum standards

================================================================================
CHAPTER 8: GRIEVANCE & COMPLAINT PROCEDURES
================================================================================

FORMAL GRIEVANCE PROCESS:
1. Submit written grievance through HRMS portal
2. Acknowledgment within 2 business days
3. Investigation within 10 business days
4. Resolution communicated with action plan

================================================================================
CHAPTER 9: SEPARATION & EXIT POLICY
================================================================================

NOTICE PERIOD:
- Junior roles: 30 days
- Senior roles: 60-90 days
- Notice period buyout available

RESIGNATION PROCESS:
1. Submit resignation through HRMS
2. Manager retention discussion within 3 days
3. Exit interview with HR
4. Knowledge transfer during notice period
5. Full and final settlement within 45 days

================================================================================
CHAPTER 10: HR DEPARTMENT CONTACTS
================================================================================

GENERAL HR INQUIRIES:
  Email: hr@{domain}.com
  Phone: Available on internal directory

ETHICS & COMPLIANCE:
  Email: ethics@{domain}.com

PAYROLL:
  Email: payroll@{domain}.com

BENEFITS:
  Email: benefits@{domain}.com

================================================================================
                    © {datetime.now().year} {company}
                         All Rights Reserved.
================================================================================
"""

    def _template_it_guide(self, info: Dict) -> str:
        company = info.get("full_name", "The Company")
        tech_stack = info.get("tech_stack", "Various technologies")
        domain = company.lower().replace(" ", "").replace(".", "").replace(",", "")[:20]

        return f"""
================================================================================
                        {company.upper()}
                    IT SETUP & ONBOARDING GUIDE {datetime.now().year}
================================================================================

CHAPTER 1: DAY-1 IT CHECKLIST
================================================================================

Before your first day, our IT team will prepare:
□ Laptop (pre-configured with company image)
□ Employee ID badge with building access
□ Corporate email account ({'{'}firstname{'}'}.{'{'}lastname{'}'}@{domain}.com)
□ VPN credentials
□ HRMS portal access
□ Communication tools access (Slack/Teams, Zoom/Meet)

CHAPTER 2: EMAIL & COMMUNICATION SETUP
================================================================================

EMAIL:
- Corporate email via Microsoft 365 / Google Workspace
- Email format: firstname.lastname@{domain}.com
- Mobile email setup guide available on IT portal

COMMUNICATION TOOLS:
- Primary: Slack / Microsoft Teams
- Video Conferencing: Zoom / Google Meet
- Project Management: Jira / Asana

CHAPTER 3: VPN & NETWORK ACCESS
================================================================================

VPN SETUP:
- Download the company VPN client from the IT portal
- Use your corporate credentials to log in
- VPN is required for accessing internal systems remotely
- Always connect to VPN before accessing sensitive data

WIFI:
- Corporate WiFi: {domain.upper()}-CORP (use AD credentials)
- Guest WiFi: {domain.upper()}-GUEST

CHAPTER 4: DEVELOPMENT ENVIRONMENT
================================================================================

TECH STACK: {tech_stack}

Standard development tools will be pre-installed on your laptop.
Additional software requests can be made through the IT portal.

CHAPTER 5: SECURITY POLICIES
================================================================================

PASSWORD REQUIREMENTS:
- Minimum 12 characters
- Must include uppercase, lowercase, numbers, and special characters
- Change every 90 days
- No password reuse (last 12 passwords)

TWO-FACTOR AUTHENTICATION (2FA):
- 2FA is MANDATORY for all systems
- Use Google Authenticator or company-approved authenticator app
- Backup codes stored securely in password manager

DATA SECURITY:
- Never share credentials
- Lock your workstation when away (Win+L / Cmd+Ctrl+Q)
- Report suspicious emails to security@{domain}.com
- Do not use personal USB drives on company systems

CHAPTER 6: IT SUPPORT
================================================================================

IT HELPDESK:
  Email: itsupport@{domain}.com
  Portal: https://itsupport.{domain}.com
  Hours: 24/7 for critical issues, 9 AM - 6 PM for general queries

PRIORITY LEVELS:
- P1 (Critical): System down, cannot work — Response within 30 minutes
- P2 (High): Major feature broken — Response within 2 hours
- P3 (Medium): Minor issue, workaround exists — Response within 8 hours
- P4 (Low): Enhancement request — Response within 48 hours

================================================================================
                    © {datetime.now().year} {company}
================================================================================
"""

    def _template_leave_policy(self, info: Dict, is_indian: bool = False) -> str:
        company = info.get("full_name", "The Company")
        domain = company.lower().replace(" ", "").replace(".", "").replace(",", "")[:20]

        if is_indian:
            return f"""
================================================================================
                        {company.upper()}
                  LEAVE & ATTENDANCE POLICY {datetime.now().year}
================================================================================

CHAPTER 1: LEAVE TYPES & ENTITLEMENTS
================================================================================

EARNED LEAVE (EL) / PRIVILEGE LEAVE (PL):
- Entitlement: 18 days per year
- Accrual: 1.5 days per month
- Can be carried forward (max 45 days)
- Encashable at separation

CASUAL LEAVE (CL):
- Entitlement: 12 days per year
- Cannot be carried forward
- Maximum 3 consecutive days
- Cannot be combined with other leave types

SICK LEAVE (SL):
- Entitlement: 12 days per year
- Medical certificate required for 3+ consecutive days
- Can be carried forward (max 30 days)

MATERNITY LEAVE:
- 26 weeks for first two children (as per Maternity Benefit Act, 1961)
- 12 weeks for third child onwards
- Fully paid leave

PATERNITY LEAVE:
- 10 working days
- Must be taken within 3 months of child's birth

BEREAVEMENT LEAVE:
- 5 days for immediate family members
- 3 days for extended family

COMPENSATORY OFF:
- For work on holidays/weekends
- Must be availed within 30 days

CHAPTER 2: LEAVE APPLICATION PROCESS
================================================================================

1. Submit leave request via HRMS portal at least 3 days in advance
2. For emergency leave, inform manager by phone/email before 9:30 AM
3. Manager must approve/reject within 24 hours
4. HR will update attendance records

CHAPTER 3: ATTENDANCE TRACKING
================================================================================

- Biometric attendance system in all offices
- Remote check-in via HRMS portal/app
- Core hours: 10:00 AM to 4:00 PM
- Half-day: minimum 4 hours of work

CHAPTER 4: HOLIDAYS ({datetime.now().year})
================================================================================

National Holidays:
- Republic Day (January 26)
- Independence Day (August 15)
- Gandhi Jayanti (October 2)

Festival Holidays (varies by location):
- Diwali, Holi, Eid, Christmas, Pongal, Onam, Durga Puja
- Total: 10-12 holidays per year (location-specific list on HRMS)

3 Restricted Holidays (employee choice from approved list)

CHAPTER 5: CONTACT
================================================================================

Leave Management Desk:
  Email: leave.desk@{domain}.com
  Portal: HRMS > Leave Module

================================================================================
                    © {datetime.now().year} {company}
================================================================================
"""
        else:
            return f"""
================================================================================
                        {company.upper()}
                  LEAVE & ATTENDANCE POLICY {datetime.now().year}
================================================================================

CHAPTER 1: PAID TIME OFF (PTO)
================================================================================

PTO ENTITLEMENT:
- 0-2 years: 15 days PTO per year
- 2-5 years: 20 days PTO per year
- 5+ years: 25 days PTO per year
- PTO accrues monthly and can be carried forward (max 5 days)

SICK LEAVE:
- 10 days per year (separate from PTO)
- Doctor's note required for 3+ consecutive days

PARENTAL LEAVE:
- Primary caregiver: 16-20 weeks fully paid
- Secondary caregiver: 6-8 weeks fully paid
- Compliant with FMLA requirements

BEREAVEMENT LEAVE:
- 5 days for immediate family
- 3 days for extended family

JURY DUTY:
- Fully paid for duration of service

CHAPTER 2: HOLIDAYS ({datetime.now().year})
================================================================================

Company Holidays:
- New Year's Day
- Martin Luther King Jr. Day
- Presidents' Day
- Memorial Day
- Independence Day
- Labor Day
- Thanksgiving Day & Day After
- Christmas Eve & Christmas Day
- New Year's Eve (half day)

2 Floating Holidays (employee choice)

CHAPTER 3: ATTENDANCE & WORK SCHEDULE
================================================================================

- Standard hours: 9:00 AM - 5:00 PM
- Core hours: 10:00 AM - 3:00 PM
- Flexible scheduling available with manager approval
- Time tracking via HRMS system

CHAPTER 4: CONTACT
================================================================================

People Operations / Leave Management:
  Email: peopleops@{domain}.com
  Portal: HRMS > Time & Attendance

================================================================================
                    © {datetime.now().year} {company}
================================================================================
"""

    def _template_benefits_guide(self, info: Dict, is_indian: bool = False) -> str:
        company = info.get("full_name", "The Company")
        benefits = info.get("benefits_highlights", "Competitive package")
        domain = company.lower().replace(" ", "").replace(".", "").replace(",", "")[:20]

        if is_indian:
            return f"""
================================================================================
                        {company.upper()}
                   EMPLOYEE BENEFITS GUIDE {datetime.now().year}
================================================================================

CHAPTER 1: HEALTH INSURANCE
================================================================================

GROUP HEALTH INSURANCE:
- Coverage: INR 5,00,000 per annum (family floater)
- Covers: Employee, spouse, and up to 2 dependent children
- Includes: Hospitalization, day-care, pre/post hospitalization
- Dental and vision coverage included
- Pre-existing conditions covered after 1 year
- Maternity coverage: INR 75,000 (additional)

GROUP PERSONAL ACCIDENT INSURANCE:
- Coverage: 2x annual CTC

CHAPTER 2: RETIREMENT BENEFITS
================================================================================

PROVIDENT FUND (PF):
- 12% of basic salary (employee + employer contribution)
- As per EPF Act, 1952

GRATUITY:
- Payable after 5 years of continuous service
- As per Payment of Gratuity Act, 1972
- Formula: (15 × last drawn salary × years of service) / 26

NATIONAL PENSION SYSTEM (NPS):
- Optional with employer matching up to INR 50,000/year

CHAPTER 3: WELLNESS PROGRAMS
================================================================================

- Annual health checkup (fully sponsored)
- Mental health support: 6 free counseling sessions/year
- Gym membership reimbursement: Up to INR 2,000/month
- Ergonomic workstation assessment

CHAPTER 4: OTHER BENEFITS
================================================================================

{f"Known benefits at {company}: {benefits}" if benefits else ""}

- Learning budget: INR 50,000/year for courses and certifications
- Mobile reimbursement: INR 1,500/month
- Internet reimbursement (WFH): INR 1,000/month
- Meal coupons: INR 2,200/month (tax-exempt)
- Relocation assistance: Up to INR 1,00,000

CHAPTER 5: CONTACT
================================================================================

Benefits Desk:
  Email: benefits@{domain}.com

================================================================================
                    © {datetime.now().year} {company}
================================================================================
"""
        else:
            return f"""
================================================================================
                        {company.upper()}
                   EMPLOYEE BENEFITS GUIDE {datetime.now().year}
================================================================================

CHAPTER 1: HEALTH INSURANCE
================================================================================

MEDICAL:
- PPO and HMO plan options
- Coverage for employee, spouse, and dependents
- Company covers 80-90% of premiums
- Low deductibles and co-pays

DENTAL & VISION:
- Comprehensive dental (preventive, basic, major)
- Vision coverage including annual exam and lens allowance

CHAPTER 2: RETIREMENT BENEFITS
================================================================================

401(K) PLAN:
- Company matches 50% of contributions up to 6% of salary
- Immediate vesting of employer match
- Wide range of investment options
- Roth 401(k) option available

CHAPTER 3: STOCK & EQUITY
================================================================================

- Restricted Stock Units (RSUs) for eligible employees
- Vesting schedule: typically 4-year with 1-year cliff
- Employee Stock Purchase Plan (ESPP): 15% discount

CHAPTER 4: WELLNESS
================================================================================

{f"Known benefits at {company}: {benefits}" if benefits else ""}

- Annual wellness reimbursement: $1,200/year
- Mental health: free counseling through EAP
- Gym membership subsidy
- Annual health screening

CHAPTER 5: OTHER BENEFITS
================================================================================

- Education reimbursement: $5,250/year
- Commuter benefits (pre-tax)
- Life insurance: 2x annual salary
- Short and long-term disability
- Employee discounts program
- Adoption assistance: up to $10,000

CHAPTER 6: CONTACT
================================================================================

Benefits Team:
  Email: benefits@{domain}.com
  Portal: BenefitsConnect

================================================================================
                    © {datetime.now().year} {company}
================================================================================
"""


# ============================================================================
# COMPANY KNOWLEDGE BASE — Orchestrator
# ============================================================================
class CompanyKnowledgeBase:
    """
    Orchestrates the full pipeline:
    1. Fetch company info
    2. Generate onboarding documents
    3. Build vector store
    4. Cache for future use
    """

    def __init__(self):
        self.fetcher = CompanyDataFetcher()
        self.generator = OnboardingDocGenerator()
        self._cache = {}  # In-memory cache of (vector_store, company_info)

    def get_or_create(
        self,
        company_name: str,
        llm=None,
        progress_callback=None,
    ) -> Tuple[any, Dict]:
        """
        Get cached or create new company knowledge base.
        Returns (vector_store, company_info).
        """
        cache_key = company_name.lower().strip()

        # Check in-memory cache
        if cache_key in self._cache:
            if progress_callback:
                progress_callback("Loading from cache...", 1.0)
            return self._cache[cache_key]

        # Check disk cache
        cache_file = COMPANY_CACHE_DIR / f"{cache_key.replace(' ', '_')}_info.json"
        collection_name = _safe_collection_name(company_name)
        chroma_dir = CHROMA_DB_DIR / "companies"
        chroma_dir.mkdir(parents=True, exist_ok=True)

        if cache_file.exists():
            try:
                with open(cache_file, "r", encoding="utf-8") as f:
                    company_info = json.load(f)

                if progress_callback:
                    progress_callback("Loading cached company vector store...", 0.5)

                # Try to load existing vector store
                from chromadb import PersistentClient
                from langchain_community.vectorstores import Chroma

                vector_store = Chroma(
                    collection_name=collection_name,
                    embedding_function=get_embeddings(),
                    persist_directory=str(chroma_dir),
                )

                # Verify it has data
                count = vector_store._collection.count()
                if count > 0:
                    if progress_callback:
                        progress_callback("Company knowledge base loaded!", 1.0)
                    self._cache[cache_key] = (vector_store, company_info)
                    return vector_store, company_info
            except Exception as e:
                print(f"Cache load failed, rebuilding: {e}")

        # Build from scratch
        return self.build_realtime(company_name, llm, progress_callback)

    def build_realtime(
        self,
        company_name: str,
        llm=None,
        progress_callback=None,
    ) -> Tuple[any, Dict]:
        """
        Build company knowledge base from scratch in real-time.
        Returns (vector_store, company_info).
        """
        cache_key = company_name.lower().strip()

        # Step 1: Fetch company info
        if progress_callback:
            progress_callback("Fetching company information...", 0.05)

        company_info = self.fetcher.fetch_company_info(company_name, progress_callback)

        # Step 2: Generate onboarding documents
        if progress_callback:
            progress_callback("Generating onboarding documents...", 0.4)

        documents = self.generator.generate_all_documents(
            company_info, llm, progress_callback
        )

        if not documents:
            raise ValueError(f"Failed to generate documents for {company_name}")

        # Step 3: Build vector store
        if progress_callback:
            progress_callback("Building knowledge base (vector store)...", 0.9)

        collection_name = _safe_collection_name(company_name)
        chroma_dir = CHROMA_DB_DIR / "companies"
        chroma_dir.mkdir(parents=True, exist_ok=True)

        from langchain_community.vectorstores import Chroma

        vector_store = Chroma.from_documents(
            documents=documents,
            embedding=get_embeddings(),
            collection_name=collection_name,
            persist_directory=str(chroma_dir),
        )

        # Step 4: Cache to disk
        cache_file = COMPANY_CACHE_DIR / f"{cache_key.replace(' ', '_')}_info.json"
        try:
            with open(cache_file, "w", encoding="utf-8") as f:
                json.dump(company_info, f, indent=2, ensure_ascii=False)
        except Exception as e:
            print(f"Warning: Could not cache company info to disk: {e}")

        # Step 5: In-memory cache
        self._cache[cache_key] = (vector_store, company_info)

        if progress_callback:
            progress_callback(f"✅ {company_info.get('full_name', company_name)} knowledge base ready!", 1.0)

        return vector_store, company_info

    def clear_cache(self, company_name: str = None):
        """Clear cached company data."""
        if company_name:
            key = company_name.lower().strip()
            self._cache.pop(key, None)
            cache_file = COMPANY_CACHE_DIR / f"{key.replace(' ', '_')}_info.json"
            if cache_file.exists():
                cache_file.unlink()
        else:
            self._cache.clear()

    def list_cached_companies(self) -> List[str]:
        """List all cached company names."""
        cached = []
        if COMPANY_CACHE_DIR.exists():
            for f in COMPANY_CACHE_DIR.glob("*_info.json"):
                try:
                    with open(f, "r", encoding="utf-8") as fh:
                        data = json.load(fh)
                        cached.append(data.get("full_name", data.get("query_name", f.stem)))
                except Exception:
                    cached.append(f.stem.replace("_", " ").title())
        return cached
