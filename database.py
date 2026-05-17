import os
import re
import json
import bcrypt
from datetime import datetime
from sqlalchemy import create_engine, Column, Integer, String, Text, DateTime, Boolean, Table, ForeignKey, UniqueConstraint
from sqlalchemy.orm import declarative_base, sessionmaker, relationship
from pydantic import BaseModel, Field, ValidationError, field_validator
from typing import List, Dict, Optional

# --- Pydantic Models for Validation ---

class UserProfileSchema(BaseModel):
    name: str = Field(..., min_length=2, max_length=100)
    course: str = Field(..., max_length=100)
    degree_level: Optional[str] = None
    university: Optional[str] = None
    campus: Optional[str] = None
    location_zone: Optional[str] = None
    study_environment: List[str] = []
    study_vibe: List[str] = []
    subjects: List[str]
    goals: List[str]
    skill_levels: Dict[str, int]
    study_styles: List[str]

    @field_validator('subjects')
    @classmethod
    def subjects_not_empty(cls, v):
        if not v:
            raise ValueError('At least one subject is required')
        return v

    @field_validator('skill_levels')
    @classmethod
    def skill_levels_in_range(cls, v):
        for subj, level in v.items():
            if not (1 <= level <= 5):
                raise ValueError(f'Skill level for {subj} must be between 1 and 5')
        return v

USERNAME_PATTERN = re.compile(r'^[a-zA-Z0-9_]{3,30}$')
PASSWORD_MIN_LEN = 8

# --- Password Helpers ---

def hash_password(plain: str) -> str:
    return bcrypt.hashpw(plain.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

def verify_password(plain: str, hashed: str) -> bool:
    try:
        return bcrypt.checkpw(plain.encode('utf-8'), hashed.encode('utf-8'))
    except Exception:
        return False

# --- SQLAlchemy Setup ---

_DATABASE_URL = os.environ.get("DATABASE_URL")
if _DATABASE_URL:
    # Render/Heroku supply postgres:// — SQLAlchemy 2.x needs postgresql://
    _DATABASE_URL = _DATABASE_URL.replace("postgres://", "postgresql://", 1)
    engine = create_engine(_DATABASE_URL, echo=False)
else:
    DB_PATH = os.path.join(os.path.dirname(__file__), 'database_v5.db')
    engine = create_engine(f'sqlite:///{DB_PATH}', echo=False)
SessionLocal = sessionmaker(bind=engine)
Base = declarative_base()

# Association tables
group_members = Table(
    'group_members', Base.metadata,
    Column('group_id', Integer, ForeignKey('study_groups.id'), primary_key=True),
    Column('user_id', Integer, ForeignKey('users.id'), primary_key=True)
)

class User(Base):
    __tablename__ = 'users'

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(50), unique=True, index=True, nullable=False)
    password_hash = Column(String(255), nullable=False)
    name = Column(String(100))
    course = Column(String(100))
    degree_level = Column(String(50))
    university = Column(String(100))
    campus = Column(String(100))
    location_zone = Column(String(100))
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Storing JSON lists/dicts as Text for SQLite simplicity, but wrapped in SQLAlchemy models
    _subjects = Column("subjects", Text, default="[]")
    _goals = Column("goals", Text, default="[]")
    _skill_levels = Column("skill_levels", Text, default="{}")
    _study_styles = Column("study_styles", Text, default="[]")
    _study_environment = Column("study_environment", Text, default="[]")
    _study_vibe = Column("study_vibe", Text, default="[]")

    groups = relationship('StudyGroup', secondary=group_members, back_populates='members')
    availabilities = relationship('Availability', back_populates='user', cascade="all, delete-orphan")

    @property
    def subjects(self):
        return json.loads(self._subjects) if self._subjects else []

    @subjects.setter
    def subjects(self, val):
        self._subjects = json.dumps(val)

    @property
    def goals(self):
        return json.loads(self._goals) if self._goals else []

    @goals.setter
    def goals(self, val):
        self._goals = json.dumps(val)

    @property
    def skill_levels(self):
        return json.loads(self._skill_levels) if self._skill_levels else {}

    @skill_levels.setter
    def skill_levels(self, val):
        self._skill_levels = json.dumps(val)

    @property
    def study_styles(self):
        return json.loads(self._study_styles) if self._study_styles else []

    @study_styles.setter
    def study_styles(self, val):
        self._study_styles = json.dumps(val)

    @property
    def study_environment(self):
        return json.loads(self._study_environment) if self._study_environment else []

    @study_environment.setter
    def study_environment(self, val):
        self._study_environment = json.dumps(val)

    @property
    def study_vibe(self):
        return json.loads(self._study_vibe) if self._study_vibe else []

    @study_vibe.setter
    def study_vibe(self, val):
        self._study_vibe = json.dumps(val)

    def to_dict(self):
        return {
            'id': self.id,
            'username': self.username,
            'name': self.name,
            'course': self.course,
            'degree_level': self.degree_level,
            'university': self.university,
            'campus': self.campus,
            'location_zone': self.location_zone,
            'study_environment': self.study_environment,
            'study_vibe': self.study_vibe,
            'subjects': self.subjects,
            'goals': self.goals,
            'skill_levels': self.skill_levels,
            'study_styles': self.study_styles
        }

class StudyGroup(Base):
    __tablename__ = 'study_groups'

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False)
    subject = Column(String(100))
    meeting_times = Column(String(200))
    goals = Column(Text)
    description = Column(Text, default="")
    max_members = Column(Integer, default=8)
    is_private = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    members = relationship('User', secondary=group_members, back_populates='groups')

    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'subject': self.subject,
            'meeting_times': self.meeting_times,
            'goals': self.goals,
            'description': self.description or "",
            'max_members': self.max_members or 8,
            'is_private': self.is_private or False,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'members': [m.id for m in self.members],
            'member_names': [m.name or m.username for m in self.members],
        }

class WorkspaceTask(Base):
    __tablename__ = 'workspace_tasks'

    id = Column(Integer, primary_key=True, index=True)
    group_id = Column(Integer, ForeignKey('study_groups.id'), nullable=False)
    title = Column(String(200), nullable=False)
    description = Column(Text, default="")
    status = Column(String(50), default="To Do")
    priority = Column(String(10), default="Medium")
    due_date = Column(DateTime, nullable=True)
    assigned_to = Column(Integer, ForeignKey('users.id'), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    assignee = relationship('User', foreign_keys=[assigned_to])

    def to_dict(self):
        return {
            'id': self.id,
            'group_id': self.group_id,
            'title': self.title,
            'description': self.description or "",
            'status': self.status,
            'priority': self.priority or "Medium",
            'due_date': self.due_date.isoformat() if self.due_date else None,
            'assigned_to': self.assigned_to,
            'assignee_name': (self.assignee.name or self.assignee.username) if self.assignee else None,
            'created_at': self.created_at.isoformat() if self.created_at else None,
        }


class UserActivity(Base):
    __tablename__ = 'user_activity'

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    event_type = Column(String(50), nullable=False)
    payload = Column(Text, default="{}")
    created_at = Column(DateTime, default=datetime.utcnow)

    user = relationship('User')

class Availability(Base):
    __tablename__ = 'user_availability'

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    day = Column(String(20), nullable=False)
    time_slot = Column(String(50), nullable=False)

    user = relationship('User', back_populates='availabilities')
    
    __table_args__ = (UniqueConstraint('user_id', 'day', 'time_slot', name='_user_day_slot_uc'),)

def init_db():
    """Initializes the database schema."""
    try:
        Base.metadata.create_all(bind=engine)
    except Exception as e:
        print(f"Error initializing DB: {e}")

# --- DB Operations Repository ---

def get_user_by_username(username: str):
    db = SessionLocal()
    try:
        user = db.query(User).filter(User.username == username).first()
        return user.to_dict() if user else None
    finally:
        db.close()

def get_user_by_id(user_id: int):
    db = SessionLocal()
    try:
        user = db.query(User).filter(User.id == user_id).first()
        return user.to_dict() if user else None
    finally:
        db.close()

def get_all_users():
    db = SessionLocal()
    try:
        users = db.query(User).all()
        return [user.to_dict() for user in users]
    finally:
        db.close()

def create_user(username: str, password: str) -> str:
    """
    Returns 'ok', 'taken', or 'invalid'.
    'invalid' covers username pattern failures and short passwords.
    """
    if not USERNAME_PATTERN.match(username):
        return 'invalid'
    if len(password) < PASSWORD_MIN_LEN:
        return 'invalid'
    db = SessionLocal()
    try:
        if db.query(User).filter(User.username == username).first():
            return 'taken'
        new_user = User(username=username, password_hash=hash_password(password))
        db.add(new_user)
        db.commit()
        return 'ok'
    except Exception as e:
        db.rollback()
        print(f"Error creating user: {e}")
        return 'invalid'
    finally:
        db.close()


def authenticate_user(username: str, password: str) -> Optional[dict]:
    """Returns user dict on success, None on failure."""
    db = SessionLocal()
    try:
        user = db.query(User).filter(User.username == username).first()
        if not user:
            return None
        if not verify_password(password, user.password_hash):
            return None
        return user.to_dict()
    finally:
        db.close()

def update_user_profile(user_id: int, profile_data: dict) -> bool:
    """Updates user profile after passing through Pydantic validation."""
    db = SessionLocal()
    try:
        # Validate data
        try:
            validated = UserProfileSchema(**profile_data)
        except ValidationError as e:
            print(f"Validation error: {e}")
            return False

        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            return False
        
        user.name = validated.name
        user.course = validated.course
        user.degree_level = validated.degree_level
        user.university = validated.university
        user.campus = validated.campus
        user.location_zone = validated.location_zone
        user.study_environment = validated.study_environment
        user.study_vibe = validated.study_vibe
        user.subjects = validated.subjects
        user.goals = validated.goals
        user.skill_levels = validated.skill_levels
        user.study_styles = validated.study_styles
        
        db.commit()
        return True
    except Exception as e:
        db.rollback()
        print(f"Error updating user profile: {e}")
        return False
    finally:
        db.close()

def get_user_availability(user_id: int):
    db = SessionLocal()
    try:
        avails = db.query(Availability).filter(Availability.user_id == user_id).all()
        return [(a.day, a.time_slot) for a in avails]
    finally:
        db.close()

def set_user_availability(user_id: int, availability_list: list) -> bool:
    db = SessionLocal()
    try:
        # Clear existing
        db.query(Availability).filter(Availability.user_id == user_id).delete()
        
        # Add new
        new_avails = [Availability(user_id=user_id, day=day, time_slot=ts) for day, ts in availability_list]
        if new_avails:
            db.add_all(new_avails)
            
        db.commit()
        return True
    except Exception as e:
        db.rollback()
        print(f"Error setting availability: {e}")
        return False
    finally:
        db.close()

def get_all_availability():
    db = SessionLocal()
    try:
        avails = db.query(Availability).all()
        availability = {}
        for a in avails:
            if a.user_id not in availability:
                availability[a.user_id] = []
            availability[a.user_id].append((a.day, a.time_slot))
        return availability
    finally:
        db.close()

def create_group(name: str, subject: str, meeting_times: str, goals: str, creator_user_id: int) -> int:
    db = SessionLocal()
    try:
        new_group = StudyGroup(name=name, subject=subject, meeting_times=meeting_times, goals=goals)
        creator = db.query(User).filter(User.id == creator_user_id).first()
        if creator:
            new_group.members.append(creator)
            
        db.add(new_group)
        db.commit()
        return new_group.id
    except Exception as e:
        db.rollback()
        print(f"Error creating group: {e}")
        return -1
    finally:
        db.close()

def join_group(group_id: int, user_id: int) -> bool:
    db = SessionLocal()
    try:
        group = db.query(StudyGroup).filter(StudyGroup.id == group_id).first()
        user = db.query(User).filter(User.id == user_id).first()
        
        if group and user and user not in group.members:
            group.members.append(user)
            db.commit()
            return True
        return False
    except Exception as e:
        db.rollback()
        print(f"Error joining group: {e}")
        return False
    finally:
        db.close()

def leave_group(group_id: int, user_id: int) -> bool:
    db = SessionLocal()
    try:
        group = db.query(StudyGroup).filter(StudyGroup.id == group_id).first()
        user = db.query(User).filter(User.id == user_id).first()
        
        if group and user and user in group.members:
            group.members.remove(user)
            db.commit()
            return True
        return False
    except Exception as e:
        db.rollback()
        print(f"Error leaving group: {e}")
        return False
    finally:
        db.close()

def get_all_groups():
    db = SessionLocal()
    try:
        groups = db.query(StudyGroup).all()
        return [g.to_dict() for g in groups]
    finally:
        db.close()

def get_user_groups(user_id: int):
    db = SessionLocal()
    try:
        user = db.query(User).filter(User.id == user_id).first()
        if user:
            return [g.to_dict() for g in user.groups]
        return []
    finally:
        db.close()

# --- Workspace Tasks CRUD ---

def get_group_tasks(group_id: int):
    db = SessionLocal()
    try:
        tasks = db.query(WorkspaceTask).filter(WorkspaceTask.group_id == group_id).all()
        return [t.to_dict() for t in tasks]
    finally:
        db.close()

def add_group_task(group_id: int, title: str, priority: str = "Medium",
                   due_date=None, assigned_to: int = None, description: str = "") -> bool:
    db = SessionLocal()
    try:
        task = WorkspaceTask(
            group_id=group_id,
            title=title,
            priority=priority,
            due_date=due_date,
            assigned_to=assigned_to if assigned_to else None,
            description=description,
        )
        db.add(task)
        db.commit()
        return True
    except Exception as e:
        db.rollback()
        print(f"Error adding task: {e}")
        return False
    finally:
        db.close()

def update_task_status(task_id: int, new_status: str) -> bool:
    db = SessionLocal()
    try:
        task = db.query(WorkspaceTask).filter(WorkspaceTask.id == task_id).first()
        if task:
            task.status = new_status
            db.commit()
            return True
        return False
    except Exception as e:
        db.rollback()
        print(f"Error updating task: {e}")
        return False
    finally:
        db.close()

def get_group_member_names(group_id: int) -> List[dict]:
    """Returns list of {'id': ..., 'name': ...} for all group members."""
    db = SessionLocal()
    try:
        group = db.query(StudyGroup).filter(StudyGroup.id == group_id).first()
        if not group:
            return []
        return [{'id': m.id, 'name': m.name or m.username} for m in group.members]
    finally:
        db.close()

def delete_task(task_id: int) -> bool:
    db = SessionLocal()
    try:
        task = db.query(WorkspaceTask).filter(WorkspaceTask.id == task_id).first()
        if task:
            db.delete(task)
            db.commit()
            return True
        return False
    except Exception as e:
        db.rollback()
        print(f"Error deleting task: {e}")
        return False
    finally:
        db.close()


def log_activity(user_id: int, event_type: str, payload: dict = None) -> None:
    db = SessionLocal()
    try:
        entry = UserActivity(
            user_id=user_id,
            event_type=event_type,
            payload=json.dumps(payload or {}),
        )
        db.add(entry)
        db.commit()
    except Exception as e:
        db.rollback()
        print(f"Error logging activity: {e}")
    finally:
        db.close()


def get_recent_activity(user_id: int, limit: int = 10) -> List[dict]:
    db = SessionLocal()
    try:
        events = (
            db.query(UserActivity)
            .filter(UserActivity.user_id == user_id)
            .order_by(UserActivity.created_at.desc())
            .limit(limit)
            .all()
        )
        return [
            {
                'event_type': e.event_type,
                'payload': json.loads(e.payload) if e.payload else {},
                'created_at': e.created_at,
            }
            for e in events
        ]
    finally:
        db.close()

