import tkinter as tk
from tkinter import ttk, messagebox
import random
import json
import os
import sys
import subprocess

try:
    from PIL import Image, ImageTk
    HAS_PIL = True
except ImportError:
    # Attempt to auto-install Pillow if missing
    try:
        subprocess.check_call([sys.executable, "-m", "pip", "install", "pillow"])
        from PIL import Image, ImageTk
        HAS_PIL = True
    except Exception as e:
        print(f"Warning: Pillow auto-install failed: {e}")
        HAS_PIL = False

# --- Constants & Configuration ---
THEME_COLOR = '#f5f5f5'
FONT_MAIN = ('Arial', 11)
FONT_BOLD = ('Arial', 11, 'bold')
FONT_TITLE = ('Arial', 16, 'bold')

IMG_MAX_WIDTH = 600
IMG_MAX_HEIGHT = 220 

class QuizDataManager:
    def __init__(self):
        self.base_dir = os.path.dirname(os.path.abspath(__file__))
        self.quiz_dir = os.path.join(self.base_dir, "Quizzes")
        if not os.path.exists(self.quiz_dir):
            os.makedirs(self.quiz_dir)

    def get_subjects(self):
        return [d for d in os.listdir(self.quiz_dir) 
                if os.path.isdir(os.path.join(self.quiz_dir, d))]

    def load_questions(self, subject):
        # Look for deduplicated first, then standard
        files = ["questions_deduplicated.json", "questions.json"]
        for fname in files:
            path = os.path.join(self.quiz_dir, subject, fname)
            if os.path.exists(path):
                try:
                    with open(path, 'r') as f:
                        return json.load(f)
                except Exception as e:
                    print(f"Error loading {path}: {e}")
        return []

    def get_image_path(self, subject, image_name):
        if not image_name: return None
        
        # 1. Try direct path
        direct_path = os.path.join(self.quiz_dir, subject, image_name)
        if os.path.exists(direct_path):
            return direct_path
            
        # 2. Try 'Images' subdirectory
        images_sub_path = os.path.join(self.quiz_dir, subject, "Images", image_name)
        if os.path.exists(images_sub_path):
            return images_sub_path
            
        return None

class QuizApp:
    def __init__(self, root):
        self.root = root
        self.data_manager = QuizDataManager()
        
        # State
        self.questions = []
        self.current_idx = 0
        self.score = 0
        self.loaded_questions_cache = []
        
        # Setup
        self._setup_window()
        self._setup_styles()
        self._init_ui()
        self._refresh_subjects()

    def _setup_window(self):
        self.root.title("Clean Quiz App")
        self.root.geometry("1000x800")
        self.root.configure(bg=THEME_COLOR)

    def _setup_styles(self):
        style = ttk.Style()
        style.theme_use('clam')
        style.configure('TFrame', background=THEME_COLOR)
        style.configure('TLabel', background=THEME_COLOR, font=FONT_MAIN)
        style.configure('Title.TLabel', font=FONT_TITLE)
        style.configure('Question.TLabel', font=('Arial', 14, 'bold'), wraplength=800)
        
        # Matching Game Styles
        style.configure('Match.TLabel', background='#e0e0e0', padding=10, relief="raised")
        style.configure('Match.Selected.TLabel', background='#b0d0ff')
        style.configure('Match.Correct.TLabel', background='#90EE90') # Green
        style.configure('Match.Wrong.TLabel', background='#FFCCCB')   # Red

        # Result Frame Styles (Used for MC options)
        style.configure('Result.Correct.TFrame', background='#90EE90')
        style.configure('Result.Wrong.TFrame', background='#FFCCCB')
        style.configure('Result.Neutral.TFrame', background=THEME_COLOR)

    def _init_ui(self):
        # --- Main Container ---
        self.main_container = ttk.Frame(self.root)
        self.main_container.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)

        # --- Setup Screen ---
        self.setup_frame = ttk.Frame(self.main_container)
        
        ttk.Label(self.setup_frame, text="Select Quiz Subject", style='Title.TLabel').pack(pady=20)
        
        # Subject Dropdown
        self.subject_var = tk.StringVar()
        self.subject_cb = ttk.Combobox(self.setup_frame, textvariable=self.subject_var, state="readonly", width=30)
        self.subject_cb.pack(pady=5)
        self.subject_cb.bind("<<ComboboxSelected>>", self._on_subject_change)
        
        # Question Count Selector
        count_frame = ttk.Frame(self.setup_frame)
        count_frame.pack(pady=15)
        ttk.Label(count_frame, text="Questions to answer: ").pack(side=tk.LEFT)
        self.q_count_var = tk.IntVar(value=10)
        self.q_count_spin = ttk.Spinbox(count_frame, from_=1, to=100, textvariable=self.q_count_var, width=5)
        self.q_count_spin.pack(side=tk.LEFT)
        self.lbl_max_q = ttk.Label(count_frame, text="(Max: 0)", font=("Arial", 9))
        self.lbl_max_q.pack(side=tk.LEFT, padx=5)

        # Start Button
        btn_frame = ttk.Frame(self.setup_frame)
        btn_frame.pack(pady=20)
        ttk.Button(btn_frame, text="Start Quiz", command=self.start_quiz).pack(side=tk.LEFT, padx=5)
        
        self.setup_frame.pack(fill=tk.BOTH, expand=True)

        # --- Quiz Screen (Split Layout) ---
        self.quiz_frame = ttk.Frame(self.main_container)
        
        # 1. Top Section: Scrollable Content
        self.content_area = ttk.Frame(self.quiz_frame)
        self.content_area.pack(side=tk.TOP, fill=tk.BOTH, expand=True)
        
        self.canvas = tk.Canvas(self.content_area, bg=THEME_COLOR, highlightthickness=0)
        self.scrollbar = ttk.Scrollbar(self.content_area, orient="vertical", command=self.canvas.yview)
        self.scrollable_frame = ttk.Frame(self.canvas)
        
        self.scrollable_frame.bind(
            "<Configure>",
            lambda e: self.canvas.configure(scrollregion=self.canvas.bbox("all"))
        )
        self.canvas.create_window((0, 0), window=self.scrollable_frame, anchor="nw")
        self.canvas.configure(yscrollcommand=self.scrollbar.set)
        
        self.canvas.pack(side="left", fill="both", expand=True)
        self.scrollbar.pack(side="right", fill="y")
        self.canvas.bind_all("<MouseWheel>", lambda e: self.canvas.yview_scroll(int(-1*(e.delta/120)), "units"))

        # 2. Bottom Section: Fixed Controls
        self.fixed_controls = ttk.Frame(self.quiz_frame)
        self.fixed_controls.pack(side=tk.BOTTOM, fill=tk.X, pady=(10, 0))
        
        ttk.Separator(self.fixed_controls, orient='horizontal').pack(fill='x', pady=5)
        
        self.lbl_feedback = ttk.Label(self.fixed_controls, text="", font=FONT_BOLD)
        self.lbl_feedback.pack(pady=5)
        
        self.btn_action = ttk.Button(self.fixed_controls, text="Submit Answer", command=self.check_answer)
        self.btn_action.pack(pady=10)

    # --- Logic: Setup ---

    def _refresh_subjects(self):
        subjects = self.data_manager.get_subjects()
        self.subject_cb['values'] = subjects
        if subjects: 
            self.subject_cb.current(0)
            self._on_subject_change(None)

    def _on_subject_change(self, event):
        subject = self.subject_var.get()
        if not subject: return
        self.loaded_questions_cache = self.data_manager.load_questions(subject)
        max_q = len(self.loaded_questions_cache)
        
        self.lbl_max_q.config(text=f"(Max: {max_q})")
        self.q_count_spin.config(to=max_q)
        self.q_count_var.set(min(10, max_q) if max_q > 0 else 0)

    def start_quiz(self):
        subject = self.subject_var.get()
        if not subject or not self.loaded_questions_cache: return
        
        requested_count = self.q_count_var.get()
        max_available = len(self.loaded_questions_cache)
        count = min(requested_count, max_available)

        self.questions = random.sample(self.loaded_questions_cache, count)
        self.current_subject = subject
        self.current_idx = 0
        self.score = 0
        
        self.setup_frame.pack_forget()
        self.quiz_frame.pack(fill=tk.BOTH, expand=True)
        
        # BUG FIX: Ensure fixed controls are visible when restarting
        self.fixed_controls.pack(side=tk.BOTTOM, fill=tk.X, pady=(10, 0))
        
        self.load_current_question()

    # --- Logic: Rendering Questions ---

    def _clear_quiz_area(self):
        for widget in self.scrollable_frame.winfo_children():
            widget.destroy()
        # Reset Controls
        self.lbl_feedback.config(text="", foreground="black")
        self.btn_action.config(text="Submit Answer", command=self.check_answer, state="normal")

    def load_current_question(self):
        self._clear_quiz_area()
        self.canvas.yview_moveto(0)

        if self.current_idx >= len(self.questions):
            self.show_results()
            return

        q_data = self.questions[self.current_idx]
        
        # 1. Header
        header_text = f"Question {self.current_idx + 1} of {len(self.questions)}"
        ttk.Label(self.scrollable_frame, text=header_text, foreground="gray").pack(anchor="w", pady=(0,5))
        
        # 2. Question Text
        ttk.Label(self.scrollable_frame, text=q_data['question'], style='Question.TLabel').pack(anchor="w", fill=tk.X, pady=10)

        # 3. Image (Scaled)
        if q_data.get('image'):
            self._render_image(q_data['image'])

        # 4. Options
        q_type = q_data.get('type', 'multiple_choice')
        if q_type == 'matching':
            self._render_matching(q_data)
        else:
            self._render_multichoice(q_data)

    def _render_image(self, image_name):
        img_path = self.data_manager.get_image_path(self.current_subject, image_name)
        
        if not img_path or not os.path.exists(img_path):
            ttk.Label(self.scrollable_frame, text=f"[Image '{image_name}' not found]", foreground="red").pack()
            return

        if HAS_PIL:
            try:
                pil_img = Image.open(img_path)
                w, h = pil_img.size
                ratio_w = IMG_MAX_WIDTH / w
                ratio_h = IMG_MAX_HEIGHT / h
                ratio = min(ratio_w, ratio_h)
                new_w = int(w * ratio)
                new_h = int(h * ratio)
                
                # Compatibility for older Pillow versions
                resample_mode = Image.Resampling.LANCZOS if hasattr(Image, 'Resampling') else Image.LANCZOS
                
                pil_img = pil_img.resize((new_w, new_h), resample_mode)
                photo = ImageTk.PhotoImage(pil_img)
                lbl = ttk.Label(self.scrollable_frame, image=photo)
                lbl.image = photo 
                lbl.pack(pady=10)
            except Exception as e:
                ttk.Label(self.scrollable_frame, text=f"[Error loading image: {e}]", foreground="red").pack()
        else:
            # Fallback: Native Tkinter (supports PNG/GIF, no JPEG)
            try:
                photo = tk.PhotoImage(file=img_path)
                
                # Basic integer downscaling (subsample)
                w, h = photo.width(), photo.height()
                scale_w = int(w / IMG_MAX_WIDTH) + 1
                scale_h = int(h / IMG_MAX_HEIGHT) + 1
                scale = max(scale_w, scale_h)
                
                if scale > 1:
                    photo = photo.subsample(scale)
                
                lbl = ttk.Label(self.scrollable_frame, image=photo)
                lbl.image = photo
                lbl.pack(pady=10)
            except tk.TclError:
                # Fallback 2: Check if a PNG version exists (e.g. image.jpg -> image.png)
                png_path = os.path.splitext(img_path)[0] + ".png"
                if os.path.exists(png_path):
                    try:
                        photo = tk.PhotoImage(file=png_path)
                        w, h = photo.width(), photo.height()
                        scale_w = int(w / IMG_MAX_WIDTH) + 1
                        scale_h = int(h / IMG_MAX_HEIGHT) + 1
                        scale = max(scale_w, scale_h)
                        if scale > 1:
                            photo = photo.subsample(scale)
                        lbl = ttk.Label(self.scrollable_frame, image=photo)
                        lbl.image = photo
                        lbl.pack(pady=10)
                        return
                    except Exception:
                        pass
                
                ttk.Label(self.scrollable_frame, text="[Format unsupported. Convert image to PNG]", foreground="red").pack()
            except Exception as e:
                ttk.Label(self.scrollable_frame, text=f"[Error: {e}]", foreground="red").pack()

    def _render_multichoice(self, q_data):
        self.mc_vars = []
        self.mc_widgets = [] 
        self.mc_frames = [] # Store frames to color them later
        options = q_data['options']
        
        indexed_options = list(enumerate(options))
        random.shuffle(indexed_options)
        
        self.mc_mapping = {ui_idx: orig_idx for ui_idx, (orig_idx, _) in enumerate(indexed_options)}
        
        for ui_idx, (_, text) in enumerate(indexed_options):
            # Create a frame for the option to handle background coloring reliability
            frame = ttk.Frame(self.scrollable_frame, padding=5)
            frame.pack(anchor="w", pady=2, padx=20, fill=tk.X)
            self.mc_frames.append(frame)

            var = tk.IntVar()
            chk = ttk.Checkbutton(frame, text=text, variable=var)
            chk.pack(side=tk.LEFT, fill=tk.X)
            
            # Label for feedback icon (checkmark/cross)
            lbl = ttk.Label(frame, text="", font=("Arial", 12, "bold"))
            lbl.pack(side=tk.RIGHT)
            
            self.mc_vars.append(var)
            self.mc_widgets.append((chk, lbl))

    def _render_matching(self, q_data):
        self.match_state = {'left_selected': None, 'right_selected': None, 'pairs': {}}
        
        container = ttk.Frame(self.scrollable_frame)
        container.pack(fill=tk.X, pady=10)
        
        left_col = ttk.Frame(container)
        left_col.pack(side=tk.LEFT, expand=True, fill=tk.BOTH, padx=10)
        
        self.match_right_col = ttk.Frame(container)
        self.match_right_col.pack(side=tk.RIGHT, expand=True, fill=tk.BOTH, padx=10)
        
        self.match_left_widgets = []
        for item in q_data['left_items']:
            lbl = ttk.Label(left_col, text=item, style='Match.TLabel', cursor="hand2")
            lbl.pack(fill=tk.X, pady=5)
            lbl.bind("<Button-1>", lambda e, w=lbl: self._on_match_click(w, 'left'))
            self.match_left_widgets.append(lbl)
            
        right_items = list(q_data['right_items'])
        random.shuffle(right_items)
        
        self.match_right_widgets = []
        for item in right_items:
            lbl = ttk.Label(self.match_right_col, text=item, style='Match.TLabel', cursor="hand2")
            lbl.pack(fill=tk.X, pady=5)
            lbl.bind("<Button-1>", lambda e, w=lbl: self._on_match_click(w, 'right'))
            self.match_right_widgets.append(lbl)

        ttk.Label(self.scrollable_frame, text="* Click an item on the left, then an item on the right to match.", font=("Arial", 9, "italic")).pack(pady=5)

    def _on_match_click(self, widget, side):
        target = 'left_selected' if side == 'left' else 'right_selected'
        old_widget = self.match_state[target]
        if old_widget: old_widget.configure(style='Match.TLabel')
        
        self.match_state[target] = widget
        widget.configure(style='Match.Selected.TLabel')
        
        if self.match_state['left_selected'] and self.match_state['right_selected']:
            l_txt = self.match_state['left_selected']['text']
            r_txt = self.match_state['right_selected']['text']
            self.match_state['pairs'][l_txt] = r_txt
            
            self.match_state['left_selected'].configure(style='Match.Selected.TLabel')
            self.match_state['right_selected'].configure(style='Match.Selected.TLabel')
            self.match_state['left_selected'] = None
            self.match_state['right_selected'] = None

    # --- Validation ---

    def check_answer(self):
        q_data = self.questions[self.current_idx]
        q_type = q_data.get('type', 'multiple_choice')
        is_correct = False
        
        if q_type == 'matching':
            is_correct = self._validate_matching(q_data)
        else:
            is_correct = self._validate_multichoice(q_data)
            
        if is_correct:
            self.score += 1
            self.lbl_feedback.config(text="Correct!", foreground="green")
        else:
            self.lbl_feedback.config(text="Incorrect. See details above.", foreground="red")
            
        self.btn_action.config(text="Next Question", command=self.next_question)

    def _validate_multichoice(self, q_data):
        selected_orig_indices = [self.mc_mapping[i] for i, var in enumerate(self.mc_vars) if var.get() == 1]
        correct = q_data['correct']
        if isinstance(correct, int): correct = [correct]
        
        is_correct = set(selected_orig_indices) == set(correct)
        
        # --- BUG FIX IS HERE ---
        # Old: for i, (orig_idx, _) in enumerate(sorted(self.mc_mapping.items())):
        # New: We unpack (ui_index, original_index)
        for i, (ui_idx, orig_idx) in enumerate(sorted(self.mc_mapping.items())):
            chk, lbl = self.mc_widgets[i]
            frame = self.mc_frames[i]
            chk.config(state="disabled")
            
            # Now 'orig_idx' actually refers to the JSON index, not the screen position
            if orig_idx in correct:
                # It was a correct answer
                frame.configure(style='Result.Correct.TFrame')
                lbl.config(text="✓", foreground="green")
            elif i in [k for k,v in enumerate(self.mc_vars) if v.get() == 1]:
                # User selected it but it was WRONG
                frame.configure(style='Result.Wrong.TFrame')
                lbl.config(text="✗", foreground="red")
            else:
                # Neutral (not correct, not selected)
                frame.configure(style='Result.Neutral.TFrame')
                lbl.config(text="")
                
        return is_correct

    def _validate_matching(self, q_data):
        user_pairs = self.match_state['pairs']
        correct_indices = q_data['correct_matches']
        left_items = q_data['left_items']
        right_items = q_data['right_items']
        
        correct_count = 0
        self.match_right_col.pack_forget()
        
        for l_idx, r_idx in correct_indices:
            l_text = left_items[l_idx]
            correct_r_text = right_items[r_idx]
            user_r_text = user_pairs.get(l_text)
            
            l_widget = next((w for w in self.match_left_widgets if w['text'] == l_text), None)
            
            if l_widget:
                new_text = f"{l_text}\n   ➔ {correct_r_text}"
                l_widget.config(text=new_text)
                
                if user_r_text == correct_r_text:
                    correct_count += 1
                    l_widget.configure(style='Match.Correct.TLabel')
                else:
                    l_widget.configure(style='Match.Wrong.TLabel')

        for w in self.match_left_widgets:
            w.unbind("<Button-1>")

        return correct_count == len(correct_indices)

    def next_question(self):
        self.current_idx += 1
        self.load_current_question()

    def show_results(self):
        self.fixed_controls.pack_forget()
        self._clear_quiz_area()
        
        pct = (self.score / len(self.questions)) * 100
        ttk.Label(self.scrollable_frame, text="Quiz Complete!", style='Title.TLabel').pack(pady=20)
        ttk.Label(self.scrollable_frame, text=f"Score: {self.score}/{len(self.questions)} ({pct:.1f}%)", font=('Arial', 14)).pack(pady=10)
        ttk.Button(self.scrollable_frame, text="Back to Menu", command=self._return_to_menu).pack(pady=20)

    def _return_to_menu(self):
        self.quiz_frame.pack_forget()
        self.setup_frame.pack(fill=tk.BOTH, expand=True)

if __name__ == "__main__":
    root = tk.Tk()
    app = QuizApp(root)
    root.mainloop()