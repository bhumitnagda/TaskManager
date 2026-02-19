import shortuuid
import datetime
import re
import json
import os
def validate_date(data_str):
    if isinstance(data_str, datetime.datetime):
        if data_str <= datetime.datetime.now():
            raise ValueError("Due date must be in the future.")
        return data_str
    
    data_str = str(data_str).strip().lower()
    
    match = re.fullmatch(r'(\d+)([dh])', data_str)
    if match:
        # match.groups() here captures all the substrings in the parentheses.
        value, unit = match.groups()
        value = int(value)
        if unit == 'd':
            delta = datetime.timedelta(days=value)
        else:
            delta = datetime.timedelta(hours=value)
        
        if delta < datetime.timedelta(hours=1):
            raise ValueError("Duration must be at least 1 hour.")
        
        return datetime.datetime.now() + delta
    
    for fmt in ["%Y-%m-%d", "%Y-%m-%d %H:%M:%S"]:
        try:
            return datetime.datetime.strptime(data_str, fmt)
        except ValueError:
            continue
  
    raise ValueError("Invalid date format. Use '5d', '3h', 'YYYY-MM-DD', or 'YYYY-MM-DD HH:MM:SS'")

    
    
def priority_check(value):
    if not (1 <= value <= 5):
        raise ValueError("Priority must be between 1 (highest) and 5 (lowest).")
    return value

def validate_title(name):
    name = name.strip()
    if not name:
        raise ValueError("Title cannot be empty.")
    if len(name) > 100:
        raise ValueError("Title cannot exceed 100 characters.")
    return name

class Logger:
    def __init__(self):
        self.__entries = []

    def log(self, level, message):
        entry = {
            "ts": datetime.datetime.now(),
            "level": level,
            "message": message
        }
        self.__entries.append(entry)

    def get_logs(self):
        copied = []
        for entry in self.__entries:
            copied.append(entry.copy())
        return copied    

    def dump(self):
        output = ""
        for entry in self.__entries:
            ts = entry["ts"].isoformat()
            level = entry["level"]
            message = entry["message"]
            output += f"{ts} [{level}] {message}\n"
        return output

class Task:
    def __init__(self, title, description="", due_date=None, priority=3):
        self.id = shortuuid.random(length=8)
        self.created_at = datetime.datetime.now()
        self.title = validate_title(title)
        self.description = description
        self.status = 'pending'
        self.priority = priority_check(priority)
        self.due_date = validate_date(due_date) if due_date else self.created_at + datetime.timedelta(days=1)

    def to_dict(self):
        return {
            'id': self.id,
            'created_at': self.created_at.isoformat(),
            'description': self.description,
            'status': self.status,
            'priority': self.priority,
            'due_date': self.due_date.isoformat(),
            'title': self.title
        }
    
    @classmethod
    def from_dict(cls, data):
       task = cls.__new__(cls)
       task.id = data['id']
       task.created_at = datetime.datetime.fromisoformat(data['created_at'])
       task.title = validate_title(data['title'])
       task.description = data['description']
       task.status = data['status']
       task.priority = priority_check(data['priority'])
     # task.due_date = datetime.datetime.fromisoformat(data['due_date'])
       # Edge case: no one should edit json for due date.
       try:
            task.due_date = datetime.datetime.fromisoformat(data['due_date'])
       except ValueError:
            raise ValueError(f"Invalid due_date format in JSON: {data['due_date']}")
       return task

    def __repr__(self):
       return f"Task(id={self.id}, title={self.title}, status={self.status})"
    
class TaskManager:
    def __init__(self,logger, file_handler):
        self.tasks = {}
        self.file_handler = file_handler
        self.logger = logger
        self.load_task()

    def add_task(self, title,description='',due_date=None,priority=3):
        task = Task(title, description, due_date, priority)
        self.tasks[task.id] = task
        self.logger.log('INFO',f"Added task: {task.id}")
        self.save_task()
        return task
    
    def get_task(self,task_id):
        return self.tasks.get(task_id)

    def update_task(self, task_id, title=None, description=None, priority=None, due_date=None, status=None):
        task = self.tasks.get(task_id)
        if not task:
            self.logger.log('WARNING',f"task not found: {task_id}")
            return False
        
        try:
            if title is not None:
                task.title = validate_title(title)
            
            if description is not None:
                task.description = description
            
            if priority is not None:
                task.priority = priority_check(priority)

            if due_date is not None:
                task.due_date = validate_date(due_date)

            if status is not None:
                valid_statuses = ['pending', 'in-progress', 'completed']
                if status not in valid_statuses:
                    raise ValueError(f"Invalid status.")
                task.status = status

            self.logger.log('INFO',f"task updated: {task_id}")
            self.save_task()
            return task

        except ValueError as e:
            self.logger.log('ERROR',f"Error updating task {task_id}: {e}")
            return False

    def delete_task(self, task_id):
        if task_id in self.tasks:
            del self.tasks[task_id]
            self.logger.log('INFO',f"task deleted: {task_id}")
            self.save_task()
            return True
        return False
    
    def list_task(self, status=None):
        list_task = []
        for task in self.tasks.values():
            if status is None or task.status == status:
                list_task.append(task)
        # Time completxity O(nlogn), if I would have used a bubblesort it would be O(n^2) which is not good for large n.
        sorted_tasks = sorted(list_task, key=lambda task: task.priority)
        return sorted_tasks

    def load_task(self):
        try:
            data = self.file_handler.load()
    
            for task_id, task_dict in data.items():
                task = Task.from_dict(task_dict)
                self.tasks[task_id] = task
            self.logger.log('INFO',f"loaded {len(self.tasks)} tasks from file.")

        except FileNotFoundError:
            self.logger.log('WARNING',f"File not found")
            self.tasks = {}

        except Exception as e:
            self.logger.log('ERROR',f"Error loading tasks: {e}")
            self.tasks = {}

    def save_task(self):
        try:
            data = {}
            for task_id, task in self.tasks.items():
                data[task_id] = task.to_dict()

            self.file_handler.save(data)
            self.logger.log('INFO',f"Saved {len(self.tasks)} tasks to file.")

        except Exception as e:
            self.logger.log('ERROR',f"Error saving tasks: {e}")

class FileHandler:
    def __init__(self,filepath):
        self.filepath = filepath
    
    def load(self):
        with open(self.filepath, 'r') as f:
            return json.load(f)

    def save(self, data):
        with open(self.filepath, 'w') as f:
            json.dump(data, f, indent=2)

def main():
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))
    filepath = os.path.join(BASE_DIR, 'tasks.json')
    logger = Logger()
    file_handler = FileHandler(filepath)
    task_manager = TaskManager(logger, file_handler)

    while True:
        print("1. Add task")
        print("2. View all tasks")
        print("3. View pending tasks")
        print("4. Update task")
        print("5. Delete task")
        print("6. Save and exit")

        choice = input("Enter your choice: ").strip()

        if choice == '1':
            try:
                title = input("Enter task title: ").strip()
                description = input("Enter task description: ").strip()
                due_date = input("Enter due date: ").strip()
                priority = int(input("Enter priority: ").strip())

                task = task_manager.add_task(title, description, due_date, priority)
                print(f"Task added with Id: {task.id}")

            except ValueError as e:
                print(f"Error: {e}")

        elif choice == '2':
            tasks = task_manager.list_task()
            for task in tasks:
                print(f"  [{task.id}] {task.title} (P:{task.priority}, {task.status})")

        elif choice == '3':
            tasks = task_manager.list_task(status='pending')
            for task in tasks:
                print(f"[{task.id}] {task.title} (P:{task.priority})")
        
        elif choice == '4':
            task_id = input("Enter task Id to update: ").strip()
            title = input("Enter new title or keep blank to skip: ").strip()
            status = input("Enter new status or blank: ").strip()
            priority = input("Enter new priority or blank: ").strip()
            due_date = input("Enter new due date or blank: ").strip()
            task_manager.update_task(
                            task_id,
                            title=title,
                            status=status,
                            priority=int(priority) ,
                            due_date=due_date 
                        )

        elif choice == "5":
            task_id = input("Task ID: ")
            if task_manager.delete_task(task_id):
                print("Deleted successfully.")
            else:
                print("Error, Task not found")

        elif choice == '6':
            task_manager.save_task()
            print("Tasks saved.")
            break

        else:
            print("Invalid choice")

if __name__ == "__main__":
    main()

# bug fix:
# Here when i create second task it is not stored inside the json file. 
# When i create a task with not a valid due date it does not show error message instead it reruns the while loop of main function.
