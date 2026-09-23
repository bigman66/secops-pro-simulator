import json
import re
import random

def shuffle_options(q):
    """Randomizes the order of answer choices so 'A' is not always the correct option."""
    options = q.get("options", {})
    answers = q.get("answer", [])

    # Skip shuffling if answer keys contain descriptive text rather than simple letters
    if not options or not all(a in ["A", "B", "C", "D", "E"] for a in answers):
        return q

    # Pair each option text with its correctness flag
    items = [(text, letter in answers) for letter, text in options.items()]
    random.shuffle(items)

    # Re-assign option letters (A, B, C, D...)
    letters = ["A", "B", "C", "D", "E"][:len(items)]
    new_options = {}
    new_answers = []

    for letter, (text, is_correct) in zip(letters, items):
        new_options[letter] = text
        if is_correct:
            new_answers.append(letter)

    q_copy = dict(q)
    q_copy["options"] = new_options
    q_copy["answer"] = sorted(new_answers)
    return q_copy

def parse_existing_text_bank(filepath="04_SecOps_Pro_Validated_Master_Bank_163Q.txt"):
    """Robustly parses text bank by splitting directly on question ID headers."""
    try:
        with open(filepath, "r", encoding="utf-8", errors="ignore") as f:
            text = f.read()
    except FileNotFoundError:
        print(f"Warning: {filepath} not found. Starting with new questions only.")
        return []

    questions = []
    blocks = re.split(r"\n(?=ID:\s*)", text)

    for block in blocks:
        if "ID:" not in block:
            continue

        q_id_match = re.search(r"ID:\s*([A-Za-z0-9-]+)", block)
        domain_match = re.search(r"Domain:\s*([^\n\r]+)", block)
        objective_match = re.search(r"Objective:\s*([^\n\r]+)", block)
        answer_match = re.search(r"(?:Answer|Correct Answer):\s*([^\n\r]+)", block, re.IGNORECASE)
        q_part_match = re.search(r"Question:\s*(.*?)\n\s*(?:Answer|Correct Answer):", block, re.DOTALL | re.IGNORECASE)
        exp_match = re.search(r"Explanation:\s*(.*)", block, re.DOTALL | re.IGNORECASE)

        if not (q_id_match and answer_match and q_part_match):
            continue

        q_id = q_id_match.group(1).strip()
        domain = domain_match.group(1).strip() if domain_match else "1 - Security Operations Fundamentals"
        objective = objective_match.group(1).strip() if objective_match else "General Objective"
        raw_answer = answer_match.group(1).strip()
        q_part = q_part_match.group(1).strip()
        explanation = exp_match.group(1).strip() if exp_match else "No explanation provided."

        lines = q_part.split("\n")
        question_stem = []
        options = {}
        current_opt = None

        for line in lines:
            line_str = line.strip()
            opt_match = re.match(r"^([A-E])[\.\)]\s*(.*)", line_str)
            if opt_match:
                current_opt = opt_match.group(1)
                opt_text = opt_match.group(2).strip()
                options[current_opt] = opt_text
            elif current_opt:
                if line_str:
                    options[current_opt] = (options[current_opt] + " " + line_str).strip()
            else:
                question_stem.append(line_str)

        clean_answers = [a.strip().upper() for a in raw_answer.replace("and", ",").split(",") if a.strip()]

        questions.append({
            "id": q_id,
            "domain": domain,
            "objective": objective,
            "stem": "\n".join(question_stem).strip(),
            "options": options,
            "answer": clean_answers,
            "explanation": explanation,
            "is_multiselect": len(clean_answers) > 1
        })

    return questions

ADDITIONAL_QUESTIONS = [
    # --- DOMAIN 3: CORTEX XDR ---
    {
        "id": "SECOPS-201",
        "domain": "3 - Cortex XDR",
        "objective": "3.1 - Incident Investigation and Causality Chains",
        "stem": "An analyst investigating a ransomware alert in Cortex XDR opens the Causality View. Which process node represents the origin of the execution chain?",
        "options": {
            "A": "Root Process",
            "B": "Causality Group Owner (CGO)",
            "C": "Parent Artifact ID",
            "D": "Execution Sentinel"
        },
        "answer": ["B"],
        "explanation": "In Cortex XDR, the Causality Group Owner (CGO) is the process that initiated the causality group.",
        "is_multiselect": False
    },
    {
        "id": "SECOPS-202",
        "domain": "3 - Cortex XDR",
        "objective": "3.2 - XQL Queries and Data Analysis",
        "stem": "Which XQL stage command filters results based on specific attribute conditions?",
        "options": {
            "A": "comp",
            "B": "filter",
            "C": "fields",
            "D": "alter"
        },
        "answer": ["B"],
        "explanation": "In XQL (Cortex Query Language), the 'filter' stage narrows down query results based on boolean expression matches.",
        "is_multiselect": False
    },
    {
        "id": "SECOPS-203",
        "domain": "3 - Cortex XDR",
        "objective": "3.3 - Endpoint Response Actions",
        "stem": "Which response actions can an analyst execute directly on an endpoint from the Cortex XDR console? (Choose two)",
        "options": {
            "A": "Isolate Endpoint",
            "B": "Initiate Live Terminal Session",
            "C": "Update Windows OS Patches",
            "D": "Reboot Network Switch"
        },
        "answer": ["A", "B"],
        "explanation": "Cortex XDR allows responders to isolate endpoints network-wide and start a remote Live Terminal session for investigation.",
        "is_multiselect": True
    },

    # --- DOMAIN 4: CORTEX XSOAR ---
    {
        "id": "SECOPS-204",
        "domain": "4 - Cortex XSOAR",
        "objective": "4.1 - Playbook Automation and Integrations",
        "stem": "In Cortex XSOAR, how do automation tasks transfer data between integrated security tools during playbook execution?",
        "options": {
            "A": "Through SQL Database Queries",
            "B": "Via Context Data JSON Data Structure",
            "C": "By converting outputs into XML syslog files",
            "D": "Using direct API memory pointers"
        },
        "answer": ["B"],
        "explanation": "Cortex XSOAR stores and shares task outputs using Context Data—a hierarchical JSON dictionary accessible across playbook steps.",
        "is_multiselect": False
    },
    {
        "id": "SECOPS-205",
        "domain": "4 - Cortex XSOAR",
        "objective": "4.2 - Incident Fields and Layout Builder",
        "stem": "Which XSOAR component defines the layout and tabs visible to security analysts when reviewing an incident?",
        "options": {
            "A": "Layout Builder",
            "B": "Widget Dashboard",
            "C": "Indicator Repository",
            "D": "Playbook Debugger"
        },
        "answer": ["A"],
        "explanation": "The Layout Builder in Cortex XSOAR customizes incident views, field arrangements, and quick-action buttons.",
        "is_multiselect": False
    },

    # --- DOMAIN 5: CORTEX XSIAM ---
    {
        "id": "SECOPS-206",
        "domain": "5 - Cortex XSIAM",
        "objective": "5.1 - Data Ingestion, Collectors, and Broker VM",
        "stem": "Which architectural component in Cortex XSIAM collects syslog, WEC, and database logs from on-premises networks?",
        "options": {
            "A": "Cortex Data Lake Agent",
            "B": "Broker VM",
            "C": "XSOAR Engine",
            "D": "Prisma Access Connector"
        },
        "answer": ["B"],
        "explanation": "The Broker VM is an on-premises virtual machine that ingests local telemetry and forwards it securely to Cortex XSIAM.",
        "is_multiselect": False
    },
    {
        "id": "SECOPS-207",
        "domain": "5 - Cortex XSIAM",
        "objective": "5.2 - Alert Stitching and Analytics",
        "stem": "How does Cortex XSIAM reduce alert fatigue across heterogeneous security data sources?",
        "options": {
            "A": "By deleting low-severity alerts after 1 hour",
            "B": "Using AI analytics to stitch related alerts into unified incidents",
            "C": "By disabling network log ingestion during peak hours",
            "D": "By requiring manual approval for every incoming alert"
        },
        "answer": ["B"],
        "explanation": "Cortex XSIAM uses machine learning and causality analytics to correlate and stitch disparate alerts into single incidents.",
        "is_multiselect": False
    }
]

if __name__ == "__main__":
    # Seed generator for reproducible shuffling
    random.seed(42)

    raw_list = parse_existing_text_bank() + ADDITIONAL_QUESTIONS
    # Shuffle options for every question in the bank
    shuffled_list = [shuffle_options(q) for q in raw_list]

    with open("questions.json", "w", encoding="utf-8") as f:
        json.dump(shuffled_list, f, indent=2, ensure_ascii=False)
    
    print(f"✅ Successfully shuffled options and compiled {len(shuffled_list)} questions into 'questions.json'!")