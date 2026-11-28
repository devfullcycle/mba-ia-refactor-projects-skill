"""Importing the package registers every mapped entity (needed by relationships and create_all)."""
from src.models.category_model import Category, CategoryRepository
from src.models.task_model import Task, TaskRepository
from src.models.user_model import User, UserRepository

__all__ = ["Category", "CategoryRepository", "Task", "TaskRepository", "User", "UserRepository"]
