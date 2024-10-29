import json
import os
from datetime import datetime, timedelta
import hashlib

def generate_user_id(group_name, user_nickname):
    # Combine group name and user nickname
    combined = f"{group_name}:{user_nickname}"

    # Create a SHA256 hash
    hash_object = hashlib.sha256(combined.encode('utf-8'))

    # Get the hexadecimal representation of the hash
    hex_dig = hash_object.hexdigest()

    # Return the first 16 characters of the hash as the user ID
    return hex_dig[:16]

class UserManager:
    def __init__(self, file_path="user_data"):
        self.file_path = file_path
        if not os.path.exists(file_path):
            os.makedirs(file_path)

    def load_user(self, user_id):
        file_path = f"{self.file_path}/{user_id}.json"
        if not os.path.exists(file_path):
            # Create a new user file with initial data
            initial_data = self.create_initial_user_data(user_id)
            self.save_user(initial_data)
            return initial_data

        with open(file_path, "r",encoding='utf-8') as f:
            return json.load(f)

    def create_initial_user_data(self, user_id):
        today = datetime.now().strftime("%Y-%m-%d")
        return {
            "user_id": user_id,
            "username": f"",  # Default username
            "level": "青铜",
            "total_score": 0,
            "current_day_score": 0,
            "last_update_date": today,
            "consecutive_days": 0,
            "scores_history": [{"date": today, "score": 0}],
            "achievements": [],
            "rewards": []
        }

    def save_user(self, user_data):
        with open(f"{self.file_path}/{user_data['user_id']}.json", "w", encoding='utf-8') as f:
            json.dump(user_data, f, indent=2)

    def update_user_score(self, user_id, user_name,score):
        score = int(score)
        user_data = self.load_user(user_id)
        user_data['username'] = user_name
        if not user_data:
            return None

        today = datetime.now().strftime("%Y-%m-%d")
        is_new_day = user_data['last_update_date'] != today
        previous_score = user_data['current_day_score']
        if is_new_day:
            # New day
            self.handle_new_day(user_data, score, today)
        else:
            # Same day, update only if score is higher
            if score > user_data['current_day_score']:
                user_data['current_day_score'] = score
                user_data['scores_history'][0]['score'] = score

        # Calculate score difference
        score_diff = max(0, user_data['current_day_score'] - previous_score)

        # Update total score
        user_data['total_score'] += score_diff

        # Check for achievements and rewards (only if score improved)
        if score_diff > 0:
            self.check_achievements(user_data)
            self.apply_rewards(user_data, is_new_day)

        # Update level
        self.update_level(user_data)

        self.save_user(user_data)
        return user_data

    def handle_new_day(self, user_data, score, today):
        user_data['scores_history'].insert(0, {"date": today, "score": score})
        if len(user_data['scores_history']) > 7:
            user_data['scores_history'] = user_data['scores_history'][:7]

        if user_data['last_update_date'] == (datetime.now() - timedelta(days=1)).strftime("%Y-%m-%d"):
            user_data['consecutive_days'] += 1
            self.check_consecutive_days_achievement(user_data)
        else:
            user_data['consecutive_days'] = 1
            self.remove_consecutive_days_achievements(user_data)

        user_data['current_day_score'] = score
        user_data['last_update_date'] = today

    def check_achievements(self, user_data):
        # Check for "首次满分" achievement
        if user_data['current_day_score'] == 5 and not any(a['name'] == "首次满分" for a in user_data['achievements']):
            user_data['achievements'].append(
                {"name": "首次满分", "achieved": True, "date": user_data['last_update_date']})

    def apply_rewards(self, user_data, is_new_day):
        # Apply reward only if it's a new day or the score improved to 5
        if is_new_day or (user_data['current_day_score'] == 5 and not any(r['date'] == user_data['last_update_date'] for r in user_data['rewards'])):
            user_data['rewards'].append({"name": "额外经验值", "amount": 10, "date": user_data['last_update_date']})
            user_data['total_score'] += 10

    def check_consecutive_days_achievement(self, user_data):
        consecutive_days = user_data['consecutive_days']
        achievements_to_check = [
            ("连续打卡3天", 3),
            ("连续打卡5天", 5),
            ("连续打卡7天", 7)
        ]

        for achievement_name, days_required in achievements_to_check:
            if consecutive_days >= days_required and not any(
                    a['name'] == achievement_name for a in user_data['achievements']):
                user_data['achievements'].append({
                    "name": achievement_name,
                    "achieved": True,
                    "date": user_data['last_update_date']
                })

    def remove_consecutive_days_achievements(self, user_data):
        achievements_to_remove = ["连续打卡3天", "连续打卡5天", "连续打卡7天"]
        user_data['achievements'] = [a for a in user_data['achievements'] if a['name'] not in achievements_to_remove]

    def remove_achievement(self, user_id, achievement_name):
        user_data = self.load_user(user_id)
        if not user_data:
            return None

        user_data['achievements'] = [a for a in user_data['achievements'] if a['name'] != achievement_name]
        self.save_user(user_data)
        return user_data

    def update_level(self, user_data):
        # Define level thresholds
        levels = [
            ("青铜", 0),
            ("白银", 20),
            ("黄金", 50),
            ("铂金", 90),
            ("钻石", 140),
            ("王者", 200)
        ]

        for level, threshold in reversed(levels):
            if user_data['total_score'] >= threshold:
                user_data['level'] = level
                break

    def deduct_points(self):
        # Deduct points for users who didn't check in today
        today = datetime.now().strftime("%Y-%m-%d")
        for user_file in os.listdir(self.file_path):
            user_data = self.load_user(user_file.split('.')[0])
            if user_data['last_update_date'] != today:
                user_data['total_score'] = max(0, int(user_data['total_score']) - 3)  # Deduct 3 points, minimum 0
                user_data['consecutive_days'] = 0
                self.save_user(user_data)