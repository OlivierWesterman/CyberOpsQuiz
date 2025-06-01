import json

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
        
        for question_obj in questions_data:
            question_text = question_obj.get("question")
            if question_text and question_text not in seen_questions_text:
                unique_questions.append(question_obj)
                seen_questions_text.add(question_text)
            else:
                duplicates_found += 1
        
        # Write the deduplicated data to new file
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(unique_questions, f, indent=4, ensure_ascii=False)
        
        print(f"✅ Successfully processed {input_file}")
        print(f"   Original questions: {len(questions_data)}")
        print(f"   Unique questions: {len(unique_questions)}")
        print(f"   Duplicates removed: {duplicates_found}")
        print(f"   Output saved to: {output_file}")
        
    except FileNotFoundError:
        print(f"❌ Error: Could not find file '{input_file}'")
    except json.JSONDecodeError as e:
        print(f"❌ Error: Invalid JSON in '{input_file}': {e}")
    except Exception as e:
        print(f"❌ Error: {e}")

# Usage
if __name__ == "__main__":
    input_filename = "questions.json"
    output_filename = "questions_deduplicated.json"
    
    deduplicate_questions(input_filename, output_filename)
    
    # Optionally, uncomment the line below to replace the original file
    # import shutil
    # shutil.move(output_filename, input_filename)