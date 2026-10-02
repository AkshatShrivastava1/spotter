"""Exercise library with form cues. This is the 'trainer standing next to you' content.

equipment: gym | dumbbell | bodyweight  (gym implies dumbbells + bodyweight are available too)
"""

EXERCISES: dict[str, dict] = {
    "barbell_back_squat": {
        "name": "Barbell Back Squat", "equipment": "gym", "pattern": "squat",
        "muscles": ["quads", "glutes", "adductors", "core"],
        "cues": ["Bar on upper traps, grip just outside shoulders", "Brace: big breath into belly, ribs down",
                 "Knees track over toes, push them out", "Sit between your hips, hit at least parallel",
                 "Drive the floor away, chest and hips rise together"],
        "mistakes": ["Knees caving in", "Heels lifting", "Good-morning-ing the weight up (hips shoot first)"],
        "rep_range": [5, 8],
    },
    "goblet_squat": {
        "name": "Goblet Squat", "equipment": "dumbbell", "pattern": "squat",
        "muscles": ["quads", "glutes", "core"],
        "cues": ["Hold dumbbell at chest, elbows under it", "Sit straight down between your heels",
                 "Elbows brush the inside of knees at the bottom", "Stay tall, chest up"],
        "mistakes": ["Leaning forward", "Half reps"], "rep_range": [8, 12],
    },
    "bodyweight_squat": {
        "name": "Bodyweight Squat", "equipment": "bodyweight", "pattern": "squat",
        "muscles": ["quads", "glutes"],
        "cues": ["Arms forward for balance", "Hips back and down", "Full foot pressure", "Control the descent (2-3 s)"],
        "mistakes": ["Rushing reps", "Knees caving"], "rep_range": [15, 25],
    },
    "romanian_deadlift": {
        "name": "Romanian Deadlift", "equipment": "gym", "pattern": "hinge",
        "muscles": ["hamstrings", "glutes", "lower back"],
        "cues": ["Soft knees, then push hips straight back", "Bar drags down your thighs",
                 "Stop when hamstrings are stretched, usually mid-shin", "Squeeze glutes to stand, don't lean back"],
        "mistakes": ["Rounding the lower back", "Turning it into a squat"], "rep_range": [6, 10],
    },
    "dumbbell_rdl": {
        "name": "Dumbbell Romanian Deadlift", "equipment": "dumbbell", "pattern": "hinge",
        "muscles": ["hamstrings", "glutes"],
        "cues": ["Dumbbells close to legs", "Hips back, flat back", "Feel the stretch, then drive hips forward"],
        "mistakes": ["Dumbbells drifting forward", "Rounded back"], "rep_range": [8, 12],
    },
    "deadlift": {
        "name": "Conventional Deadlift", "equipment": "gym", "pattern": "hinge",
        "muscles": ["glutes", "hamstrings", "back", "traps"],
        "cues": ["Bar over mid-foot", "Grip, then pull slack out of the bar", "Chest up, lats tight ('protect your armpits')",
                 "Push the floor away, lock out with glutes"],
        "mistakes": ["Jerking the bar off the floor", "Hips too low (squatting it)", "Hyperextending at lockout"],
        "rep_range": [3, 6],
    },
    "glute_bridge": {
        "name": "Glute Bridge", "equipment": "bodyweight", "pattern": "hinge",
        "muscles": ["glutes", "hamstrings"],
        "cues": ["Feet flat, close to glutes", "Tuck pelvis slightly", "Drive through heels, squeeze 1 s at top"],
        "mistakes": ["Arching lower back instead of using glutes"], "rep_range": [12, 20],
    },
    "bench_press": {
        "name": "Barbell Bench Press", "equipment": "gym", "pattern": "horizontal_push",
        "muscles": ["chest", "front delts", "triceps"],
        "cues": ["Shoulder blades pinched back and down", "Feet planted, slight arch", "Lower to lower chest, elbows ~45°",
                 "Press up and slightly back toward your face"],
        "mistakes": ["Flared elbows (90°)", "Bouncing off the chest", "Butt lifting off the bench"],
        "rep_range": [5, 8],
    },
    "dumbbell_bench_press": {
        "name": "Dumbbell Bench Press", "equipment": "dumbbell", "pattern": "horizontal_push",
        "muscles": ["chest", "front delts", "triceps"],
        "cues": ["Kick dumbbells up with your knees", "Shoulder blades back", "Lower until a deep chest stretch", "Press together without clanging"],
        "mistakes": ["Elbows flared", "Losing tension at the top"], "rep_range": [8, 12],
    },
    "push_up": {
        "name": "Push-up", "equipment": "bodyweight", "pattern": "horizontal_push",
        "muscles": ["chest", "triceps", "front delts", "core"],
        "cues": ["Hands under shoulders", "Body is one straight plank, glutes squeezed", "Chest to floor, elbows ~45°", "Push the floor away"],
        "mistakes": ["Sagging hips", "Half reps", "Head poking forward"], "rep_range": [8, 20],
    },
    "overhead_press": {
        "name": "Overhead Press", "equipment": "gym", "pattern": "vertical_push",
        "muscles": ["shoulders", "triceps", "upper chest"],
        "cues": ["Squeeze glutes and brace", "Bar starts on front delts", "Move head back, press straight up, head through at the top"],
        "mistakes": ["Leaning back excessively", "Pressing the bar forward"], "rep_range": [5, 8],
    },
    "dumbbell_shoulder_press": {
        "name": "Dumbbell Shoulder Press", "equipment": "dumbbell", "pattern": "vertical_push",
        "muscles": ["shoulders", "triceps"],
        "cues": ["Seated or standing tall", "Start at ear level, palms forward or neutral", "Press up, don't clang at the top"],
        "mistakes": ["Arching the lower back"], "rep_range": [8, 12],
    },
    "pike_push_up": {
        "name": "Pike Push-up", "equipment": "bodyweight", "pattern": "vertical_push",
        "muscles": ["shoulders", "triceps"],
        "cues": ["Hips high, inverted V", "Lower head toward a spot in front of hands", "Press back up through shoulders"],
        "mistakes": ["Turning it into a normal push-up"], "rep_range": [6, 12],
    },
    "pull_up": {
        "name": "Pull-up", "equipment": "gym", "pattern": "vertical_pull",
        "muscles": ["lats", "biceps", "upper back"],
        "cues": ["Start from a dead hang", "Pull elbows down to your ribs", "Chest toward the bar", "Control the way down"],
        "mistakes": ["Kipping", "Half reps"], "rep_range": [4, 10],
    },
    "lat_pulldown": {
        "name": "Lat Pulldown", "equipment": "gym", "pattern": "vertical_pull",
        "muscles": ["lats", "biceps"],
        "cues": ["Thighs locked under pad", "Slight lean back", "Pull bar to upper chest, elbows down and back"],
        "mistakes": ["Pulling behind the neck", "Leaning way back to swing"], "rep_range": [8, 12],
    },
    "barbell_row": {
        "name": "Barbell Row", "equipment": "gym", "pattern": "horizontal_pull",
        "muscles": ["upper back", "lats", "biceps"],
        "cues": ["Hinge to ~45°, flat back", "Pull bar to lower ribs", "Squeeze shoulder blades together"],
        "mistakes": ["Standing up as you row", "Jerking the weight"], "rep_range": [6, 10],
    },
    "dumbbell_row": {
        "name": "One-arm Dumbbell Row", "equipment": "dumbbell", "pattern": "horizontal_pull",
        "muscles": ["lats", "upper back", "biceps"],
        "cues": ["Hand and knee on bench, flat back", "Pull dumbbell to your hip, not your chest", "Pause at the top"],
        "mistakes": ["Rotating the torso to lift"], "rep_range": [8, 12],
    },
    "inverted_row": {
        "name": "Inverted Row (table or bar)", "equipment": "bodyweight", "pattern": "horizontal_pull",
        "muscles": ["upper back", "lats", "biceps"],
        "cues": ["Body straight like a plank", "Pull chest to the bar/table edge", "Squeeze shoulder blades"],
        "mistakes": ["Hips sagging"], "rep_range": [6, 15],
    },
    "walking_lunge": {
        "name": "Walking Lunge", "equipment": "bodyweight", "pattern": "lunge",
        "muscles": ["quads", "glutes"],
        "cues": ["Long step, back knee kisses the floor", "Front shin roughly vertical", "Push through front heel"],
        "mistakes": ["Front knee caving in", "Short choppy steps"], "rep_range": [10, 16],
    },
    "bulgarian_split_squat": {
        "name": "Bulgarian Split Squat", "equipment": "dumbbell", "pattern": "lunge",
        "muscles": ["quads", "glutes"],
        "cues": ["Rear foot laces on bench", "Drop straight down", "Slight forward lean for more glute"],
        "mistakes": ["Front foot too close to bench"], "rep_range": [8, 12],
    },
    "leg_press": {
        "name": "Leg Press", "equipment": "gym", "pattern": "squat",
        "muscles": ["quads", "glutes"],
        "cues": ["Feet shoulder width mid-platform", "Lower until knees ~90°, lower back stays on pad", "Don't lock knees hard at top"],
        "mistakes": ["Butt peeling off the pad", "Locking out knees"], "rep_range": [10, 15],
    },
    "bicep_curl": {
        "name": "Dumbbell Bicep Curl", "equipment": "dumbbell", "pattern": "isolation",
        "muscles": ["biceps"],
        "cues": ["Elbows pinned to sides", "Curl and squeeze", "Lower slowly (2-3 s)"],
        "mistakes": ["Swinging the torso"], "rep_range": [10, 15],
    },
    "tricep_pushdown": {
        "name": "Cable Tricep Pushdown", "equipment": "gym", "pattern": "isolation",
        "muscles": ["triceps"],
        "cues": ["Elbows glued to sides", "Push down to full lockout", "Control up"],
        "mistakes": ["Elbows flaring forward"], "rep_range": [10, 15],
    },
    "lateral_raise": {
        "name": "Dumbbell Lateral Raise", "equipment": "dumbbell", "pattern": "isolation",
        "muscles": ["side delts"],
        "cues": ["Slight bend in elbows", "Lead with elbows, raise to shoulder height", "Pinkies not higher than thumbs"],
        "mistakes": ["Shrugging", "Swinging heavy weight"], "rep_range": [12, 20],
    },
    "plank": {
        "name": "Plank", "equipment": "bodyweight", "pattern": "core",
        "muscles": ["core"],
        "cues": ["Elbows under shoulders", "Squeeze glutes, tuck ribs", "Straight line head to heels"],
        "mistakes": ["Hips sagging or piking"], "rep_range": [30, 60],  # seconds
    },
    "hanging_knee_raise": {
        "name": "Hanging Knee Raise", "equipment": "gym", "pattern": "core",
        "muscles": ["abs", "hip flexors"],
        "cues": ["Dead hang, no swing", "Curl pelvis up, not just knees", "Lower slowly"],
        "mistakes": ["Swinging"], "rep_range": [8, 15],
    },
    # ---- older adults: strength + balance for independence ----
    "sit_to_stand": {
        "name": "Sit-to-Stand (chair)", "equipment": "bodyweight", "pattern": "squat",
        "muscles": ["quads", "glutes"],
        "cues": ["Sit near the front of a sturdy chair", "Feet flat, hip-width", "Lean forward, 'nose over toes', and stand up tall",
                 "Sit back down slowly; use hands only if needed"],
        "mistakes": ["Dropping into the chair", "Knees collapsing inward"], "rep_range": [8, 15],
    },
    "wall_push_up": {
        "name": "Wall Push-up", "equipment": "bodyweight", "pattern": "horizontal_push",
        "muscles": ["chest", "triceps", "shoulders"],
        "cues": ["Hands on the wall at shoulder height", "Step back so you lean in a straight line", "Bend elbows, chest to wall, push back"],
        "mistakes": ["Hips sagging", "Elbows flaring straight out"], "rep_range": [10, 15],
    },
    "single_leg_balance": {
        "name": "Single-Leg Balance", "equipment": "bodyweight", "pattern": "balance",
        "muscles": ["ankles", "hips", "core"],
        "cues": ["Stand next to a counter or chair for support", "Lift one foot a few inches", "Hold steady, eyes forward; switch sides"],
        "mistakes": ["Doing it with nothing nearby to hold"], "rep_range": [20, 30],  # seconds per side
    },
    "step_up": {
        "name": "Step-up", "equipment": "bodyweight", "pattern": "lunge",
        "muscles": ["quads", "glutes", "balance"],
        "cues": ["Use a low, stable step and a rail if available", "Whole foot on the step", "Push through the heel to stand tall, step down slowly"],
        "mistakes": ["Pushing off the back foot", "Step too high"], "rep_range": [8, 12],
    },
    # ---- kids: movement as play ----
    "bear_crawl": {
        "name": "Bear Crawl", "equipment": "bodyweight", "pattern": "play",
        "muscles": ["shoulders", "core", "legs"],
        "cues": ["Hands and feet on the floor, knees just off the ground", "Crawl forward like a bear", "Keep your back flat like a table"],
        "mistakes": ["Hips way up in the air"], "rep_range": [20, 30],  # seconds
    },
    "jumping_jacks": {
        "name": "Jumping Jacks", "equipment": "bodyweight", "pattern": "play",
        "muscles": ["full body"],
        "cues": ["Jump feet out as arms go up", "Jump back in", "Land softly on the balls of your feet"],
        "mistakes": ["Landing with stiff legs"], "rep_range": [20, 30],
    },
    "animal_walks": {
        "name": "Animal Walks (frog, crab, duck)", "equipment": "bodyweight", "pattern": "play",
        "muscles": ["legs", "arms", "core"],
        "cues": ["Pick an animal and move like it across the room", "Switch animals each round", "Have fun with it"],
        "mistakes": [], "rep_range": [20, 40],
    },
}

# Things we never program for these groups
EXCLUDE = {
    "child": {"barbell_back_squat", "deadlift", "romanian_deadlift", "bench_press", "overhead_press", "barbell_row",
              "leg_press", "bulgarian_split_squat", "tricep_pushdown", "lat_pulldown", "hanging_knee_raise",
              "dumbbell_rdl", "dumbbell_bench_press", "dumbbell_shoulder_press", "dumbbell_row", "goblet_squat",
              "bicep_curl", "lateral_raise", "pull_up", "pike_push_up", "sit_to_stand", "wall_push_up", "step_up",
              "single_leg_balance"},
    "teen": {"deadlift", "bear_crawl", "animal_walks", "sit_to_stand", "wall_push_up", "single_leg_balance"},
    "senior": {"barbell_back_squat", "deadlift", "overhead_press", "pull_up", "hanging_knee_raise", "bulgarian_split_squat",
               "pike_push_up", "barbell_row", "walking_lunge", "bear_crawl", "animal_walks", "jumping_jacks"},
    "adult": {"bear_crawl", "animal_walks", "sit_to_stand", "wall_push_up", "single_leg_balance"},
}


def available_for(equipment: str, band: str = "adult") -> dict[str, dict]:
    allowed = {"full_gym": {"gym", "dumbbell", "bodyweight"},
               "home_dumbbells": {"dumbbell", "bodyweight"},
               "bodyweight": {"bodyweight"}}.get(equipment, {"bodyweight"})
    skip = EXCLUDE.get(band, set())
    return {k: v for k, v in EXERCISES.items() if v["equipment"] in allowed and k not in skip}
