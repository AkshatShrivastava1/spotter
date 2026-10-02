"""Small built-in food reference (approximate values per common serving).

Used two ways:
1. Offline/mock mode: a keyword parser estimates meals without an LLM.
2. Grounding: the LLM prompt can be given matching references to anchor its estimates.

Values are rounded USDA / IFCT-style averages. Good enough for an MVP; swap for a
real database (USDA FoodData Central, Open Food Facts) later.
"""

# name: (aliases, serving, grams, kcal, protein, carbs, fat, fiber)
FOODS: dict[str, tuple[list[str], str, int, int, float, float, float, float]] = {
    "roti": (["chapati", "phulka", "rotis", "chapatis"], "1 medium", 40, 120, 3.5, 20, 3, 3),
    "paratha": (["parantha", "parathas"], "1 plain", 80, 260, 5, 36, 10, 4),
    "aloo paratha": (["aloo parantha"], "1 piece", 120, 320, 6, 45, 13, 4),
    "naan": (["butter naan"], "1 piece", 90, 270, 8, 45, 6, 2),
    "white rice": (["rice", "chawal", "steamed rice"], "1 cup cooked", 160, 205, 4, 45, 0.5, 0.6),
    "brown rice": ([], "1 cup cooked", 195, 215, 5, 45, 1.8, 3.5),
    "biryani": (["chicken biryani"], "1 plate", 350, 600, 25, 70, 22, 3),
    "dal": (["daal", "dal tadka", "yellow dal", "lentils", "dal fry"], "1 cup", 200, 230, 12, 30, 6, 8),
    "rajma": (["kidney beans", "rajma masala"], "1 cup", 200, 250, 13, 35, 6, 11),
    "chole": (["chana masala", "chickpea curry", "chickpeas"], "1 cup", 200, 280, 12, 38, 9, 10),
    "paneer": (["cottage cheese"], "100 g", 100, 265, 18, 3, 20, 0),
    "paneer bhurji": ([], "1 cup", 150, 330, 20, 8, 24, 1),
    "palak paneer": ([], "1 cup", 200, 320, 15, 10, 24, 4),
    "sabzi": (["mixed veg", "vegetable curry", "sabji", "aloo gobi", "bhindi"], "1 cup", 150, 150, 4, 15, 8, 5),
    "curd": (["dahi", "plain yogurt", "yogurt", "raita"], "1 cup", 245, 150, 9, 11, 8, 0),
    "greek yogurt": (["greek yoghurt"], "1 cup nonfat", 245, 145, 25, 9, 0.5, 0),
    "egg": (["eggs", "boiled egg", "boiled eggs", "anda"], "1 large", 50, 72, 6.3, 0.4, 4.8, 0),
    "egg whites": (["egg white"], "1 large white", 33, 17, 3.6, 0.2, 0, 0),
    "omelette": (["omelet", "masala omelette"], "2-egg", 120, 200, 13, 2, 15, 0.5),
    "chicken breast": (["grilled chicken", "chicken"], "150 g cooked", 150, 248, 46, 0, 5.4, 0),
    "butter chicken": ([], "1 cup", 240, 490, 30, 12, 35, 2),
    "chicken curry": ([], "1 cup", 240, 350, 28, 8, 22, 2),
    "fish": (["salmon", "grilled fish"], "150 g cooked", 150, 280, 38, 0, 13, 0),
    "tuna": (["canned tuna"], "1 can drained", 140, 160, 35, 0, 1.5, 0),
    "tofu": ([], "150 g firm", 150, 215, 24, 4, 12, 3),
    "oats": (["oatmeal", "porridge", "overnight oats"], "1 cup cooked", 240, 165, 6, 28, 3.5, 4),
    "poha": ([], "1 plate", 200, 270, 5, 45, 8, 2),
    "upma": ([], "1 plate", 200, 250, 6, 38, 8, 3),
    "idli": (["idlis"], "1 piece", 40, 58, 2, 12, 0.4, 0.5),
    "dosa": (["masala dosa", "plain dosa"], "1 piece", 120, 170, 4, 29, 4, 1),
    "sambar": ([], "1 cup", 200, 140, 6, 20, 4, 5),
    "bread": (["toast", "slice of bread", "white bread"], "1 slice", 30, 80, 3, 14, 1, 0.8),
    "whole wheat bread": (["brown bread"], "1 slice", 32, 80, 4, 14, 1, 2),
    "peanut butter": (["pb"], "1 tbsp", 16, 95, 4, 3, 8, 1),
    "banana": (["bananas"], "1 medium", 118, 105, 1.3, 27, 0.4, 3),
    "apple": (["apples"], "1 medium", 180, 95, 0.5, 25, 0.3, 4),
    "milk": (["doodh", "whole milk"], "1 cup", 245, 150, 8, 12, 8, 0),
    "whey protein": (["protein shake", "whey", "protein powder"], "1 scoop", 32, 120, 24, 3, 1.5, 0),
    "almonds": (["badam"], "1 oz (23)", 28, 165, 6, 6, 14, 3.5),
    "pizza": (["pizza slice"], "1 slice", 110, 285, 12, 36, 10, 2.5),
    "burger": (["cheeseburger"], "1 burger", 220, 540, 28, 40, 29, 2),
    "fries": (["french fries"], "medium", 115, 365, 4, 48, 17, 4),
    "pasta": (["spaghetti"], "1 cup cooked", 140, 220, 8, 43, 1.3, 2.5),
    "salad": (["green salad"], "1 bowl", 150, 50, 2, 9, 0.5, 3),
    "samosa": (["samosas"], "1 piece", 100, 260, 4, 30, 14, 2.5),
    "chai": (["tea", "masala chai"], "1 cup with milk+sugar", 200, 100, 3, 14, 3.5, 0),
    "coffee": (["black coffee"], "1 cup", 240, 5, 0.3, 0, 0, 0),
    "latte": (["cappuccino"], "12 oz", 350, 190, 10, 15, 10, 0),
    "soda": (["coke", "pepsi", "soft drink"], "12 oz can", 355, 140, 0, 39, 0, 0),
    "beer": ([], "12 oz", 355, 150, 1.6, 13, 0, 0),
    "ghee": (["butter"], "1 tbsp", 14, 120, 0, 0, 14, 0),
    "khichdi": ([], "1 cup", 200, 240, 9, 38, 6, 5),
    "maggi": (["instant noodles", "ramen"], "1 pack", 70, 310, 7, 44, 12, 2),
    "sandwich": (["veg sandwich"], "1 sandwich", 150, 300, 10, 40, 11, 3),
}

NUMBER_WORDS = {
    "a": 1, "an": 1, "one": 1, "two": 2, "three": 3, "four": 4, "five": 5, "six": 6,
    "half": 0.5, "couple": 2, "few": 3,
}
