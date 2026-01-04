import pytest
from taskmanager import Task, priority_check, validate_title,validate_date
import datetime

def test_priority_check_valid():
    assert priority_check(1) == 1
    assert priority_check(3) == 3
    assert priority_check(5) == 5

def test_priority_check_invalid():
    with pytest.raises(ValueError):
        priority_check(0)
    with pytest.raises(ValueError):
        priority_check(6)

def test_validate_title_valid():
    assert validate_title("Task 1") == "Task 1"
    assert validate_title("Task 2") == "Task 2"
    
def test_validate_title_invalid():
    with pytest.raises(ValueError):
        validate_title("")
    with pytest.raises(ValueError):
        validate_title("a" * 101)

def test_validate_date_valid():
    future_date = (datetime.datetime.now() + datetime.timedelta(days=1))
    assert validate_date(future_date) > datetime.datetime.now()

    result = validate_date("5d")
    assert result > datetime.datetime.now()

    result = validate_date("3h")
    assert result > datetime.datetime.now()

    result = validate_date('2026-1-2')
    assert result > datetime.datetime.now()

def test_validate_date_invalid():
    past_date = (datetime.datetime.now() - datetime.timedelta(days=1))
    with pytest.raises(ValueError):
        validate_date(past_date)
    with pytest.raises(ValueError):
        validate_date("invalid-date")

def test_task_creation_valid():
    task = Task(title='Test Title', description='Test Descript',due_date= '5d', priority=3)
    assert task.title == 'Test Title'
    assert task.description == 'Test Descript'
    assert task.priority == 3
    assert task.due_date > datetime.datetime.now()
    assert task.status == 'pending'

def test_task_creation_invalid_priority():
    with pytest.raises(ValueError):
        Task(title='Test Title', priority=6)
    with pytest.raises(ValueError):
        Task(title='', priority=3)

def test_task_to_dict():
    task = Task(title='Test Title', description='Test Descript', due_date='3h', priority=2)
    task_dict = task.to_dict()

    assert task_dict['title'] == 'Test Title'
    assert task_dict['description'] == 'Test Descript'
    assert task_dict['priority'] == 2
    assert task_dict['status'] == 'pending'
    assert isinstance(task_dict['due_date'], str)

def test_task_from_dict():
    task = Task(title='Test Title', description='Test Descript', due_date='1d', priority=4)
    task_dict = task.to_dict()
    new_task = Task.from_dict(task_dict)

    assert new_task.id == task.id
    assert new_task.title == task.title
    assert new_task.description == task.description
    assert new_task.priority == task.priority
    assert new_task.status == task.status
    assert new_task.due_date == task.due_date

# The repr() function in Python returns a developer-focused, unambiguous string representation of an object.

def test_task_repr():
    task = Task("Test", due_date="5d")
    repr_str = repr(task)
    assert "Task(" in repr_str
    assert task.id in repr_str
    assert "Test" in repr_str