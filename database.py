import os
import re
import json
import bcrypt
from datetime import datetime
from sqlalchemy import (
    create_engine, Column, Integer, String, Text, DateTime,
    Boolean, Table, ForeignKey, UniqueConstraint, inspect, text,
)
from sqlalchemy.orm import declarative_base, sessionmaker, relationship
from pydantic import BaseModel, Field, ValidationError, field_validator
from typing import List, Dict, Optional

# ── Pydantic Validation Schema ────────────────────────────────────────────────

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

# ── Password Helpers ──────────────────────────────────────────────────────────

def hash_password(plain: str) -> str:
    return bcrypt.hashpw(plain.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

def verify_password(plain: str, hashed: str) -> bool:
    try:
        return bcrypt.checkpw(plain.encode('utf-8'), hashed.encode('utf-8'))
    except Exception:
        return False

# ── SQLAlchemy Setup ──────────────────────────────────────────────────────────

_DATABASE_URL = os.environ.get("DATABASE_URL")
if _DATABASE_URL:
    _DATABASE_URL = _DATABASE_URL.replace("postgres://", "postgresql://", 1)
    engine = create_engine(_DATABASE_URL, echo=False)
else:
    DB_PATH = os.path.join(os.path.dirname(__file__), 'database_v5.db')
    engine = create_engine(f'sqlite:///{DB_PATH}', echo=False)

SessionLocal = sessionmaker(bind=engine)
Base = declarative_base()

# ── Association tables ────────────────────────────────────────────────────────

group_members = Table(
    'group_members', Base.metadata,
    Column('group_id', Integer, ForeignKey('study_groups.id'), primary_key=True),
    Column('user_id', Integer, ForeignKey('users.id'), primary_key=True),
)

# ── ORM Models ────────────────────────────────────────────────────────────────

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

    # JSON lists/dicts stored as Text (SQLite-compatible; PostgreSQL users can migrate to JSONB)
    _subjects         = Column("subjects",          Text, default="[]")
    _goals            = Column("goals",             Text, default="[]")
    _skill_levels     = Column("skill_levels",      Text, default="{}")
    _study_styles     = Column("study_styles",      Text, default="[]")
    _study_environment = Column("study_environment", Text, default="[]")
    _study_vibe       = Column("study_vibe",        Text, default="[]")

    groups = relationship('StudyGroup', secondary=group_members, back_populates='members')
    availabilities = relationship('Availability', back_populates='user', cascade="all, delete-orphan")

    # ── JSON property accessors ───────────────────────────────────────────────
    @property
    def subjects(self):
        return json.loads(self._subjects) if self._subjects else []
    @subjects.setter
    def subjects(self, val): self._subjects = json.dumps(val)

    @property
    def goals(self):
        return json.loads(self._goals) if self._goals else []
    @goals.setter
    def goals(self, val): self._goals = json.dumps(val)

    @property
    def skill_levels(self):
        return json.loads(self._skill_levels) if self._skill_levels else {}
    @skill_levels.setter
    def skill_levels(self, val): self._skill_levels = json.dumps(val)

    @property
    def study_styles(self):
        return json.loads(self._study_styles) if self._study_styles else []
    @study_styles.setter
    def study_styles(self, val): self._study_styles = json.dumps(val)

    @property
    def study_environment(self):
        return json.loads(self._study_environment) if self._study_environment else []
    @study_environment.setter
    def study_environment(self, val): self._study_environment = json.dumps(val)

    @property
    def study_vibe(self):
        return json.loads(self._study_vibe) if self._study_vibe else []
    @study_vibe.setter
    def study_vibe(self, val): self._study_vibe = json.dumps(val)

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
            'study_styles': self.study_styles,
        }


class StudyGroup(Base):
    __tablename__ = 'study_groups'

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False)
    subject = Column(String(100))
    meeting_times = Column(String(200))
    goals = Column(Text)                          # free-text goal description
    description = Column(Text, default="")
    max_members = Column(Integer, default=8)
    is_private = Column(Boolean, default=False)
    creator_id = Column(Integer, ForeignKey('users.id'), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    members = relationship('User', secondary=group_members, back_populates='groups')
    creator = relationship('User', foreign_keys=[creator_id])

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
            'creator_id': self.creator_id,
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


class UserWeights(Base):
    """Persists each user's Weight Studio preferences across sessions."""
    __tablename__ = 'user_weights'

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey('users.id'), unique=True, nullable=False)
    weights_json = Column(Text, default="{}")
    updated_at = Column(DateTime, default=datetime.utcnow)

    user = relationship('User')


class StudySession(Base):
    """A concrete study session proposed or confirmed by a group."""
    __tablename__ = 'study_sessions'

    id = Column(Integer, primary_key=True, index=True)
    group_id = Column(Integer, ForeignKey('study_groups.id'), nullable=False)
    day = Column(String(20), nullable=False)
    time_slot = Column(String(50), nullable=False)
    scheduled_date = Column(DateTime, nullable=True)
    status = Column(String(20), default='Proposed')  # Proposed | Confirmed | Completed | Cancelled
    notes = Column(Text, default="")
    created_by = Column(Integer, ForeignKey('users.id'), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    group = relationship('StudyGroup')
    creator = relationship('User', foreign_keys=[created_by])

    def to_dict(self):
        return {
            'id': self.id,
            'group_id': self.group_id,
            'day': self.day,
            'time_slot': self.time_slot,
            'scheduled_date': self.scheduled_date.isoformat() if self.scheduled_date else None,
            'status': self.status,
            'notes': self.notes or "",
            'created_by': self.created_by,
            'created_at': self.created_at.isoformat() if self.created_at else None,
        }


# ── DB Initialisation ─────────────────────────────────────────────────────────

def _run_migrations():
    """Add columns/tables introduced after the initial schema was deployed."""
    is_pg = engine.dialect.name == 'postgresql'
    bool_default = "FALSE" if is_pg else "0"
    try:
        insp = inspect(engine)
        existing_tables = insp.get_table_names()

        # study_groups — columns added in v2
        if 'study_groups' in existing_tables:
            sg_cols = {c['name'] for c in insp.get_columns('study_groups')}
            with engine.begin() as conn:
                if 'description' not in sg_cols:
                    conn.execute(text("ALTER TABLE study_groups ADD COLUMN description TEXT DEFAULT ''"))
                if 'max_members' not in sg_cols:
                    conn.execute(text("ALTER TABLE study_groups ADD COLUMN max_members INTEGER DEFAULT 8"))
                if 'is_private' not in sg_cols:
                    conn.execute(text(f"ALTER TABLE study_groups ADD COLUMN is_private BOOLEAN DEFAULT {bool_default}"))
                if 'creator_id' not in sg_cols:
                    conn.execute(text("ALTER TABLE study_groups ADD COLUMN creator_id INTEGER REFERENCES users(id)"))
    except Exception as e:
        print(f"Migration warning: {e}")


def init_db():
    try:
        Base.metadata.create_all(bind=engine)
        _run_migrations()
    except Exception as e:
        print(f"Error initializing DB: {e}")


# ── User CRUD ─────────────────────────────────────────────────────────────────

def get_user_by_username(username: str) -> Optional[dict]:
    db = SessionLocal()
    try:
        user = db.query(User).filter(User.username == username).first()
        return user.to_dict() if user else None
    finally:
        db.close()


def get_user_by_id(user_id: int) -> Optional[dict]:
    db = SessionLocal()
    try:
        user = db.query(User).filter(User.id == user_id).first()
        return user.to_dict() if user else None
    finally:
        db.close()


def get_all_users() -> List[dict]:
    db = SessionLocal()
    try:
        return [u.to_dict() for u in db.query(User).all()]
    finally:
        db.close()


def create_user(username: str, password: str) -> str:
    """Returns 'ok', 'taken', or 'invalid'."""
    if not USERNAME_PATTERN.match(username):
        return 'invalid'
    if len(password) < PASSWORD_MIN_LEN:
        return 'invalid'
    db = SessionLocal()
    try:
        if db.query(User).filter(User.username == username).first():
            return 'taken'
        db.add(User(username=username, password_hash=hash_password(password)))
        db.commit()
        return 'ok'
    except Exception as e:
        db.rollback()
        print(f"Error creating user: {e}")
        return 'invalid'
    finally:
        db.close()


def authenticate_user(username: str, password: str) -> Optional[dict]:
    db = SessionLocal()
    try:
        user = db.query(User).filter(User.username == username).first()
        if not user or not verify_password(password, user.password_hash):
            return None
        return user.to_dict()
    finally:
        db.close()


def update_user_profile(user_id: int, profile_data: dict) -> bool:
    db = SessionLocal()
    try:
        validated = UserProfileSchema(**profile_data)
    except ValidationError as e:
        print(f"Validation error: {e}")
        return False

    try:
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


# ── Availability CRUD ─────────────────────────────────────────────────────────

def get_user_availability(user_id: int) -> List[tuple]:
    db = SessionLocal()
    try:
        return [(a.day, a.time_slot) for a in
                db.query(Availability).filter(Availability.user_id == user_id).all()]
    finally:
        db.close()


def set_user_availability(user_id: int, availability_list: list) -> bool:
    db = SessionLocal()
    try:
        db.query(Availability).filter(Availability.user_id == user_id).delete()
        if availability_list:
            db.add_all([Availability(user_id=user_id, day=d, time_slot=ts)
                        for d, ts in availability_list])
        db.commit()
        return True
    except Exception as e:
        db.rollback()
        print(f"Error setting availability: {e}")
        return False
    finally:
        db.close()


def get_all_availability() -> Dict[int, List[tuple]]:
    db = SessionLocal()
    try:
        avail: Dict[int, List[tuple]] = {}
        for a in db.query(Availability).all():
            avail.setdefault(a.user_id, []).append((a.day, a.time_slot))
        return avail
    finally:
        db.close()


# ── Group CRUD ────────────────────────────────────────────────────────────────

def create_group(
    name: str,
    subject: str,
    meeting_times: str,
    goals: str,
    creator_user_id: int,
    description: str = "",
    max_members: int = 8,
    is_private: bool = False,
) -> int:
    """Create a group, add the creator as first member, return new group id (-1 on failure)."""
    db = SessionLocal()
    try:
        creator = db.query(User).filter(User.id == creator_user_id).first()
        if not creator:
            return -1
        group = StudyGroup(
            name=name,
            subject=subject,
            meeting_times=meeting_times,
            goals=goals,
            description=description,
            max_members=max_members,
            is_private=is_private,
            creator_id=creator_user_id,
        )
        group.members.append(creator)
        db.add(group)
        db.commit()
        return group.id
    except Exception as e:
        db.rollback()
        print(f"Error creating group: {e}")
        return -1
    finally:
        db.close()


def update_group(
    group_id: int,
    name: str = None,
    subject: str = None,
    meeting_times: str = None,
    goals: str = None,
    description: str = None,
    max_members: int = None,
) -> bool:
    db = SessionLocal()
    try:
        group = db.query(StudyGroup).filter(StudyGroup.id == group_id).first()
        if not group:
            return False
        if name is not None:
            group.name = name
        if subject is not None:
            group.subject = subject
        if meeting_times is not None:
            group.meeting_times = meeting_times
        if goals is not None:
            group.goals = goals
        if description is not None:
            group.description = description
        if max_members is not None:
            group.max_members = max_members
        db.commit()
        return True
    except Exception as e:
        db.rollback()
        print(f"Error updating group: {e}")
        return False
    finally:
        db.close()


def join_group(group_id: int, user_id: int) -> bool:
    db = SessionLocal()
    try:
        group = db.query(StudyGroup).filter(StudyGroup.id == group_id).first()
        user = db.query(User).filter(User.id == user_id).first()
        if group and user and user not in group.members:
            # Respect max_members cap
            if len(group.members) < (group.max_members or 8):
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


def get_all_groups() -> List[dict]:
    db = SessionLocal()
    try:
        return [g.to_dict() for g in db.query(StudyGroup).all()]
    finally:
        db.close()


def get_user_groups(user_id: int) -> List[dict]:
    db = SessionLocal()
    try:
        user = db.query(User).filter(User.id == user_id).first()
        return [g.to_dict() for g in user.groups] if user else []
    finally:
        db.close()


# ── Task CRUD ─────────────────────────────────────────────────────────────────

def get_group_tasks(group_id: int) -> List[dict]:
    db = SessionLocal()
    try:
        return [t.to_dict() for t in
                db.query(WorkspaceTask).filter(WorkspaceTask.group_id == group_id).all()]
    finally:
        db.close()


def add_group_task(
    group_id: int,
    title: str,
    priority: str = "Medium",
    due_date=None,
    assigned_to: int = None,
    description: str = "",
) -> bool:
    db = SessionLocal()
    try:
        db.add(WorkspaceTask(
            group_id=group_id,
            title=title,
            priority=priority,
            due_date=due_date,
            assigned_to=assigned_to or None,
            description=description,
        ))
        db.commit()
        return True
    except Exception as e:
        db.rollback()
        print(f"Error adding task: {e}")
        return False
    finally:
        db.close()


def update_task(
    task_id: int,
    title: str = None,
    description: str = None,
    priority: str = None,
    due_date=None,
    assigned_to: int = None,
    clear_due: bool = False,
    clear_assignee: bool = False,
) -> bool:
    """Update any combination of task fields. Use clear_due/clear_assignee to set those to None."""
    db = SessionLocal()
    try:
        task = db.query(WorkspaceTask).filter(WorkspaceTask.id == task_id).first()
        if not task:
            return False
        if title is not None:
            task.title = title
        if description is not None:
            task.description = description
        if priority is not None:
            task.priority = priority
        if due_date is not None:
            task.due_date = due_date
        if clear_due:
            task.due_date = None
        if assigned_to is not None:
            task.assigned_to = assigned_to
        if clear_assignee:
            task.assigned_to = None
        db.commit()
        return True
    except Exception as e:
        db.rollback()
        print(f"Error updating task: {e}")
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
        print(f"Error updating task status: {e}")
        return False
    finally:
        db.close()


def get_group_member_names(group_id: int) -> List[dict]:
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


# ── Weight Preferences ────────────────────────────────────────────────────────

def save_user_weights(user_id: int, weights: dict) -> bool:
    db = SessionLocal()
    try:
        row = db.query(UserWeights).filter(UserWeights.user_id == user_id).first()
        if row:
            row.weights_json = json.dumps(weights)
            row.updated_at = datetime.utcnow()
        else:
            db.add(UserWeights(user_id=user_id, weights_json=json.dumps(weights)))
        db.commit()
        return True
    except Exception as e:
        db.rollback()
        print(f"Error saving weights: {e}")
        return False
    finally:
        db.close()


def get_user_weights(user_id: int) -> dict:
    db = SessionLocal()
    try:
        row = db.query(UserWeights).filter(UserWeights.user_id == user_id).first()
        return json.loads(row.weights_json) if row and row.weights_json else {}
    finally:
        db.close()


# ── Study Session CRUD ────────────────────────────────────────────────────────

def create_study_session(
    group_id: int,
    day: str,
    time_slot: str,
    scheduled_date: datetime = None,
    notes: str = "",
    created_by: int = None,
) -> int:
    db = SessionLocal()
    try:
        session = StudySession(
            group_id=group_id,
            day=day,
            time_slot=time_slot,
            scheduled_date=scheduled_date,
            notes=notes,
            created_by=created_by,
            status='Proposed',
        )
        db.add(session)
        db.commit()
        return session.id
    except Exception as e:
        db.rollback()
        print(f"Error creating session: {e}")
        return -1
    finally:
        db.close()


def get_group_sessions(group_id: int) -> List[dict]:
    db = SessionLocal()
    try:
        return [s.to_dict() for s in
                db.query(StudySession).filter(StudySession.group_id == group_id)
                .order_by(StudySession.created_at.desc()).all()]
    finally:
        db.close()


def update_session_status(session_id: int, status: str) -> bool:
    db = SessionLocal()
    try:
        s = db.query(StudySession).filter(StudySession.id == session_id).first()
        if s:
            s.status = status
            db.commit()
            return True
        return False
    except Exception as e:
        db.rollback()
        print(f"Error updating session: {e}")
        return False
    finally:
        db.close()


# ── Activity Log ──────────────────────────────────────────────────────────────

def log_activity(user_id: int, event_type: str, payload: dict = None) -> None:
    db = SessionLocal()
    try:
        db.add(UserActivity(
            user_id=user_id,
            event_type=event_type,
            payload=json.dumps(payload or {}),
        ))
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
