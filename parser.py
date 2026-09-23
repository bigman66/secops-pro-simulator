import re

def parse_master_bank(filepath="04_SecOps_Pro_Validated_Master_Bank_163Q.txt"):
    """Parses the SecOps-Pro master question text file into structured objects."""
    with open(filepath, "r", encoding="utf-8", errors="ignore") as f:
        text = f.read()

    questions = []
    blocks = text.split("========================================================================================")

    for block in blocks:
        if "ID: SECOPS-" not in block:
            continue

        q_id_match = re.search(r"ID:\s*(SECOPS-\d+)", block)
        domain_match = re.search(r"Domain:\s*([^\n]+)", block)
        objective_match = re.search(r"Objective:\s*([^\n]+)", block)
        answer_match = re.search(r"Answer:\s*([^\n]+)", block)
        q_part_match = re.search(r"Question:\s*\n(.*?)\nAnswer:", block, re.DOTALL)
        exp_match = re.search(r"Explanation:\s*\n(.*)", block, re.DOTALL)

        if not (q_id_match and answer_match and q_part_match):
            continue

        q_id = q_id_match.group(1).strip()
        domain = domain_match.group(1).strip() if domain_match else "Domain 1 - Security Operations Fundamentals"
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
            opt_match = re.match(r"^([A-E])\.(.*)", line_str)
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