import os
import json
import shutil
import random
import string
from datetime import datetime
from pathlib import Path

class Project:
    def __init__(self, project_id, name, root_path):
        self.id = project_id
        self.name = name
        self.root_path = Path(root_path)
        self.folders = {
            'source': self.root_path / 'source_files',
            'processed': self.root_path / 'processed_files',
            'exports': self.root_path / 'exports',
            'ai_analysis': self.root_path / 'ai_analysis',
            'trash': self.root_path / '.trash',
            'backups': self.root_path / 'backups'
        }
        self.created_at = datetime.now().isoformat()
        self.last_opened = None

    def create_folders(self):
        self.root_path.mkdir(parents=True, exist_ok=True)
        for folder in self.folders.values():
            folder.mkdir(exist_ok=True)

    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'root_path': str(self.root_path),
            'created_at': self.created_at,
            'last_opened': self.last_opened
        }

    @staticmethod
    def from_dict(data):
        proj = Project(data['id'], data['name'], data['root_path'])
        proj.created_at = data['created_at']
        proj.last_opened = data.get('last_opened')
        return proj

class ProjectManager:
    def __init__(self, base_dir=None):
        if base_dir is None:
            base_dir = Path.home() / "decisiona_projects"
        self.base_dir = Path(base_dir)
        self.base_dir.mkdir(exist_ok=True)
        self.index_file = self.base_dir / "projects_index.json"
        self.projects = {}
        self.active_project = None
        self._load_index()

    def _load_index(self):
        if self.index_file.exists():
            with open(self.index_file, 'r') as f:
                data = json.load(f)
                for pid, pdata in data.get('projects', {}).items():
                    self.projects[pid] = Project.from_dict(pdata)
                active_id = data.get('active')
                if active_id and active_id in self.projects:
                    self.active_project = self.projects[active_id]
        else:
            self._save_index()

    def _save_index(self):
        data = {
            'projects': {pid: p.to_dict() for pid, p in self.projects.items()},
            'active': self.active_project.id if self.active_project else None
        }
        with open(self.index_file, 'w') as f:
            json.dump(data, f, indent=2)

    def generate_project_id(self):
        today = datetime.now().strftime("%y%m%d")
        letters = ''.join(random.choices(string.ascii_uppercase, k=3))
        digits = ''.join(random.choices(string.digits, k=4))
        return f"PRJ-{today}-{letters}-{digits}"

    def create_project(self, name):
        if len(name) > 100:
            raise ValueError("Project name too long (max 100 chars)")
        proj_id = self.generate_project_id()
        while proj_id in self.projects:
            proj_id = self.generate_project_id()
        root = self.base_dir / proj_id
        proj = Project(proj_id, name, root)
        proj.create_folders()
        self.projects[proj_id] = proj
        self._save_index()
        return proj

    def set_active_project(self, project_id):
        if project_id in self.projects:
            self.active_project = self.projects[project_id]
            self.active_project.last_opened = datetime.now().isoformat()
            self._save_index()
            return True
        return False

    def get_project_list(self):
        projects = list(self.projects.values())
        projects.sort(key=lambda p: p.last_opened or p.created_at, reverse=True)
        return projects

    def delete_project(self, project_id):
        if project_id in self.projects:
            proj = self.projects[project_id]
            shutil.rmtree(proj.root_path, ignore_errors=True)
            del self.projects[project_id]
            if self.active_project and self.active_project.id == project_id:
                self.active_project = None
            self._save_index()
            return True
        return False