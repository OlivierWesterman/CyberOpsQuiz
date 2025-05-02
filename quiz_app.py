import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import random
import json
import os
from PIL import Image, ImageTk

class QuizApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Enhanced Quiz App")
        self.root.geometry("1000x800")
        
        # Set theme and style
        self.style = ttk.Style()
        self.style.theme_use('clam')  # Use a modern theme
        
        # Configure custom styles
        self.style.configure('TFrame', background='#f5f5f5')
        self.style.configure('TLabel', background='#f5f5f5', font=('Arial', 11))
        self.style.configure('TButton', font=('Arial', 10, 'bold'))
        self.style.configure('Title.TLabel', font=('Arial', 16, 'bold'))
        self.style.configure('Counter.TLabel', font=('Arial', 12), foreground='#555555')
        self.style.configure('Question.TLabel', font=('Arial', 12, 'bold'), wraplength=700)
        self.style.configure('MatchItem.TLabel', font=('Arial', 11), background='#e0e0e0', padding=10)
        self.style.configure('MatchItem.Selected.TLabel', font=('Arial', 11), background='#b0d0ff', padding=10)
        self.style.configure('MatchItem.Correct.TLabel', font=('Arial', 11), background='#90EE90', padding=10)
        self.style.configure('MatchItem.Incorrect.TLabel', font=('Arial', 11), background='#FFCCCB', padding=10)
        
        # Add custom styles for correct and incorrect answers
        self.style.configure('Correct.TCheckbutton', background='#90EE90')  # Light green
        self.style.configure('Incorrect.TCheckbutton', background='#FFCCCB')  # Light red
        self.style.map('Correct.TCheckbutton', background=[('active', '#90EE90')])
        self.style.map('Incorrect.TCheckbutton', background=[('active', '#FFCCCB')])
        
        # Data attributes
        self.available_subjects = []
        self.selected_questions = []
        self.current_question = 0
        self.score = 0
        self.current_correct_answers = []
        self.feedback_shown = False
        
        # Matching question attributes
        self.left_selection = None
        self.right_selection = None
        self.match_pairs = []  # To store the user's matched pairs [(left_idx, right_idx), ...]
        self.correct_matches = []  # To store the correct match pairs
        
        # Create the main application structure
        self.setup_ui()
        
        # Load available subjects
        self.load_available_subjects()

    def resource_path(self, subject, relative_path):
        """Get the absolute path to a resource"""
        # Get the directory where the script is located
        script_dir = os.path.dirname(os.path.abspath(__file__))
        
        # Construct absolute path to the resource
        if subject:
            full_path = os.path.normpath(os.path.join(script_dir, "Quizzes", subject, relative_path))
        else:
            full_path = os.path.normpath(os.path.join(script_dir, "Quizzes", relative_path))
            
        return full_path

    def load_available_subjects(self):
        """Scan the Quizzes directory for available subjects"""
        try:
            quizzes_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "Quizzes")
            
            # Create the directory if it doesn't exist
            if not os.path.exists(quizzes_dir):
                os.makedirs(quizzes_dir)
                # Create a sample quiz if none exists
                self.create_sample_quiz()
                
            # Get subdirectories which represent subjects
            self.available_subjects = [d for d in os.listdir(quizzes_dir) 
                                      if os.path.isdir(os.path.join(quizzes_dir, d))]
            
            # Update the subject dropdown
            self.subject_combobox['values'] = self.available_subjects
            
            if self.available_subjects:
                self.subject_combobox.current(0)
                self.update_question_count()
            
        except Exception as e:
            messagebox.showerror("Error", f"Failed to load subjects: {str(e)}")

    def create_sample_quiz(self):
        """Create a sample quiz if no quizzes exist"""
        try:
            sample_dir = os.path.join(
                os.path.dirname(os.path.abspath(__file__)),
                "Quizzes", 
                "Sample Quiz"
            )
            os.makedirs(sample_dir)
            
            # Create a questions.json file
            sample_questions = [
                {
                    "question": "What is the capital of France?",
                    "options": ["London", "Berlin", "Paris", "Madrid"],
                    "correct": 2,
                    "image": None,
                    "type": "multiple_choice"
                },
                {
                    "question": "Which planet is known as the Red Planet?",
                    "options": ["Venus", "Mars", "Jupiter", "Saturn"],
                    "correct": 1,
                    "image": None,
                    "type": "multiple_choice"
                },
                {
                    "question": "Match the planets with their order from the Sun",
                    "left_items": ["Mercury", "Earth", "Mars"],
                    "right_items": ["First", "Third", "Fourth"],
                    "correct_matches": [[0, 0], [1, 1], [2, 2]],
                    "image": None,
                    "type": "matching"
                }
            ]
            
            with open(os.path.join(sample_dir, "questions.json"), 'w') as f:
                json.dump(sample_questions, f, indent=4)
                
        except Exception as e:
            messagebox.showerror("Error", f"Failed to create sample quiz: {str(e)}")

    def load_questions(self, subject):
        """Load questions from a JSON file for the selected subject"""
        try:
            questions_file = self.resource_path(subject, "questions.json")
            
            with open(questions_file, 'r') as f:
                questions = json.load(f)
                
            return questions
        except FileNotFoundError:
            messagebox.showerror("Error", f"Questions file not found for {subject}")
            return []
        except json.JSONDecodeError:
            messagebox.showerror("Error", f"Invalid JSON format in questions file for {subject}")
            return []
        except Exception as e:
            messagebox.showerror("Error", f"Failed to load questions: {str(e)}")
            return []

    def setup_ui(self):
        """Set up the user interface"""
        # Create main container frames
        self.main_frame = ttk.Frame(self.root)
        self.main_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)
        
        # Setup frames
        self.setup_frame = ttk.Frame(self.main_frame)
        self.setup_frame.pack(fill=tk.BOTH, pady=10)
        
        # Title
        ttk.Label(self.setup_frame, text="Quiz Application", style='Title.TLabel').pack(pady=10)
        
        # Subject selection
        subject_frame = ttk.Frame(self.setup_frame)
        subject_frame.pack(fill=tk.X, pady=5)
        
        ttk.Label(subject_frame, text="Select Subject:").pack(side=tk.LEFT, padx=5)
        self.subject_combobox = ttk.Combobox(subject_frame, state="readonly", width=30)
        self.subject_combobox.pack(side=tk.LEFT, padx=5)
        self.subject_combobox.bind("<<ComboboxSelected>>", lambda e: self.update_question_count())
        
        refresh_btn = ttk.Button(subject_frame, text="↻", width=3, 
                                command=self.load_available_subjects)
        refresh_btn.pack(side=tk.LEFT, padx=5)
        
        add_subject_btn = ttk.Button(subject_frame, text="Add New Subject", 
                                    command=self.add_new_subject)
        add_subject_btn.pack(side=tk.LEFT, padx=5)
        
        # Question count selection
        question_frame = ttk.Frame(self.setup_frame)
        question_frame.pack(fill=tk.X, pady=5)
        
        ttk.Label(question_frame, text="Number of Questions:").pack(side=tk.LEFT, padx=5)
        self.question_count_var = tk.StringVar(value="5")
        self.question_count = ttk.Spinbox(question_frame, from_=1, to=100, 
                                        textvariable=self.question_count_var, width=5)
        self.question_count.pack(side=tk.LEFT, padx=5)
        
        self.max_questions_label = ttk.Label(question_frame, text="(Max: 0)")
        self.max_questions_label.pack(side=tk.LEFT, padx=5)
        
        all_questions_btn = ttk.Button(question_frame, text="All Questions", 
                                     command=self.set_all_questions)
        all_questions_btn.pack(side=tk.LEFT, padx=5)
        
        # Start button
        ttk.Button(self.setup_frame, text="Start Quiz", 
                 command=self.start_quiz).pack(pady=10)
        
        # Quiz frame (initially hidden)
        self.quiz_frame = ttk.Frame(self.main_frame)
        
        # Question counter
        self.counter_label = ttk.Label(self.quiz_frame, text="", style='Counter.TLabel')
        self.counter_label.pack(pady=5)
        
        # Question display
        self.question_label = ttk.Label(self.quiz_frame, text="", 
                                      style='Question.TLabel', wraplength=700)
        self.question_label.pack(pady=20)
        
        # Image display
        self.image_frame = ttk.Frame(self.quiz_frame)
        self.image_frame.pack(pady=10)
        self.image_label = ttk.Label(self.image_frame)
        self.image_label.pack()
        
        # Answer options
        self.answers_frame = ttk.Frame(self.quiz_frame)
        self.answers_frame.pack(pady=10, fill=tk.X)
        
        # Matching questions frame
        self.matching_frame = ttk.Frame(self.quiz_frame)
        
        # Left and right columns for matching
        self.matching_columns_frame = ttk.Frame(self.matching_frame)
        self.matching_columns_frame.pack(pady=10, fill=tk.X)
        
        self.left_column = ttk.Frame(self.matching_columns_frame)
        self.left_column.pack(side=tk.LEFT, padx=20, fill=tk.Y)
        
        self.right_column = ttk.Frame(self.matching_columns_frame)
        self.right_column.pack(side=tk.RIGHT, padx=20, fill=tk.Y)
        
        # Matched pairs display
        self.matched_pairs_frame = ttk.Frame(self.matching_frame)
        self.matched_pairs_frame.pack(pady=10, fill=tk.X)
        
        # Add a feedback label
        self.feedback_label = ttk.Label(self.quiz_frame, text="", font=('Arial', 12, 'bold'))
        self.feedback_label.pack(pady=5)
        
        # Buttons
        self.button_frame = ttk.Frame(self.quiz_frame)
        self.button_frame.pack(pady=20)
        
        self.submit_btn = ttk.Button(self.button_frame, text="Check Answer", 
                                   command=self.check_answer)
        self.submit_btn.pack(side=tk.LEFT, padx=10)
        
        self.next_btn = ttk.Button(self.button_frame, text="Next Question", 
                                 command=self.next_question)
        self.next_btn.pack(side=tk.LEFT, padx=10)
        self.next_btn.pack_forget()  # Initially hidden

    def update_question_count(self):
        """Update the maximum question count based on the selected subject"""
        if not self.subject_combobox.get():
            return
            
        subject = self.subject_combobox.get()
        questions = self.load_questions(subject)
        
        if questions:
            max_count = len(questions)
            self.max_questions_label.config(text=f"(Max: {max_count})")
            # Update the spinbox range
            self.question_count.config(to=max_count)
            
            # Set a default value
            if max_count < int(self.question_count_var.get()):
                self.question_count_var.set(str(max_count))
        else:
            self.max_questions_label.config(text="(Max: 0)")
            self.question_count_var.set("0")

    def set_all_questions(self):
        """Set the question count to the maximum available"""
        if not self.subject_combobox.get():
            messagebox.showinfo("Info", "Please select a subject first")
            return
            
        subject = self.subject_combobox.get()
        questions = self.load_questions(subject)
        
        if questions:
            self.question_count_var.set(str(len(questions)))
        else:
            messagebox.showinfo("Info", "No questions available for this subject")

    def add_new_subject(self):
        """Create a new subject folder and template"""
        subject_name = tk.simpledialog.askstring("New Subject", 
                                               "Enter the name for the new subject:")
        
        if not subject_name:
            return
            
        try:
            # Create subject directory
            subject_dir = os.path.join(
                os.path.dirname(os.path.abspath(__file__)),
                "Quizzes", 
                subject_name
            )
            
            if os.path.exists(subject_dir):
                messagebox.showerror("Error", f"Subject '{subject_name}' already exists")
                return
                
            os.makedirs(subject_dir)
            os.makedirs(os.path.join(subject_dir, "Images"), exist_ok=True)
            
            # Create a template questions.json file
            template_questions = [
                {
                    "question": "Sample Question 1",
                    "options": ["Option 1", "Option 2", "Option 3", "Option 4"],
                    "correct": 0,
                    "image": None,
                    "type": "multiple_choice"
                },
                {
                    "question": "Sample Question 2 (with multiple correct answers)",
                    "options": ["Option 1", "Option 2", "Option 3", "Option 4"],
                    "correct": [0, 2],
                    "image": None,
                    "type": "multiple_choice"
                },
                {
                    "question": "Sample Matching Question",
                    "left_items": ["Item A", "Item B", "Item C"],
                    "right_items": ["Description 1", "Description 2", "Description 3"],
                    "correct_matches": [[0, 0], [1, 1], [2, 2]],
                    "image": None,
                    "type": "matching"
                }
            ]
            
            with open(os.path.join(subject_dir, "questions.json"), 'w') as f:
                json.dump(template_questions, f, indent=4)
                
            messagebox.showinfo("Success", 
                              f"Created subject '{subject_name}' with template questions.\n\n"
                              f"You can now edit the questions.json file in the folder:\n"
                              f"{subject_dir}")
                              
            # Refresh the subject list
            self.load_available_subjects()
            
            # Select the new subject
            index = self.available_subjects.index(subject_name)
            self.subject_combobox.current(index)
            self.update_question_count()
            
        except Exception as e:
            messagebox.showerror("Error", f"Failed to create subject: {str(e)}")

    def start_quiz(self):
        """Start the quiz with the selected subject and question count"""
        subject = self.subject_combobox.get()
        
        if not subject:
            messagebox.showinfo("Info", "Please select a subject first")
            return
            
        try:
            num_questions = int(self.question_count.get())
            
            # Load questions for the selected subject
            all_questions = self.load_questions(subject)
            
            if not all_questions:
                messagebox.showerror("Error", "No questions found for this subject")
                return
                
            if num_questions > len(all_questions):
                messagebox.showerror("Error", 
                                   f"Maximum number of questions is {len(all_questions)}")
                return
                
            # Select random questions
            self.selected_questions = random.sample(all_questions, num_questions)
            self.current_subject = subject
            self.current_question = 0
            self.score = 0
            
            # Hide setup frame and show quiz frame
            self.setup_frame.pack_forget()
            self.quiz_frame.pack(fill=tk.BOTH, expand=True)
            
            # Show the first question
            self.show_question()
            
        except ValueError:
            messagebox.showerror("Error", "Please enter a valid number of questions")

    def show_question(self):
        """Display the current question"""
        # Reset the feedback label
        self.feedback_label.config(text="")
        self.feedback_shown = False
            
        if self.current_question < len(self.selected_questions):
            question = self.selected_questions[self.current_question]
            question_type = question.get("type", "multiple_choice")  # Default to multiple choice
            
            # Set the question text and counter
            self.question_label.config(text=question["question"])
            self.counter_label.config(
                text=f"Question {self.current_question + 1} of {len(self.selected_questions)}"
            )
            
            # Display image if available
            image_path = question.get("image")
            if image_path:
                try:
                    full_path = self.resource_path(self.current_subject, image_path)
                    
                    image = Image.open(full_path)
                    # Calculate new dimensions while maintaining aspect ratio
                    width, height = image.size
                    max_width, max_height = 500, 400
                    
                    # Scale down if necessary
                    if width > max_width or height > max_height:
                        ratio = min(max_width/width, max_height/height)
                        new_width = int(width * ratio)
                        new_height = int(height * ratio)
                        image = image.resize((new_width, new_height), Image.Resampling.LANCZOS)
                        
                    photo = ImageTk.PhotoImage(image)
                    self.image_label.config(image=photo)
                    self.image_label.image = photo  # Keep a reference
                    self.image_frame.pack(pady=10)
                except Exception as e:
                    print(f"Error loading image: {e}")
                    self.image_frame.pack_forget()
            else:
                self.image_frame.pack_forget()
                
            # Show the appropriate question type
            if question_type == "matching":
                self.answers_frame.pack_forget()
                self.matching_frame.pack(pady=10, fill=tk.BOTH, expand=True)
                self.setup_matching_question(question)
            else:
                self.matching_frame.pack_forget()
                self.answers_frame.pack(pady=10, fill=tk.X)
                self.setup_answer_options(question)
            
            # Reset button states
            self.submit_btn.config(state='normal')
            self.next_btn.pack_forget()
        else:
            self.show_results()

    def setup_answer_options(self, question):
        """Set up the answer options for the current question"""
        # Clear previous options
        for widget in self.answers_frame.winfo_children():
            widget.destroy()
            
        self.answer_vars = []
        self.answer_buttons = []
        self.option_frames = []
        
        # Determine correct answers
        correct_answers = question["correct"]
        if not isinstance(correct_answers, list):
            correct_answers = [correct_answers]
            
        # Create pairs of options and correctness status
        option_pairs = [(opt, i in correct_answers) 
                       for i, opt in enumerate(question["options"])]
        
        # Optional: Shuffle the options (comment out if you want fixed order)
        random.shuffle(option_pairs)
        
        # Unpack the shuffled options
        options, correct_statuses = zip(*option_pairs)
        
        # Store the indices of correct answers in the shuffled order
        self.current_correct_answers = [i for i, is_correct in enumerate(correct_statuses) 
                                      if is_correct]
        
        # Create checkboxes for each option
        for i, option in enumerate(options):
            frame = ttk.Frame(self.answers_frame)
            frame.pack(fill=tk.X, pady=2)
            self.option_frames.append(frame)
            
            var = tk.IntVar()
            btn = ttk.Checkbutton(
                frame, 
                text=option,
                variable=var,
                padding=5
            )
            btn.pack(side=tk.LEFT, fill=tk.X, expand=True, anchor="w")
            
            self.answer_vars.append(var)
            self.answer_buttons.append(btn)

    def setup_matching_question(self, question):
        """Setup a matching type question"""
        # Clear previous items
        for widget in self.left_column.winfo_children():
            widget.destroy()
        for widget in self.right_column.winfo_children():
            widget.destroy()
        for widget in self.matched_pairs_frame.winfo_children():
            widget.destroy()
            
        # Reset selection and matches
        self.left_selection = None
        self.right_selection = None
        self.match_pairs = []
        
        # Store correct matches
        self.correct_matches = question["correct_matches"]
        
        # Get the items
        left_items = question["left_items"]
        right_items = question["right_items"]
        
        # Shuffle the right items for presentation
        shuffled_right = list(right_items)
        random.shuffle(shuffled_right)
        
        # Create left column labels
        ttk.Label(self.left_column, text="Items to Match", font=('Arial', 12, 'bold')).pack(pady=(0, 10))
        
        self.left_labels = []
        for i, item in enumerate(left_items):
            label = ttk.Label(self.left_column, text=item, style='MatchItem.TLabel')
            label.pack(fill=tk.X, pady=5)
            label.bind("<Button-1>", lambda e, idx=i: self.select_left_item(idx))
            self.left_labels.append(label)
            
        # Create right column labels
        ttk.Label(self.right_column, text="Matching Options", font=('Arial', 12, 'bold')).pack(pady=(0, 10))
        
        self.right_labels = []
        for i, item in enumerate(shuffled_right):
            label = ttk.Label(self.right_column, text=item, style='MatchItem.TLabel')
            label.pack(fill=tk.X, pady=5)
            label.bind("<Button-1>", lambda e, idx=i: self.select_right_item(idx))
            self.right_labels.append(label)
            
        # Create a frame to display matched pairs
        ttk.Label(self.matched_pairs_frame, text="Your Matches:", font=('Arial', 12, 'bold')).pack(anchor="w", pady=(20, 10))
        
        self.matched_pairs_display = ttk.Frame(self.matched_pairs_frame)
        self.matched_pairs_display.pack(fill=tk.X)
        
        # Store the original right items (for checking correct answers)
        self.original_right_items = right_items
        self.shuffled_right_items = shuffled_right

    def select_left_item(self, index):
        """Handle selection of an item from the left column"""
        # Reset styles
        for label in self.left_labels:
            label.configure(style='MatchItem.TLabel')
            
        # Set selected style
        self.left_labels[index].configure(style='MatchItem.Selected.TLabel')
        self.left_selection = index
        
        # If we have both selections, create a match
        if self.right_selection is not None:
            self.create_match_pair()

    def select_right_item(self, index):
        """Handle selection of an item from the right column"""
        # Reset styles
        for label in self.right_labels:
            label.configure(style='MatchItem.TLabel')
            
        # Set selected style
        self.right_labels[index].configure(style='MatchItem.Selected.TLabel')
        self.right_selection = index
        
        # If we have both selections, create a match
        if self.left_selection is not None:
            self.create_match_pair()

    def create_match_pair(self):
        """Create a match between selected left and right items"""
        # Check if this left item is already matched
        for pair in self.match_pairs:
            if pair[0] == self.left_selection:
                # Remove the existing match
                self.match_pairs.remove(pair)
                break
                
        # Add the new match
        self.match_pairs.append((self.left_selection, self.right_selection))
        
        # Reset selections
        self.left_selection = None
        self.right_selection = None
        
        # Reset all label styles
        for label in self.left_labels:
            label.configure(style='MatchItem.TLabel')
        for label in self.right_labels:
            label.configure(style='MatchItem.TLabel')
            
        # Update the display of matched pairs
        self.update_matched_pairs_display()

    def update_matched_pairs_display(self):
        """Update the display of matched pairs"""
        # Clear existing display
        for widget in self.matched_pairs_display.winfo_children():
            widget.destroy()
            
        if not self.match_pairs:
            ttk.Label(self.matched_pairs_display, text="No matches yet. Click on items to match them.").pack(anchor="w")
            return
            
        # Display each match
        for i, (left_idx, right_idx) in enumerate(self.match_pairs):
            frame = ttk.Frame(self.matched_pairs_display)
            frame.pack(fill=tk.X, pady=2)
            
            left_text = self.left_labels[left_idx]['text']
            right_text = self.right_labels[right_idx]['text']
            
            match_text = f"{left_text} ↔ {right_text}"
            match_label = ttk.Label(frame, text=match_text)
            match_label.pack(side=tk.LEFT, padx=5)
            
            # Add a delete button
            delete_btn = ttk.Button(frame, text="×", width=2, 
                                  command=lambda idx=i: self.delete_match(idx))
            delete_btn.pack(side=tk.RIGHT, padx=5)

    def delete_match(self, index):
        """Delete a match pair"""
        if 0 <= index < len(self.match_pairs):
            del self.match_pairs[index]
            self.update_matched_pairs_display()

    def check_matching_answer(self):
        """Check if the matching pairs are correct"""
        # Check if all items have been matched
        left_items = self.selected_questions[self.current_question]["left_items"]
        if len(self.match_pairs) != len(left_items):
            messagebox.showinfo("Incomplete", "Please match all items before checking answer.")
            return False
            
        # Convert user's matches from shuffled indices to original indices
        user_matches = []
        for left_idx, shuffled_right_idx in self.match_pairs:
            # Find the original index of the shuffled right item
            right_item = self.shuffled_right_items[shuffled_right_idx]
            original_right_idx = self.original_right_items.index(right_item)
            user_matches.append([left_idx, original_right_idx])
            
        # Check if user's matches match the correct matches
        is_correct = sorted(user_matches) == sorted(self.correct_matches)
        
        if is_correct:
            self.score += 1
            self.feedback_label.config(text="Correct!", foreground="green")
        else:
            self.feedback_label.config(text="Incorrect", foreground="red")
            
        # Update the visual feedback
        self.show_matching_feedback(user_matches)
        
        return True

    def show_matching_feedback(self, user_matches):
        """Show visual feedback for matching answers"""
        # For each user match, highlight correct or incorrect
        for left_idx, right_idx in self.match_pairs:
            # Get the corresponding original right index
            right_item = self.shuffled_right_items[right_idx]
            original_right_idx = self.original_right_items.index(right_item)
            
            # Check if this match is correct
            if [left_idx, original_right_idx] in self.correct_matches:
                # Correct match
                for widget in self.matched_pairs_display.winfo_children():
                    if self.left_labels[left_idx]['text'] in widget.winfo_children()[0]['text']:
                        widget.winfo_children()[0].configure(foreground="green", font=('Arial', 11, 'bold'))
            else:
                # Incorrect match
                for widget in self.matched_pairs_display.winfo_children():
                    if self.left_labels[left_idx]['text'] in widget.winfo_children()[0]['text']:
                        widget.winfo_children()[0].configure(foreground="red", font=('Arial', 11, 'bold'))
                        
        # Disable further matching
        for label in self.left_labels:
            label.unbind("<Button-1>")
        for label in self.right_labels:
            label.unbind("<Button-1>")
            
        # Disable buttons in the matched pairs display
        for widget in self.matched_pairs_display.winfo_children():
            if len(widget.winfo_children()) > 1:  # If there's a delete button
                widget.winfo_children()[1].configure(state="disabled")
                
        return True

    def check_answer(self):
        """Validate the user's answer and show visual feedback"""
        if self.feedback_shown:
            return
            
        question = self.selected_questions[self.current_question]
        question_type = question.get("type", "multiple_choice")
        
        if question_type == "matching":
            success = self.check_matching_answer()
            if not success:
                return
        else:
            # Standard multiple choice question
            selected_answers = [i for i, var in enumerate(self.answer_vars) if var.get() == 1]
            
            # Flag to track if the answer was correct
            is_correct = set(selected_answers) == set(self.current_correct_answers)
            
            # Apply visual feedback (highlight correct answers in green, incorrect selections in red)
            for i, btn in enumerate(self.answer_buttons):
                # For correct answers (always show these in green)
                if i in self.current_correct_answers:
                    btn.configure(style='Correct.TCheckbutton')
                # For incorrect selections (show in red)
                elif i in selected_answers:
                    btn.configure(style='Incorrect.TCheckbutton')
                    
            # Update the score if correct
            if is_correct:
                self.score += 1
                self.feedback_label.config(text="Correct!", foreground="green")
            else:
                self.feedback_label.config(text="Incorrect", foreground="red")
            
            # Disable further changes to checkboxes
            for btn in self.answer_buttons:
                btn.configure(state="disabled")
        
        # Disable the submit button and show the next button
        self.submit_btn.config(state="disabled")
        self.next_btn.pack(side=tk.LEFT, padx=10)
        
        # Set flag to indicate feedback has been shown
        self.feedback_shown = True

    def next_question(self):
        """Move to the next question"""
        self.current_question += 1
        self.show_question()

    def show_results(self):
        """Display the quiz results"""
        # Clear the quiz frame
        for widget in self.quiz_frame.winfo_children():
            widget.destroy()
            
        # Calculate score percentage
        score_percentage = (self.score / len(self.selected_questions)) * 100
        
        # Create results display
        results_frame = ttk.Frame(self.quiz_frame)
        results_frame.pack(expand=True, pady=50)
        
        ttk.Label(results_frame, text="Quiz Completed!", 
                style='Title.TLabel').pack(pady=10)
        
        result_text = f"Your Score: {self.score} out of {len(self.selected_questions)}\n"
        result_text += f"Percentage: {score_percentage:.1f}%"
        
        ttk.Label(results_frame, text=result_text, 
                font=('Arial', 14)).pack(pady=20)
        
        # Performance feedback
        if score_percentage >= 90:
            feedback = "Excellent! Outstanding performance!"
        elif score_percentage >= 70:
            feedback = "Good job! Well done!"
        elif score_percentage >= 50:
            feedback = "Not bad. Keep practicing!"
        else:
            feedback = "You might need more practice with this subject."
            
        ttk.Label(results_frame, text=feedback, 
                font=('Arial', 12)).pack(pady=10)
        
        # Buttons
        button_frame = ttk.Frame(results_frame)
        button_frame.pack(pady=20)
        
        ttk.Button(button_frame, text="Try Again", 
                 command=self.restart_quiz).pack(side=tk.LEFT, padx=10)
        
        ttk.Button(button_frame, text="New Quiz", 
                 command=self.reset_quiz).pack(side=tk.LEFT, padx=10)

    def restart_quiz(self):
        """Restart the quiz with the same settings"""
        self.quiz_frame.pack_forget()
        self.start_quiz()

    def reset_quiz(self):
        """Return to the quiz setup screen"""
        self.quiz_frame.pack_forget()
        self.setup_frame.pack(fill=tk.BOTH, pady=10)

if __name__ == "__main__":
    root = tk.Tk()
    app = QuizApp(root)
    root.mainloop()