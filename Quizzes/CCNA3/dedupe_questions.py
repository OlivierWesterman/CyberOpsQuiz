import json
import os

def deduplicate_questions(input_file, output_file):
    """Remove duplicate questions from a JSON file based on question text."""
    
    try:
        # Read the original file
        with open(input_file, 'r', encoding='utf-8') as f:
            questions_data = json.load(f)
        
        # Track unique questions
        unique_questions = []
        seen_questions_text = set()
        duplicates_found = 0
        
        print(f"📂 Processing: {input_file}...")

        for question_obj in questions_data:
            question_text = question_obj.get("question")
            
            if question_text:
                # .strip() removes invisible spaces at the start/end
                # This ensures "What is NAT?" matches "What is NAT? "
                clean_text = question_text.strip()
                
                if clean_text not in seen_questions_text:
                    unique_questions.append(question_obj)
                    seen_questions_text.add(clean_text)
                else:
                    duplicates_found += 1
                    # Optional: Print which ID was removed (good for debugging)
                    # print(f"   - Removed duplicate ID: {question_obj.get('id')}")
        
        # Write the deduplicated data to new file
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(unique_questions, f, indent=4, ensure_ascii=False)
        
        print(f"✅ Success! Processed {len(questions_data)} items.")
        print(f"   Unique questions saved: {len(unique_questions)}")
        print(f"   Duplicates removed: {duplicates_found}")
        print(f"   Output file: {output_file}")
        
    except FileNotFoundError:
        print(f"❌ Error: Could not find file at: {input_file}")
        print("   Make sure 'questions.json' is in the same folder as this script.")
    except json.JSONDecodeError as e:
        print(f"❌ Error: Invalid JSON in '{input_file}': {e}")
    except Exception as e:
        print(f"❌ Error: {e}")

# Usage
if __name__ == "__main__":
    # 1. Get the directory where THIS script is saved
    script_dir = os.path.dirname(os.path.abspath(__file__))
    
    # 2. Build the full path to the files based on that directory
    # This fixes the "File Not Found" error regardless of where you run the command from
    input_filename = os.path.join(script_dir, "questions.json")
    output_filename = os.path.join(script_dir, "questions_deduplicated.json")
    
    deduplicate_questions(input_filename, output_filename)