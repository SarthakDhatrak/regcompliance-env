from __future__ import annotations

import random
import textwrap
from typing import Dict, Optional

# ---------------------------------------------------------------------------
# Static pools for randomisation
# ---------------------------------------------------------------------------

_STARTUP_NAMES = [
    "NovaTech Solutions Pvt Ltd",
    "Axiom Digitech Pvt Ltd",
    "Cerebra Software Pvt Ltd",
    "Luminary Fintech Pvt Ltd",
    "Helix Platforms Pvt Ltd",
    "Zenith Analytics Pvt Ltd",
    "Orion Cloud Services Pvt Ltd",
    "Prism LegalTech Pvt Ltd",
    "Vortex Data Systems Pvt Ltd",
    "Catalyst Infoworks Pvt Ltd",
]

_CITIES = ["Bengaluru", "Mumbai", "Pune", "Hyderabad", "New Delhi"]

_CITY_ADDRESSES = {
    "Bengaluru": ("4th Floor, Prestige Tower, MG Road", "560001", "Karnataka"),
    "Mumbai":    ("Level 12, One BKC, Bandra Kurla Complex", "400051", "Maharashtra"),
    "Pune":      ("3rd Floor, Nucleus Mall, Church Road", "411001", "Maharashtra"),
    "Hyderabad": ("8th Floor, Cyber Towers, HITEC City", "500081", "Telangana"),
    "New Delhi": ("5th Floor, DLF Cyber Hub, Sector 24, Gurugram", "122002", "Haryana"),
}

_FOREIGN_VENDORS = [
    ("CloudServe Ltd",        "22 Canary Wharf, London E14 5AB", "England and Wales", "UK"),
    ("DataBridge Inc",        "350 Fifth Avenue, New York NY 10118", "Delaware, USA", "US"),
    ("NexGen Solutions Ltd",  "15 St James's Square, London SW1Y 4LB", "England and Wales", "UK"),
    ("TechSpan Global Inc",   "1 Market Street, San Francisco CA 94105", "California, USA", "US"),
    ("Aldgate Systems Ltd",   "30 Old Broad Street, London EC2N 1HQ", "England and Wales", "UK"),
]

_FOREIGN_DIRECTORS = [
    ("Jonathan Hale",  "British", "UK"),
    ("Emily Stratton", "British", "UK"),
    ("Marcus Webb",    "American", "US"),
    ("Claire Dubois",  "French",  "EU"),
    ("Stefan Braun",   "German",  "EU"),
]

_INVESTOR_FUNDS = [
    "TechCapital UK Fund II",
    "BlueSky Ventures LP",
    "Atlantic Crossover Fund III",
    "Meridian Growth Capital",
    "NorthStar VC Partners",
]

_FOREIGN_VENDOR_DEVCOS = [
    ("DevBridge Technologies Pte Ltd", "18 Raffles Quay, #22-00, Singapore 048582", "Singapore"),
    ("CodeNest Systems Ltd",           "10 Marina Boulevard, Marina Bay, Singapore 018983", "Singapore"),
    ("TechForge Pte Ltd",              "8 Shenton Way, #46-01, Singapore 068811", "Singapore"),
]

_FOUNDER_PAIRS = [
    ("Arjun Mehta",    "Priya Kapoor"),
    ("Rohan Singh",    "Ananya Sharma"),
    ("Karan Malhotra", "Sneha Reddy"),
    ("Vivek Nair",     "Divya Iyer"),
    ("Amit Gupta",     "Pooja Verma"),
]

_EMPLOYEE_NAMES = [
    "Rohan Sharma", "Nikhil Tiwari", "Aditya Patel",
    "Meera Joshi",  "Saurabh Rao",   "Tanvi Desai",
]

_FOUNDING_YEARS = list(range(2018, 2024))

_CONTRACT_VALUES_LAKHS = list(range(5, 51, 5))  # 5L – 50L

_SERVICE_MONTHS = [12, 18, 24, 36]  # contract duration options

_ARBITRATION_SEATS = {
    "England and Wales": ("LCIA", "London, United Kingdom", "the laws of England and Wales"),
    "Delaware, USA":     ("AAA",  "New York, United States", "the laws of the State of Delaware"),
    "California, USA":   ("JAMS", "San Francisco, United States", "the laws of the State of California"),
}

_SINGAPORE_ARBI = ("SIAC", "Singapore", "the laws of Singapore")


# ---------------------------------------------------------------------------
# DocumentGenerator
# ---------------------------------------------------------------------------

class DocumentGenerator:
    """Generates fresh synthetic legal documents for each task.

    Each call to a generate_* method produces realistic but randomised text
    while always planting the exact compliance issues expected by the grader.

    Args:
        seed: Optional integer seed for reproducible output.
    """

    def __init__(self, seed: Optional[int] = None) -> None:
        self._rng = random.Random(seed)

    # -----------------------------------------------------------------------
    # Public API
    # -----------------------------------------------------------------------

    def generate_task1_docs(self) -> Dict[str, str]:
        """Return a privacy policy MISSING the data retention clause."""
        return {"privacy_policy.txt": self._privacy_policy(issues={"missing_retention"})}

    def generate_task2_docs(self) -> Dict[str, str]:
        """Return vendor_agreement.txt and company_terms.txt with a jurisdiction conflict."""
        company = self._pick(_STARTUP_NAMES)
        city    = self._pick(_CITIES)
        addr    = _CITY_ADDRESSES[city]
        vendor  = self._pick(_FOREIGN_VENDORS)
        value_l = self._pick(_CONTRACT_VALUES_LAKHS)
        months  = self._pick(_SERVICE_MONTHS)
        year    = str(self._pick(_FOUNDING_YEARS))

        vendor_name, vendor_addr, vendor_law, vendor_flag = vendor
        arbi = _ARBITRATION_SEATS.get(vendor_law, ("LCIA", "London, United Kingdom", vendor_law))

        return {
            "vendor_agreement.txt": self._vendor_agreement_t2(
                company=company, city=city, addr=addr,
                vendor_name=vendor_name, vendor_addr=vendor_addr,
                vendor_law=vendor_law, value_l=value_l, months=months,
                arbi_body=arbi[0], arbi_seat=arbi[1], year=year,
            ),
            "company_terms.txt": self._company_terms(
                company=company, city=city, addr=addr, year=year,
            ),
        }

    def generate_task3_docs(self) -> Dict[str, str]:
        """Return all 5 task3 documents with all 10 compliance issues planted."""
        company = self._pick(_STARTUP_NAMES)
        city    = self._pick(_CITIES)
        addr    = _CITY_ADDRESSES[city]
        year    = str(self._pick(_FOUNDING_YEARS))
        founders = self._pick(_FOUNDER_PAIRS)
        investor_fund = self._pick(_INVESTOR_FUNDS)
        fdir    = self._pick(_FOREIGN_DIRECTORS)
        devco   = self._pick(_FOREIGN_VENDOR_DEVCOS)
        employee = self._pick(_EMPLOYEE_NAMES)
        value_l = self._pick(_CONTRACT_VALUES_LAKHS)
        months  = self._pick(_SERVICE_MONTHS)

        # Foreign director tuple: (name, nationality, country)
        fdir_name, fdir_nationality, _fdir_country = fdir
        # Dev company tuple: (name, address, law)
        devco_name, devco_addr, devco_law = devco

        return {
            "privacy_policy.txt": self._privacy_policy(
                company=company, city=city, addr=addr, year=year,
                issues={"missing_retention", "missing_grievance_officer",
                        "missing_dpa_reference"},
            ),
            "moa.txt": self._moa(
                company=company, city=city, addr=addr, year=year,
                founders=founders, investor_fund=investor_fund,
                fdir_name=fdir_name, fdir_nationality=fdir_nationality,
            ),
            "shareholder_agreement.txt": self._shareholder_agreement(
                company=company, city=city, year=year,
                founders=founders, investor_fund=investor_fund,
            ),
            "vendor_contract.txt": self._vendor_contract_t3(
                company=company, city=city, addr=addr,
                devco_name=devco_name, devco_addr=devco_addr, devco_law=devco_law,
                value_l=value_l, months=months, year=year,
            ),
            "employment_agreement.txt": self._employment_agreement(
                company=company, city=city, addr=addr, year=year,
                founders=founders, employee=employee,
            ),
        }

    # -----------------------------------------------------------------------
    # Private helpers
    # -----------------------------------------------------------------------

    def _pick(self, seq: list):
        return self._rng.choice(seq)

    def _short_name(self, company: str) -> str:
        """Return abbreviated company name (first word before space)."""
        return company.split()[0]

    def _cin(self) -> str:
        digits = "".join(str(self._rng.randint(0, 9)) for _ in range(6))
        return f"U72900KA{self._rng.randint(2018,2023)}PTC{digits}"

    def _email_domain(self, company: str) -> str:
        slug = self._short_name(company).lower()
        return f"{slug}solutions.in"

    def _date(self, year: str, month: int = 1) -> str:
        months = ["January", "February", "March", "April", "May", "June",
                  "July", "August", "September", "October", "November", "December"]
        day = self._rng.randint(1, 28)
        return f"{day} {months[month - 1]} {year}"

    # -----------------------------------------------------------------------
    # Document builders
    # -----------------------------------------------------------------------

    def _privacy_policy(
        self,
        company: Optional[str] = None,
        city: Optional[str] = None,
        addr: Optional[tuple] = None,
        year: Optional[str] = None,
        issues: Optional[set] = None,
    ) -> str:
        company = company or self._pick(_STARTUP_NAMES)
        city    = city    or self._pick(_CITIES)
        addr    = addr    or _CITY_ADDRESSES[city]
        year    = year    or str(self._pick(_FOUNDING_YEARS))
        issues  = issues  or {"missing_retention"}
        domain  = self._email_domain(company)
        cin     = self._cin()
        short   = self._short_name(company)
        street, pin, state = addr
        eff_date = self._date(year, self._rng.randint(1, 12))

        # Grievance officer section differs based on planted issues
        if "missing_grievance_officer" in issues:
            grievance_section = f"""\
7. CONTACT AND GRIEVANCES

For data privacy queries, please contact:

Data Privacy Team
{company}
{street}
{city} - {pin}, {state}
Email: privacy@{domain}
Phone: +91-80-{self._rng.randint(1000,9999)}-{self._rng.randint(1000,9999)}

Note: A formally designated Grievance Officer with name and contact details, \
as mandated by the IT (Intermediary Guidelines and Digital Media Ethics Code) Rules, \
2021, and the DPDP Act, 2023, has not been explicitly appointed and is not identified \
in this Policy."""
        else:
            officer_name = self._pick(["Rahul Saxena", "Anita Nair", "Deepak Menon"])
            grievance_section = f"""\
7. GRIEVANCE OFFICER

In accordance with the Information Technology (Intermediary Guidelines and Digital \
Media Ethics Code) Rules, 2021, and the Digital Personal Data Protection Act, 2023, \
the Grievance Officer is:

Name: {officer_name}
Designation: Data Protection Officer
Email: grievance@{domain}
Phone: +91-80-{self._rng.randint(1000,9999)}-{self._rng.randint(1000,9999)}
Response time: Within 30 days of receipt of complaint."""

        # Data sharing section: optionally missing DPA reference
        if "missing_dpa_reference" in issues:
            sharing_note = (
                "We share data with cloud infrastructure providers and payment processors "
                "under contractual terms."
            )
        else:
            sharing_note = (
                "We share data with cloud infrastructure providers and payment processors "
                "under formal Data Processing Agreements (DPAs) compliant with DPDP Act 2023 Section 8(2)."
            )

        # Retention section: always MISSING for task1/task3
        retention_placeholder = ""  # deliberately omitted

        policy = f"""\
PRIVACY POLICY

{company}
Effective Date: {eff_date}
Version 1.0
CIN: {cin}

---

1. INTRODUCTION

{company} ("{short}", "we", "us", or "our"), incorporated under the Companies Act, 2013, \
with its registered office in {city}, {state}, India, is committed to protecting the \
personal data of users of our platform and related services ("Services").

By using our Services, you agree to this Privacy Policy.

---

2. INFORMATION WE COLLECT

We collect the following categories of personal data:

(a) Identity Data: full name, date of birth, government-issued identification where \
required for KYC compliance.
(b) Contact Data: email address, phone number, postal address.
(c) Financial Data: bank account details, UPI identifiers, and transaction records.
(d) Technical Data: IP address, device identifiers, browser type, operating system, \
session logs, and usage data.
(e) Document Data: contracts, filings, or other documents uploaded to our platform.

---

3. DATA HANDLING AND USE

{retention_placeholder}
We process personal data for the following purposes:

- Providing and operating our Services
- Processing payments and maintaining financial records
- Conducting KYC verification under applicable Indian law
- Communicating service updates and alerts
- Detecting fraud and ensuring platform security
- Meeting legal and regulatory obligations

We process data on the basis of contractual necessity, legal obligation, and legitimate \
business interests.

---

4. DATA SHARING

We do not sell personal data. We share data with:

(a) Service Providers: {sharing_note}
(b) Legal Authorities: where required by applicable law, including the IT Act, 2000, \
and the DPDP Act, 2023.
(c) Successors: in the event of a merger or acquisition, subject to equivalent \
data protection obligations.

---

5. YOUR RIGHTS

Under the Digital Personal Data Protection Act, 2023, you have the right to:

- Access your personal data
- Correct inaccurate or incomplete data
- Erasure of data no longer required
- Grievance redressal
- Nominate a representative in case of death or incapacity

---

6. SECURITY

We implement AES-256 encryption, role-based access controls, and regular security \
audits. No electronic system is completely immune to security incidents.

---

{grievance_section}

---

8. UPDATES TO THIS POLICY

We may update this Policy periodically. Significant changes will be communicated \
via our website or direct notification where required by law.

---

{company} | CIN: {cin}
"""
        return textwrap.dedent(policy)

    # ------------------------------------------------------------------ MOA

    def _moa(
        self,
        company: str,
        city: str,
        addr: tuple,
        year: str,
        founders: tuple,
        investor_fund: str,
        fdir_name: str,
        fdir_nationality: str,
    ) -> str:
        cin = self._cin()
        street, pin, state = addr
        f1, f2 = founders
        shares_f1 = self._rng.randint(35, 50) * 100_000
        shares_f2 = self._rng.randint(20, 34) * 100_000
        total = 100_000_000
        shares_inv = total - shares_f1 - shares_f2
        eff_date = self._date(year, self._rng.randint(1, 6))
        din_f1 = f"0{self._rng.randint(8000000, 9999999)}"
        din_f2 = f"0{self._rng.randint(8000000, 9999999)}"
        din_fd = f"0{self._rng.randint(8000000, 9999999)}"

        return f"""\
MEMORANDUM OF ASSOCIATION

{company}
CIN: {cin}
Registered under the Companies Act, 2013

---

I. NAME

The name of the Company is {company.replace("Pvt Ltd", "Private Limited")}.

II. REGISTERED OFFICE

The Registered Office of the Company is situated in the State of {state}. \
The current address is {street}, {city} - {pin}.

III. OBJECTS OF THE COMPANY

1. To carry on the business of providing technology-enabled compliance, legal-tech, \
document management, and SaaS-based workflow automation services to businesses, \
startups, and professionals across India and internationally.

2. To develop, deploy, and operate artificial intelligence-powered platforms and tools \
for regulatory compliance monitoring, contract analysis, and legal risk assessment.

3. To provide consulting, advisory, and training services in the domains of legal \
compliance, data protection, corporate governance, and regulatory affairs.

4. To acquire, develop, license, and commercialise intellectual property, including \
software, algorithms, and databases.

IV. LIABILITY

The liability of the members of the Company is limited.

V. CAPITAL

The Authorised Share Capital of the Company is Rs. 10,00,00,000 (Ten Crore Rupees) \
divided into 1,00,00,000 (One Crore) equity shares of Rs. 10/- each.

VI. SHAREHOLDING AT INCORPORATION

1. {f1} - {shares_f1:,} equity shares
2. {f2} - {shares_f2:,} equity shares
3. {investor_fund} - {shares_inv:,} equity shares

{investor_fund} holds {shares_inv / total * 100:.0f}% of the Company's equity. \
The Memorandum does not reference any FEMA compliance filings (such as FC-GPR with \
the Reserve Bank of India) confirming that this foreign investment has been duly \
reported and approved under the Foreign Exchange Management (Non-debt Instruments) \
Rules, 2019.

VII. DIRECTORS

The initial Board of Directors comprises:

1. {f1} (DIN: {din_f1}) - Managing Director - Indian National
2. {f2} (DIN: {din_f2}) - Executive Director - Indian National
3. {fdir_name} (DIN: {din_fd}) - Non-Executive Director - {fdir_nationality} National

{fdir_name} is appointed as a Director representing the interests of overseas investor \
{investor_fund}. This appointment has been made pursuant to the investment agreement \
dated {eff_date}. No specific approvals from the Reserve Bank of India under FEMA 2000 \
or the Foreign Exchange Management (Non-debt Instruments) Rules, 2019, have been \
obtained or referenced in connection with this directorship.

VIII. GOVERNING LAW

This Memorandum and all corporate actions of the Company shall be governed by the \
Companies Act, 2013, and all applicable laws of India. For all corporate disputes, \
the jurisdiction shall be the courts at {city}, {state}.

IX. DECLARATION

We, the several persons whose names are subscribed, are desirous of being formed into \
a Company in accordance with this Memorandum, and agree to take the number of shares \
set opposite our respective names.

---

Sd/- {f1}, Managing Director, Date: {eff_date}
Sd/- {f2}, Executive Director, Date: {eff_date}

Witnessed by: Prashant Iyer, Advocate
"""

    # -------------------------------------------------------- Shareholder Agmt

    def _shareholder_agreement(
        self,
        company: str,
        city: str,
        year: str,
        founders: tuple,
        investor_fund: str,
    ) -> str:
        f1, f2 = founders
        shares_f1 = self._rng.randint(35, 50) * 100_000
        shares_f2 = self._rng.randint(20, 34) * 100_000
        total = 100_000_000
        shares_inv = total - shares_f1 - shares_f2
        invested_cr = self._rng.randint(2, 10)
        eff_date = self._date(year, self._rng.randint(1, 6))
        esop_pct = self._rng.choice([8, 10, 12, 15])

        return f"""\
SHAREHOLDERS' AGREEMENT

{company}

This Shareholders' Agreement ("Agreement") is entered into as of {eff_date} by and among:

1. {f1} ("Founder 1");
2. {f2} ("Founder 2");
3. {investor_fund}, represented by its General Partner ("Investor"); and
4. {company}, the Company.

---

1. BACKGROUND

The Company was incorporated to develop technology-enabled compliance and legal-tech \
solutions. The Investor has agreed to invest INR {invested_cr} Crore, and the Parties \
wish to record their rights and obligations as shareholders.

2. SHARE CAPITAL AND OWNERSHIP

Following completion of the investment round:

Shareholder            | Shares         | %
-----------------------|----------------|-------
{f1:<22} | {shares_f1:>14,} | {shares_f1/total*100:.0f}%
{f2:<22} | {shares_f2:>14,} | {shares_f2/total*100:.0f}%
{investor_fund:<22} | {shares_inv:>14,} | {shares_inv/total*100:.0f}%
Total                  | {total:>14,} | 100%

3. FOUNDER LOCK-IN

Founder Shares shall be subject to a lock-in of 24 months from the Effective Date. \
Founders may not transfer or encumber Founder Shares without prior written consent \
of the Investor.

4. EQUITY ALLOCATION AND ESOP

The Company may allocate equity or stock options to employees and advisors from an \
ESOP Pool set at {esop_pct}% of the fully-diluted share capital. All allocations \
require Board approval.

However, no specific vesting schedule, cliff period, or acceleration provisions for \
founder or employee equity have been defined in this Agreement or any attached \
Schedule. Vesting terms shall be determined at the Board's discretion without \
obligation to document them formally in this Agreement.

5. BOARD COMPOSITION

The Board shall comprise five (5) directors:
- Two (2) nominated jointly by Founders
- One (1) nominated by the Investor
- One (1) Independent Director
- One (1) Woman Director (Companies Act 2013, Section 149)

6. INVESTOR RIGHTS

(a) Information Rights: audited financials and quarterly management accounts within \
45 days of each quarter end.
(b) Anti-Dilution: broad-based weighted average anti-dilution protection.
(c) Pre-emption: right of first refusal on any new issuances.
(d) Tag-Along: right to participate in any Founder share sale exceeding 10%.

7. DRAG-ALONG

Shareholders holding more than 75% may require all others to participate in a \
company sale on equivalent terms.

8. RESERVED MATTERS

Prior written approval of the Investor is required for:
- Amendments to MOA or AOA
- Issuance of new securities or convertible instruments
- Debt in excess of INR 1 Crore
- Mergers, acquisitions, or restructuring

9. CONFIDENTIALITY

All terms of this Agreement are confidential for 5 years after termination.

10. GOVERNING LAW

This Agreement shall be governed by the laws of India. All disputes shall be resolved \
by arbitration in {city} under the Arbitration and Conciliation Act, 1996.

---

Signed:

________________________          ________________________
{f1:<24}   {f2}
(Founder 1)                       (Founder 2)

________________________          ________________________
{investor_fund:<24}   {company}
(Investor)                        (Company)
"""

    # ----------------------------------------------------- Vendor Agreement T2

    def _vendor_agreement_t2(
        self,
        company: str,
        city: str,
        addr: tuple,
        vendor_name: str,
        vendor_addr: str,
        vendor_law: str,
        value_l: int,
        months: int,
        arbi_body: str,
        arbi_seat: str,
        year: str,
    ) -> str:
        street, pin, state = addr
        eff_date = self._date(year, self._rng.randint(1, 12))
        monthly_fee = int(value_l * 100_000 / months)

        return f"""\
VENDOR SERVICE AGREEMENT

This Vendor Service Agreement ("Agreement") is entered into as of {eff_date} between:

{company}, having its registered office at {street}, {city} - {pin}, {state}, India \
("Client"); and

{vendor_name}, having its registered office at {vendor_addr} ("Vendor").

---

1. SCOPE OF SERVICES

The Vendor shall provide cloud infrastructure, data backup, and platform hosting \
services as described in Schedule A. The Vendor shall ensure minimum uptime of 99.5% \
per calendar month. Planned maintenance requires 72 hours advance notice.

2. PAYMENT TERMS

The Client shall pay a monthly retainer of INR {monthly_fee:,}, invoiced on the first \
business day of each month. Payment is due within 30 days. Overdue payments attract \
interest at 8% per annum.

3. TERM AND TERMINATION

This Agreement commences on {eff_date} and continues for {months} months. Either Party \
may terminate with 90 days written notice. Immediate termination is available for \
material breach unremedied within 30 days.

4. CONFIDENTIALITY

Each Party shall maintain the confidentiality of the other's proprietary information. \
Disclosure requires prior written consent except as required by applicable law.

5. DATA PROTECTION

The Vendor shall process personal data solely per the Client's instructions, in \
compliance with applicable data protection laws.

6. LIMITATION OF LIABILITY

Aggregate liability shall not exceed fees paid in the preceding 12 months. Neither \
Party is liable for indirect or consequential losses.

7. INTELLECTUAL PROPERTY

Pre-existing IP remains with its respective owner. Client-specific tools developed \
under this Agreement vest in the Client upon full payment.

8. FORCE MAJEURE

Neither Party is liable for delays caused by events beyond their reasonable control.

9. DISPUTE RESOLUTION

Any dispute arising from this Agreement shall be resolved by arbitration under the \
auspices of the {arbi_body}. The seat of arbitration shall be {arbi_seat}. The \
governing law of this Agreement shall be {vendor_law}, and the courts of \
{arbi_seat.split(",")[0]} shall have exclusive jurisdiction to enforce any award or \
grant interim relief.

10. ENTIRE AGREEMENT

This Agreement constitutes the entire agreement between the Parties on its subject \
matter.

---

For {company}:                    For {vendor_name}:
Signature: ________________       Signature: ________________
"""

    # ------------------------------------------------------- Company Terms T2

    def _company_terms(
        self,
        company: str,
        city: str,
        addr: tuple,
        year: str,
    ) -> str:
        street, pin, state = addr
        cin = self._cin()
        eff_date = self._date(year, self._rng.randint(1, 12))
        short = self._short_name(company)
        domain = self._email_domain(company)

        return f"""\
STANDARD TERMS OF SERVICE

{company}
Effective Date: {eff_date}
Version 2.1

---

1. ACCEPTANCE OF TERMS

By accessing or using the services provided by {company} ("{short}", "we", "us", or \
"our"), you ("User") agree to be bound by these Standard Terms of Service ("Terms").

2. SERVICES

{company} provides a technology-enabled compliance and document management platform \
for Indian startups, small businesses, and legal professionals.

3. USER ACCOUNTS

Users must create an account to access the Services and are responsible for \
maintaining the confidentiality of their credentials.

4. ACCEPTABLE USE

You may not use the Services for any unlawful purpose or in any manner that could \
damage or impair our platform.

5. INTELLECTUAL PROPERTY

All content and software provided through the Services are the exclusive property of \
{company}, protected under the Copyright Act, 1957. You are granted a limited, \
non-exclusive licence for internal business use only.

6. FEES AND PAYMENT

Subscription fees are billed in advance in Indian Rupees, inclusive of applicable GST.

7. LIMITATION OF LIABILITY

{company}'s liability shall not exceed fees paid in the preceding three months. We are \
not liable for indirect or consequential damages.

8. INDEMNIFICATION

You indemnify {company} from claims arising from your use of the Services or breach \
of these Terms.

9. MODIFICATIONS

{company} may modify these Terms at any time. Continued use constitutes acceptance.

10. TERMINATION

{company} may suspend or terminate access with reasonable notice, or immediately for \
serious breach.

11. PRIVACY

Your use is also governed by our Privacy Policy at www.{domain}/privacy.

12. GOVERNING LAW AND JURISDICTION

These Terms shall be governed by and construed in accordance with the laws of India. \
Any dispute arising out of or in connection with these Terms shall be subject to the \
exclusive jurisdiction of the courts located in {city}, {state}, India. Each Party \
irrevocably submits to such jurisdiction.

13. CONTACT

legal@{domain}

---

{company} | CIN: {cin}
"""

    # --------------------------------------------------- Vendor Contract T3

    def _vendor_contract_t3(
        self,
        company: str,
        city: str,
        addr: tuple,
        devco_name: str,
        devco_addr: str,
        devco_law: str,
        value_l: int,
        months: int,
        year: str,
    ) -> str:
        street, pin, state = addr
        eff_date = self._date(year, self._rng.randint(1, 6))
        monthly_sgd = self._rng.randint(10, 30) * 1_000

        return f"""\
VENDOR SERVICE CONTRACT

This Vendor Service Contract ("Contract") is entered into as of {eff_date} between:

{company}, having its registered office at {street}, {city} - {pin}, {state}, India \
("Client"); and

{devco_name}, having its principal place of business at {devco_addr} ("Vendor").

---

1. SCOPE OF WORK

The Vendor shall provide full-stack software development, DevOps setup, and technical \
support as detailed in the Statement of Work (Annexure I). A minimum of four senior \
engineers shall be dedicated to the Client's projects. Weekly progress reports are \
due every Friday.

2. FEES

The Client shall pay SGD {monthly_sgd:,} per month. Invoices are raised on the last \
working day of each month. Payment is due within 21 working days. Late payments \
attract a penalty of 1.5% per month.

3. TERM

This Contract commences {eff_date} and is valid for {months} months unless terminated \
earlier. Either Party may terminate without cause with 60 days written notice.

4. DELIVERABLES AND ACCEPTANCE

Deliverables are subject to a 14-day acceptance testing period. Failure to respond \
within 14 days constitutes deemed acceptance.

5. CONFIDENTIALITY

The Vendor shall keep all Client proprietary information strictly confidential during \
and for 3 years after the Contract term.

6. INTELLECTUAL PROPERTY

All work product created exclusively for the Client vests in the Client upon full \
payment. The Vendor retains its pre-existing tools and frameworks.

7. DATA SECURITY

The Vendor shall implement encryption, access controls, and audit logging to protect \
Client data.

8. LIMITATION OF LIABILITY

The Vendor's maximum aggregate liability shall not exceed 3 months' fees.

9. DISPUTE RESOLUTION

Any dispute arising out of or in connection with this Contract shall be resolved by \
arbitration administered by the Singapore International Arbitration Centre (SIAC) \
under its rules. The seat of arbitration shall be Singapore, and the governing law \
shall be the laws of {devco_law}. The courts of Singapore shall have exclusive \
jurisdiction to grant interim measures and enforce awards.

This Contract does not contain a provision for arbitration under the Arbitration and \
Conciliation Act, 1996, nor does it provide for dispute resolution under Indian law, \
notwithstanding that the Client is an Indian company with operations primarily within \
India. This creates a jurisdictional conflict with the Company's MOA, which specifies \
courts at {city}, {state} for all corporate disputes.

10. GOVERNING LAW

This Contract shall be governed by the laws of {devco_law}.

---

For {company}:                    For {devco_name}:
Signature: ________________       Signature: ________________
"""

    # ----------------------------------------------------- Employment Agmt

    def _employment_agreement(
        self,
        company: str,
        city: str,
        addr: tuple,
        year: str,
        founders: tuple,
        employee: str,
    ) -> str:
        _, f2 = founders
        street, pin, state = addr
        salary_l = self._rng.choice([18, 20, 22, 24, 28, 32])
        noncompete_months = self._rng.choice([30, 36, 42, 48])  # always > 12
        nonsolicitation_months = self._rng.choice([18, 24])
        eff_date = self._date(year, self._rng.randint(1, 6))
        bonus_pct = self._rng.choice([10, 15, 20])

        return f"""\
EMPLOYMENT AGREEMENT

{company}

This Employment Agreement ("Agreement") is entered into as of {eff_date} between:

{company}, having its registered office at {street}, {city} - {pin}, {state} \
("Company"); and

{employee} ("Employee").

---

1. POSITION AND COMMENCEMENT

The Employee is appointed as Senior Software Engineer effective {eff_date}, \
reporting to the Chief Technology Officer. Primary place of work: {city}.

2. PROBATION

Probation period of 6 months. During probation, either Party may terminate with \
15 days written notice.

3. COMPENSATION

(a) Fixed Gross Salary: INR {salary_l},00,000 per annum, payable monthly.
(b) Performance Bonus: Up to {bonus_pct}% of fixed salary based on annual review.
(c) Benefits: health insurance (self, spouse, two dependents), mobile reimbursement \
up to INR 1,500/month, meal vouchers.

4. WORKING HOURS

Standard hours: 9:30 AM - 6:30 PM, Monday to Friday. Reasonable overtime may be \
required without separate compensation for managerial roles.

5. LEAVES

18 days annual leave, 12 days casual/sick leave, and all public holidays.

6. CONFIDENTIALITY

The Employee agrees to maintain strict confidentiality of all proprietary information \
including client data, source code, and business strategies both during and after \
employment, indefinitely.

7. INTELLECTUAL PROPERTY

All work product developed by the Employee during the course of employment, including \
code, documentation, and inventions, shall belong exclusively to the Company. The \
Employee agrees to execute any additional documents required by the Company to perfect \
its rights.

Note: This Agreement does not contain a formal, operative IP assignment clause as \
required under the Copyright Act, 1957, Sections 17 and 18. The foregoing language \
is aspirational rather than a present-tense written assignment signed by the Employee \
in favour of the Company.

8. NON-DISCLOSURE

The Employee shall not disclose any trade secrets or proprietary information of the \
Company to any third party during or after employment, except as required by law.

9. NON-COMPETE AND NON-SOLICITATION

(a) Non-Compete: For {noncompete_months} months following termination or resignation \
for any reason, the Employee shall not, directly or indirectly, engage in, be employed \
by, consult for, or hold any interest in any business engaged in legal-tech, \
compliance-tech, or document management software targeting the Indian startup \
ecosystem. Indian courts have consistently held that such post-employment restrictions \
are in restraint of trade under Section 27 of the Indian Contract Act, 1872, and are \
generally unenforceable beyond 12 months.

(b) Non-Solicitation: For {nonsolicitation_months} months following end of employment, \
the Employee shall not solicit or recruit any employee, contractor, or advisor of \
the Company.

10. TERMINATION

After probation: 90 days written notice or pay in lieu. Immediate termination \
available for gross misconduct, fraud, or wilful neglect.

11. GOVERNING LAW

This Agreement shall be governed by the laws of India. Disputes shall be referred to \
arbitration in {city} under the Arbitration and Conciliation Act, 1996.

---

For {company}:                    Employee:
Signature: ________________       Signature: ________________
Name: {f2:<24}   Name: {employee}
Designation: Executive Director   Date: {eff_date}
Date: {eff_date}
"""
