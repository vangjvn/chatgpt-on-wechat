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
            "username": "",
            "level": "青铜",
            "total_score": 0,
            "current_day_score": 0,
            "last_update_date": today,
            "consecutive_days": 0,
            "scores_history": [{"date": today, "score": 0}],
            "achievements": {
                "首次满分": {"achieved": False, "date": None},
                "连续打卡3天": {"achieved": False, "date": None, "bonus": 1},
                "连续打卡5天": {"achieved": False, "date": None, "bonus": 2},
                "连续打卡7天": {"achieved": False, "date": None, "bonus": 3}
            },
            "rewards": {
                "首次满分": {"achieved": False, "date": None, "amount": 10},
                "连续打卡": {"achieved": False, "date": None, "amount": 1}
            }
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
            # New day - 直接将今天的分数加到总分上
            user_data['total_score'] += score
            self.handle_new_day(user_data, score, today)
        else:
            # 同一天 - 只有当新分数更高时才增加总分差值
            if score > user_data['current_day_score']:
                score_diff = score - user_data['current_day_score']
                user_data['total_score'] += score_diff
                user_data['current_day_score'] = score
                user_data['scores_history'][0]['score'] = score

        # Check for achievements and rewards (only if score improved)
        if is_new_day or score > user_data['current_day_score']:
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
        today = user_data['last_update_date']

        # 检查首次满分
        if user_data['current_day_score'] == 5 and not user_data['achievements']['首次满分']['achieved']:
            user_data['achievements']['首次满分'] = {
                "achieved": True,
                "date": today
            }
            # 首次满分奖励
            user_data['rewards']['首次满分'] = {
                "achieved": True,
                "date": today,
                "amount": 10
            }
            user_data['total_score'] += 10

    def apply_rewards(self, user_data, is_new_day):
        # Apply reward only if it's a new day or the score improved to 5
        if is_new_day or (user_data['current_day_score'] == 5 and not any(r['date'] == user_data['last_update_date'] for r in user_data['rewards'])):
            user_data['rewards'].append({"name": "额外经验值", "amount": 10, "date": user_data['last_update_date']})
            user_data['total_score'] += 10

    def check_consecutive_days_achievement(self, user_data):
        consecutive_days = user_data['consecutive_days']
        today = user_data['last_update_date']

        # 检查连续打卡成就
        achievements_to_check = [
            ("连续打卡3天", 3),
            ("连续打卡5天", 5),
            ("连续打卡7天", 7)
        ]

        # 给予连续打卡基础奖励（≥7天每天1分）
        if consecutive_days >= 7:
            user_data['rewards']['连续打卡'] = {
                "achieved": True,
                "date": today,
                "amount": 1
            }
            user_data['total_score'] += 1

        # 给予达到特定天数的额外奖励
        for achievement_name, days_required in achievements_to_check:
            if consecutive_days == days_required and not user_data['achievements'][achievement_name]['achieved']:
                user_data['achievements'][achievement_name] = {
                    "achieved": True,
                    "date": today,
                    "bonus": days_required
                }
                # 达到特定天数时给予额外奖励
                user_data['total_score'] += 1

    def remove_consecutive_days_achievements(self, user_data):
        # 重置连续打卡相关的成就和奖励
        achievements_to_reset = ["连续打卡3天", "连续打卡5天", "连续打卡7天"]
        for achievement in achievements_to_reset:
            user_data['achievements'][achievement] = {
                "achieved": False,
                "date": None,
                "bonus": int(achievement[4:-1])  # 提取天数
            }

        # 重置连续打卡奖励
        user_data['rewards']['连续打卡'] = {
            "achieved": False,
            "date": None,
            "amount": 1
        }

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