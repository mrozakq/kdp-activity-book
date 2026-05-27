"""
Series presets for "Little Vibe Coders" — 5-volume KDP activity book series
for kids 5-7. Each preset bundles:
  - book metadata (title, subtitle, author, age, description, keywords)
  - activity mix (counts per type)
  - difficulty per type
  - wordsearch theme
  - chapter intros (rendered in Etap 2; stored here now for content readiness)

Used by:
  - blueprints/kdp/activity.py — to pre-fill form fields when user picks preset
  - templates/activity.html — dropdown shows preset names, JS calls API for config
"""

SERIES_NAME = 'Little Vibe Coders'
SERIES_AUTHOR = 'Mr Felix Mrozak'
SERIES_AGE = '5-7'

PRESETS = {
    'vibe_v1_first_steps': {
        'volume': 1,
        'title': 'Little Vibe Coders',
        'subtitle': 'Your First Logic Puzzles — Think Before You Prompt (Ages 5-6)',
        'series_name': SERIES_NAME,
        'author': SERIES_AUTHOR,
        'age_range': SERIES_AGE,
        'description': (
            "Your child is going to grow up talking to computers — not typing "
            "in code, but describing what they want. This first workbook builds "
            "the one skill that matters: precision. 40 hand-crafted puzzles that "
            "teach kids 5-6 to follow a path, spot a pattern, and notice what's "
            "there. No screens, no apps, just a pencil and 60 minutes of focused "
            "thinking."
        ),
        'keywords': [
            'logic puzzles for kids 5-6',
            'pre-coding workbook',
            'kindergarten activity book',
            'AI for kids',
            'STEM puzzles age 5',
            'preschool logic workbook',
            'thinking skills for children',
        ],
        'mix': {
            'n_mazes': 10, 'n_pattern': 8, 'n_symmetry': 6, 'n_counting': 8,
            'n_dotgrid': 4, 'n_wordsearch': 4,
            'n_sudoku': 0, 'n_magic': 0, 'n_pathsum': 0, 'n_mathmaze': 0,
        },
        'difficulty': {
            'difficulty': 'easy',
            'sudoku_difficulty': 'easy',
            'sudoku_size': '4x4',
            'magic_difficulty': 'easy',
            'dotgrid_difficulty': 'easy',
            'counting_difficulty': 'easy',
            'pattern_difficulty': 'easy',
            'symmetry_difficulty': 'easy',
            'pathsum_difficulty': 'easy',
            'mathmaze_difficulty': 'easy',
            'wordsearch_difficulty': 'easy',
        },
        'wordsearch_theme': 'ai_kids_basics_en',
        'chapter_intros': {
            'maze':       "A prompt is like a map. The clearer the path, "
                          "the better the answer.",
            'pattern':    "Computers love things that repeat. Find what "
                          "comes next.",
            'symmetry':   "A function takes something in and gives something "
                          "back. Mirror takes a half-picture and gives a "
                          "whole one.",
            'counting':   "Before a computer can do anything, it has to count. "
                          "How many do you see?",
            'dotgrid':    "Read the words. Then draw what they say. That's "
                          "what a prompt does.",
            'wordsearch': "Every great answer starts with the right word. "
                          "Find them all.",
        },
    },

    'vibe_v2_prompting_power': {
        'volume': 2,
        'title': 'Little Vibe Coders',
        'subtitle': 'Logic Puzzles That Teach Kids How to Ask the Right Questions (Ages 5-7)',
        'series_name': SERIES_NAME,
        'author': SERIES_AUTHOR,
        'age_range': SERIES_AGE,
        'description': (
            "To get a great answer from an AI, you need to ask a great question. "
            "This is Volume 2 of Little Vibe Coders — a workbook that teaches "
            "kids 5-7 the muscle of clear thinking. Through 48 puzzles, your "
            "child learns to give directions, find keywords, and describe what "
            "they see. Building blocks for a generation that will direct "
            "computers, not just use them."
        ),
        'keywords': [
            'AI workbook for kids',
            'prompting skills for children',
            'logic puzzles age 5 7',
            'kindergarten coding book',
            'pre-AI literacy kids',
            'thinking puzzles for early readers',
            'STEM workbook K-1',
        ],
        'mix': {
            'n_mazes': 12, 'n_wordsearch': 8, 'n_dotgrid': 8, 'n_counting': 6,
            'n_pattern': 8, 'n_symmetry': 6,
            'n_sudoku': 0, 'n_magic': 0, 'n_pathsum': 0, 'n_mathmaze': 0,
        },
        'difficulty': {
            'difficulty': 'medium',
            'sudoku_difficulty': 'easy',
            'sudoku_size': '4x4',
            'magic_difficulty': 'easy',
            'dotgrid_difficulty': 'medium',
            'counting_difficulty': 'medium',
            'pattern_difficulty': 'medium',
            'symmetry_difficulty': 'medium',
            'pathsum_difficulty': 'easy',
            'mathmaze_difficulty': 'easy',
            'wordsearch_difficulty': 'medium',
        },
        'wordsearch_theme': 'ai_kids_prompting_en',
        'chapter_intros': {
            'maze':       "A clear prompt is a clear path. No detours. "
                          "Get to the goal.",
            'wordsearch': "When you talk to a computer, the right words "
                          "matter. Find them.",
            'dotgrid':    "Someone writes what they want. You draw it. "
                          "That's a prompt working.",
            'counting':   "Numbers are how computers count things. Practice "
                          "counting like a machine.",
            'pattern':    "Spot the rule. Predict what's next. Computers do "
                          "this billions of times a second.",
            'symmetry':   "A function flips. A function repeats. A function "
                          "transforms. Try one.",
        },
    },

    'vibe_v3_loops_and_logic': {
        'volume': 3,
        'title': 'Little Vibe Coders',
        'subtitle': 'If/Then Puzzles for Kids Who Will Build with AI (Ages 6-7)',
        'series_name': SERIES_NAME,
        'author': SERIES_AUTHOR,
        'age_range': SERIES_AGE,
        'description': (
            "If this, then that. The most important sentence in computing. "
            "This Volume 3 of Little Vibe Coders teaches kids 6-7 to think "
            "in rules: repeat what works, decide when to stop, follow the "
            "right path. 52 puzzles that quietly install the mental habits "
            "of every programmer and every great AI user."
        ),
        'keywords': [
            'if then puzzles for kids',
            'logic workbook age 6 7',
            'coding logic for children',
            'pattern puzzles K-1',
            'pre-coding workbook',
            'first grade STEM book',
            'AI thinking for kids',
        ],
        'mix': {
            'n_pattern': 10, 'n_mathmaze': 10, 'n_pathsum': 8, 'n_mazes': 6,
            'n_symmetry': 6, 'n_counting': 6, 'n_wordsearch': 6,
            'n_sudoku': 0, 'n_magic': 0, 'n_dotgrid': 0,
        },
        'difficulty': {
            'difficulty': 'medium',
            'sudoku_difficulty': 'medium',
            'sudoku_size': '4x4',
            'magic_difficulty': 'medium',
            'dotgrid_difficulty': 'medium',
            'counting_difficulty': 'medium',
            'pattern_difficulty': 'medium',
            'symmetry_difficulty': 'medium',
            'pathsum_difficulty': 'medium',
            'mathmaze_difficulty': 'medium',
            'wordsearch_difficulty': 'medium',
        },
        'wordsearch_theme': 'ai_kids_loops_en',
        'chapter_intros': {
            'pattern':    "Loop: a thing that repeats. Find it. Continue it. "
                          "Now you're thinking like code.",
            'mathmaze':   "If the number is even, go left. If odd, go right. "
                          "That's how computers choose.",
            'pathsum':    "Keep adding as you go. The total is your answer. "
                          "Programmers call this an accumulator.",
            'maze':       "Same path, but harder. Stay precise.",
            'symmetry':   "A mirror is a function: input on one side, output "
                          "on the other. Find the rule.",
            'counting':   "Tokens are how AI counts language. Counting things "
                          "is the first step.",
            'wordsearch': "Find the words a programmer uses every day.",
        },
    },

    'vibe_v4_solving_constraints': {
        'volume': 4,
        'title': 'Little Vibe Coders',
        'subtitle': 'Puzzles for Kids Who Love Hard Rules (Ages 6-7)',
        'series_name': SERIES_NAME,
        'author': SERIES_AUTHOR,
        'age_range': SERIES_AGE,
        'description': (
            "Real problems have rules that all have to be true at once. "
            "A row has to add up. A column has to fit. A grid has to balance. "
            "Volume 4 of Little Vibe Coders teaches kids 6-7 the hardest "
            "skill in problem-solving: holding many rules in your head and "
            "finding the answer that satisfies them all. 60 puzzles, no "
            "shortcuts."
        ),
        'keywords': [
            'sudoku for kids 4x4',
            'logic puzzles age 7',
            'constraint puzzles for children',
            'math workbook first grade',
            'STEM puzzles K-2',
            'critical thinking for kids',
            'AI puzzles workbook',
        ],
        'mix': {
            'n_sudoku': 12, 'n_magic': 8, 'n_pathsum': 8, 'n_mathmaze': 8,
            'n_symmetry': 6, 'n_pattern': 6, 'n_wordsearch': 6, 'n_mazes': 6,
            'n_counting': 0, 'n_dotgrid': 0,
        },
        'difficulty': {
            'difficulty': 'hard',
            'sudoku_difficulty': 'hard',
            'sudoku_size': '4x4',
            'magic_difficulty': 'medium',
            'dotgrid_difficulty': 'hard',
            'counting_difficulty': 'hard',
            'pattern_difficulty': 'hard',
            'symmetry_difficulty': 'hard',
            'pathsum_difficulty': 'hard',
            'mathmaze_difficulty': 'hard',
            'wordsearch_difficulty': 'hard',
        },
        'wordsearch_theme': 'ai_kids_constraints_en',
        'chapter_intros': {
            'sudoku':     "Every row, every column, every box — all the rules "
                          "must be true. That's a constraint.",
            'magic':      "Every row sums to the same number. Every column too. "
                          "Balance the grid.",
            'pathsum':    "Add as you go. But the total must match. Keep "
                          "checking.",
            'mathmaze':   "Choose, but choose right. The rule decides.",
            'symmetry':   "The rule of symmetry: what's true on one side must "
                          "be true on the other.",
            'pattern':    "Hard patterns hide deeper rules. Find them.",
            'wordsearch': "Words about rules. Find them all.",
            'maze':       "One path is correct. The rest are traps.",
        },
    },

    'vibe_v5_ai_director': {
        'volume': 5,
        'title': 'Little Vibe Coders',
        'subtitle': 'The Complete Logic Workout for Future AI Directors (Ages 6-7)',
        'series_name': SERIES_NAME,
        'author': SERIES_AUTHOR,
        'age_range': SERIES_AGE,
        'description': (
            "The capstone of Little Vibe Coders. 68 puzzles across all ten "
            "thinking patterns your child will use when they grow up to direct "
            "AI: prompting, looping, deciding, accumulating, balancing, "
            "constraining. Volume 5 is the complete logic workout for kids "
            "6-7 — and the proof that they're ready. By the end, they won't "
            "be afraid of any problem a computer can pose."
        ),
        'keywords': [
            'logic puzzles for kids 7',
            'AI workbook for children',
            'STEM activity book grade 1',
            'thinking puzzles K-2',
            'coding logic for kids',
            'pre-programming workbook',
            'sudoku and mazes for children',
        ],
        'mix': {
            'n_mazes': 10, 'n_pattern': 8, 'n_symmetry': 6, 'n_mathmaze': 8,
            'n_pathsum': 8, 'n_sudoku': 8, 'n_magic': 6, 'n_counting': 6,
            'n_wordsearch': 4, 'n_dotgrid': 4,
        },
        'difficulty': {
            'difficulty': 'hard',
            'sudoku_difficulty': 'hard',
            'sudoku_size': '4x4',
            'magic_difficulty': 'hard',
            'dotgrid_difficulty': 'hard',
            'counting_difficulty': 'hard',
            'pattern_difficulty': 'hard',
            'symmetry_difficulty': 'hard',
            'pathsum_difficulty': 'hard',
            'mathmaze_difficulty': 'hard',
            'wordsearch_difficulty': 'hard',
        },
        'wordsearch_theme': 'ai_kids_director_en',
        'chapter_intros': {
            'maze':       "You're directing now. Pick the path. Commit.",
            'pattern':    "Patterns of patterns. The world of programming "
                          "in one puzzle.",
            'symmetry':   "Compose functions. Mirror, rotate, reflect. "
                          "You're building.",
            'mathmaze':   "A decision tree with consequences. Choose well.",
            'pathsum':    "Accumulate, check, accumulate, check. That's an "
                          "algorithm.",
            'sudoku':     "The classic constraint puzzle. Programmers love it.",
            'magic':      "Balance four ways at once. AI does this with "
                          "millions of variables.",
            'counting':   "Tokens, items, steps. Counting is everywhere.",
            'wordsearch': "All the words you've learned. Find them. You're "
                          "ready.",
            'dotgrid':    "Draw what you've imagined. The output is yours.",
        },
    },
}


def list_preset_keys():
    """Stable, ordered list of preset keys for UI dropdowns."""
    return [
        'vibe_v1_first_steps',
        'vibe_v2_prompting_power',
        'vibe_v3_loops_and_logic',
        'vibe_v4_solving_constraints',
        'vibe_v5_ai_director',
    ]


def get_preset(key):
    """Return preset dict or None."""
    return PRESETS.get(key)


def preset_display_name(key):
    """Human-friendly label for a preset (dropdown)."""
    p = PRESETS.get(key)
    if not p:
        return key
    return f"Vol.{p['volume']}: {p['subtitle'].split('—')[0].strip()}"
