#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
生成测试数据脚本
用于向数据库中添加各种测试任务，覆盖各种边界情况
"""
import requests
import random
import sys
from datetime import datetime, timedelta, date
from typing import List, Dict

# 设置输出编码为UTF-8（Windows控制台）
if sys.platform == 'win32':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

API_BASE_URL = "http://localhost:8000"

# 测试数据配置
CATEGORIES = ["工作", "学习", "生活", "其他", "项目A", "项目B", "购物", "健康", "旅行", "娱乐"]
PRIORITIES = [1, 2, 3]  # 1=高, 2=中, 3=低

# 各种测试场景的任务数据
TEST_TASKS = []

def generate_date_scenarios():
    """生成各种日期场景"""
    today = date.today()
    return {
        "today": today,
        "tomorrow": today + timedelta(days=1),
        "next_week": today + timedelta(days=7),
        "next_month": today + timedelta(days=30),
        "yesterday": today - timedelta(days=1),
        "last_week": today - timedelta(days=7),
        "last_month": today - timedelta(days=30),
        "far_future": today + timedelta(days=365),
        "far_past": today - timedelta(days=365),
    }

def create_task(
    title: str,
    description: str = "",
    category: str = "",
    priority: int = 2,
    due_date: date = None,  # type: ignore
    is_completed: bool = False
):
    """创建任务数据"""
    return {
        "title": title,
        "description": description,
        "category": category or random.choice(CATEGORIES),
        "priority": priority,
        "due_date": due_date.isoformat() if due_date else None,
        "is_completed": is_completed
    }

# 1. 正常任务 - 各种优先级和分类
for priority in PRIORITIES:
    priority_name = ["高", "中", "低"][priority - 1]
    for category in ["工作", "学习", "生活"]:
        TEST_TASKS.append(create_task(
            title=f"{priority_name}优先级 {category}任务",
            description=f"这是一个{priority_name}优先级的{category}任务描述。",
            category=category,
            priority=priority,
            due_date=date.today() + timedelta(days=random.randint(1, 30))
        ))

# 2. 超长标题测试（接近255字符限制）
long_title = "这是一个非常长的任务标题" * 10  # 约250字符
TEST_TASKS.append(create_task(
    title=long_title[:255],  # 确保不超过255字符
    description="测试超长标题的任务",
    priority=1
))

# 3. 超长描述测试（接近1000字符限制）
long_description = "这是一个非常长的任务描述内容。" * 50  # 约1000字符
TEST_TASKS.append(create_task(
    title="超长描述任务",
    description=long_description[:1000],  # 确保不超过1000字符
    priority=2
))

# 4. 包含换行的描述
multiline_description = """这是一个包含多行的任务描述。

第一段：这是第一段内容，描述了任务的基本情况。

第二段：这是第二段内容，包含了更多的详细信息。

第三段：这是最后一段，总结了任务的关键点。"""
TEST_TASKS.append(create_task(
    title="多行描述任务",
    description=multiline_description,
    priority=1
))

# 5. 各种日期场景
date_scenarios = generate_date_scenarios()
TEST_TASKS.append(create_task(
    title="今天截止的任务",
    description="这个任务的截止日期是今天",
    due_date=date_scenarios["today"],
    priority=1
))
TEST_TASKS.append(create_task(
    title="明天截止的任务",
    description="这个任务的截止日期是明天",
    due_date=date_scenarios["tomorrow"],
    priority=2
))
TEST_TASKS.append(create_task(
    title="已过期的任务",
    description="这个任务已经过期了",
    due_date=date_scenarios["yesterday"],
    priority=1
))
TEST_TASKS.append(create_task(
    title="一周前过期的任务",
    description="这个任务一周前就过期了",
    due_date=date_scenarios["last_week"],
    priority=1
))
TEST_TASKS.append(create_task(
    title="一个月后截止的任务",
    description="这个任务还有一个月才截止",
    due_date=date_scenarios["next_month"],
    priority=3
))
TEST_TASKS.append(create_task(
    title="一年后截止的任务",
    description="这个任务还有一年才截止",
    due_date=date_scenarios["far_future"],
    priority=3
))

# 6. 没有截止日期的任务
for i in range(5):
    TEST_TASKS.append(create_task(
        title=f"无截止日期任务 {i+1}",
        description="这个任务没有设置截止日期",
        priority=random.choice(PRIORITIES)
    ))
for i in range(10):
    TEST_TASKS.append(create_task(
        title=f"已完成的任务 {i+1}",
        description=f"这是第{i+1}个已完成的任务",
        category=random.choice(CATEGORIES),
        priority=random.choice(PRIORITIES),
        due_date=date.today() - timedelta(days=random.randint(1, 30)),
        is_completed=True
    ))

# 8. 自定义分类的任务
custom_categories = ["项目A", "项目B", "购物", "健康", "旅行", "娱乐"]
for category in custom_categories:
    TEST_TASKS.append(create_task(
        title=f"{category}相关任务",
        description=f"这是一个{category}分类的任务",
        category=category,
        priority=random.choice(PRIORITIES),
        due_date=date.today() + timedelta(days=random.randint(1, 60))
    ))

# 9. 边界情况：最短标题
TEST_TASKS.append(create_task(
    title="A",
    description="只有一个字符的标题",
    priority=2
))

# 10. 边界情况：空描述
TEST_TASKS.append(create_task(
    title="没有描述的任务",
    description="",
    priority=2
))

# 11. 特殊字符测试
TEST_TASKS.append(create_task(
    title="特殊字符任务：!@#$%^&*()",
    description="包含特殊字符的描述：!@#$%^&*()_+-=[]{}|;':\",./<>?",
    priority=1
))

# 12. Emoji测试
TEST_TASKS.append(create_task(
    title="包含Emoji的任务 ✨🎉🔥",
    description="这个任务包含各种Emoji：✨🎉🔥💡⭐️📝✅❌",
    priority=2
))

# 13. 中英文混合
TEST_TASKS.append(create_task(
    title="Mixed English and 中文 Title",
    description="This is a mixed description with English and 中文内容。",
    priority=2
))

# 14. 数字和符号
TEST_TASKS.append(create_task(
    title="任务编号 #12345",
    description="这是一个包含数字和符号的任务：版本v1.2.3，价格$99.99",
    priority=1
))

# 15. 各种组合的随机任务
for i in range(20):
    TEST_TASKS.append(create_task(
        title=f"随机任务 {i+1}",
        description=f"这是第{i+1}个随机生成的任务，用于测试各种组合情况。",
        category=random.choice(CATEGORIES),
        priority=random.choice(PRIORITIES),
        due_date=date.today() + timedelta(days=random.randint(-30, 60)),
        is_completed=random.choice([True, False])
    ))

def create_tasks_via_api(tasks: List[Dict]):
    """通过API创建任务"""
    created_count = 0
    failed_count = 0
    
    print(f"开始创建 {len(tasks)} 个测试任务...")
    print("-" * 60)
    
    for i, task in enumerate(tasks, 1):
        try:
            # 如果是已完成的任务，需要先创建，然后更新状态
            is_completed = task.pop("is_completed", False)
            
            response = requests.post(
                f"{API_BASE_URL}/tasks/",
                json=task,
                timeout=10
            )
            
            if response.status_code == 201:
                task_data = response.json()
                task_id = task_data.get("id")
                
                # 如果需要标记为已完成，使用PATCH更新
                if is_completed:
                    update_response = requests.patch(
                        f"{API_BASE_URL}/tasks/{task_id}",
                        json={"is_completed": True},
                        timeout=10
                    )
                    if update_response.status_code == 200:
                        print(f"[OK] [{i}/{len(tasks)}] 创建并完成: {task['title'][:50]}")
                    else:
                        print(f"[WARN] [{i}/{len(tasks)}] 创建成功但更新失败: {task['title'][:50]}")
                else:
                    print(f"[OK] [{i}/{len(tasks)}] 创建成功: {task['title'][:50]}")
                
                created_count += 1
            else:
                print(f"[FAIL] [{i}/{len(tasks)}] 创建失败: {task['title'][:50]}")
                print(f"  错误: {response.status_code} - {response.text}")
                failed_count += 1
                
        except requests.exceptions.RequestException as e:
            print(f"[ERROR] [{i}/{len(tasks)}] 请求异常: {task['title'][:50]}")
            print(f"  错误: {str(e)}")
            failed_count += 1
        except Exception as e:
            print(f"[ERROR] [{i}/{len(tasks)}] 未知错误: {task['title'][:50]}")
            print(f"  错误: {str(e)}")
            failed_count += 1
    
    print("-" * 60)
    print(f"完成！成功创建: {created_count}, 失败: {failed_count}")

if __name__ == "__main__":
    print("=" * 60)
    print("测试数据生成脚本")
    print("=" * 60)
    print(f"API地址: {API_BASE_URL}")
    print(f"准备创建 {len(TEST_TASKS)} 个测试任务")
    print()
    
    # 检查API是否可用
    try:
        response = requests.get(f"{API_BASE_URL}/tasks/", timeout=5)
        print("[OK] API连接正常")
    except requests.exceptions.RequestException as e:
        print(f"[ERROR] 无法连接到API: {e}")
        print("请确保后端服务正在运行 (http://localhost:8000)")
        exit(1)
    
    print()
    create_tasks_via_api(TEST_TASKS)

