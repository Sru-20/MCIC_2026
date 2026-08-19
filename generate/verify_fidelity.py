#!/usr/bin/env python3
import json
import os
import sys

def validate_transcript(obj, line_num, file_path):
    """
    Validates a single transcript object against the schemas.json rules.
    Raises ValueError on validation failures.
    """
    required_keys = [
        "conversation_id",
        "attack_type",
        "turn_count",
        "turns",
        "final_transfer_attempted",
        "transfer_details",
        "ground_truth_label"
    ]
    
    # Check top-level keys
    for key in required_keys:
        if key not in obj:
            raise ValueError(f"Missing required key '{key}'")
            
    # Check types
    if not isinstance(obj["conversation_id"], str):
        raise ValueError("conversation_id must be a string")
        
    if obj["attack_type"] not in ["prompt_injection_merchant_content", "multiturn_trust_poisoning", "legitimate"]:
        raise ValueError(f"Invalid attack_type '{obj['attack_type']}'")
        
    if not isinstance(obj["turn_count"], int) or obj["turn_count"] < 1:
        raise ValueError("turn_count must be a positive integer")
        
    if not isinstance(obj["turns"], list) or len(obj["turns"]) != obj["turn_count"]:
        raise ValueError(f"turns must be a list of size turn_count ({obj['turn_count']}), got {len(obj['turns'])}")
        
    if not isinstance(obj["final_transfer_attempted"], bool):
        raise ValueError("final_transfer_attempted must be a boolean")
        
    # Check turns
    for idx, turn in enumerate(obj["turns"]):
        if not isinstance(turn, dict):
            raise ValueError(f"Turn {idx+1} must be an object")
        for tkey in ["turn_number", "role", "content"]:
            if tkey not in turn:
                raise ValueError(f"Turn {idx+1} is missing key '{tkey}'")
        if not isinstance(turn["turn_number"], int):
            raise ValueError(f"Turn {idx+1} turn_number must be an integer")
        if turn["role"] not in ["user", "attacker", "agent", "assistant", "tool_result", "agent_tool_call", "agent_reasoning"]:
            raise ValueError(f"Turn {idx+1} has invalid role '{turn['role']}'")
        if not isinstance(turn["content"], str):
            raise ValueError(f"Turn {idx+1} content must be a string")

    # Check transfer_details
    details = obj["transfer_details"]
    if not isinstance(details, dict):
        raise ValueError("transfer_details must be an object")
        
    for dkey in ["payee_id", "amount", "currency", "source_of_instruction"]:
        if dkey not in details:
            raise ValueError(f"transfer_details is missing key '{dkey}'")
            
    if details["payee_id"] is not None and not isinstance(details["payee_id"], str):
        raise ValueError("payee_id must be a string or null")
        
    if details["amount"] is not None and not isinstance(details["amount"], (int, float)):
        raise ValueError("amount must be a number or null")
        
    if details["currency"] is not None and not isinstance(details["currency"], str):
        raise ValueError("currency must be a string or null")
        
    if details["source_of_instruction"] is not None and details["source_of_instruction"] not in ["user_explicit", "agent_inferred", "external_content"]:
        raise ValueError(f"Invalid source_of_instruction '{details['source_of_instruction']}'")
        
    if obj["ground_truth_label"] not in ["fraud", "legitimate"]:
        raise ValueError(f"Invalid ground_truth_label '{obj['ground_truth_label']}'")

def verify_file(file_path):
    """Verifies all JSON lines in a JSONL file."""
    if not os.path.exists(file_path):
        print(f"[-] File not found: {file_path}")
        return False
        
    print(f"[*] Validating: {file_path}")
    count = 0
    errors = 0
    
    with open(file_path, "r", encoding="utf-8") as f:
        for idx, line in enumerate(f, 1):
            if not line.strip():
                continue
            try:
                obj = json.loads(line)
                validate_transcript(obj, idx, file_path)
                count += 1
            except Exception as e:
                print(f"  [ERROR] Line {idx}: {e}")
                errors += 1
                
    if errors > 0:
        print(f"[-] Validation failed for {file_path} with {errors} errors.")
        return False
    else:
        print(f"[+] Successfully validated {count} transcripts in {file_path}.")
        return True

def main():
    data_dir = "generate/data"
    files = [
        "flagship1_injections.jsonl",
        "flagship2_poisonings.jsonl",
        "legitimate_conversations.jsonl"
    ]
    
    all_ok = True
    for fname in files:
        fpath = os.path.join(data_dir, fname)
        if not verify_file(fpath):
            all_ok = False
            
    if all_ok:
        print("\n[+] Verification PASSED: All generated files strictly adhere to the schemas.json guidelines.")
        sys.exit(0)
    else:
        print("\n[-] Verification FAILED: Some files contain errors.")
        sys.exit(1)

if __name__ == "__main__":
    main()
