export type Macros = { kcal: number; protein_g: number; carbs_g: number; fat_g: number };

export type FoodItem = Macros & {
  name: string;
  quantity: string;
  fiber_g?: number;
  confidence: 'high' | 'medium' | 'low' | string;
};

export type MealType = 'breakfast' | 'lunch' | 'dinner' | 'snack';

export type Meal = Macros & {
  id: number;
  meal_type: MealType;
  description: string;
  source: string;
  coach_feedback: string | null;
  items: FoodItem[];
};

export type Notification = {
  id: number;
  kind: string;
  title: string;
  body: string;
  read: boolean;
  created_at: string;
};

export type PlanExercise = { slug: string; name: string; sets: number; reps: string; rest_s: number };
export type PlanDay = { day: string; focus: string; exercises: PlanExercise[] };
export type Plan = { id: number; name: string; days: PlanDay[]; notes: string };

export type Today = {
  age_band: 'child' | 'teen' | 'adult' | 'senior';
  show_calories: boolean;
  name: string;
  day: string;
  local_time: string;
  target: Macros & { water_ml: number; steps: number };
  eaten: Macros & { fiber_g: number };
  remaining: Macros & { water_ml: number; steps: number };
  water_ml: number;
  steps: number;
  weight_kg: number | null;
  kcal_adjustment: number;
  meals: Meal[];
  meal_types_logged: MealType[];
  workout_done: boolean;
  todays_workout: PlanDay | null;
  flags: string[];
  streak: number;
  coach_card: Notification | null;
  unread: number;
};

export type ParseResult = { items: FoodItem[]; clarifying_question: string; totals: Macros };

export type Exercise = {
  slug: string;
  name: string;
  equipment: string;
  pattern: string;
  muscles: string[];
  cues: string[];
  mistakes: string[];
  rep_range: [number, number];
};

export type WeekAvg = { week_start: string; week_end: string; avg_kg: number | null; weigh_ins: number };
export type Trend = {
  daily: { day: string; kg: number }[];
  weekly: WeekAvg[];
  this_week_avg: number | null;
  last_week_avg: number | null;
  change_kg: number | null;
  change_pct: number | null;
  verdict: string;
};

export type CheckinQuestion = { key: string; q: string; type: 'scale' | 'text' };
export type Checkin = {
  id: number;
  week_end: string;
  avg_weight_kg: number | null;
  prev_avg_weight_kg: number | null;
  coach_review: string;
  kcal_change: number;
};
