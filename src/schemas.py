from typing import List, Optional

from pydantic import BaseModel, Field


class EducationItem(BaseModel):
    degree: Optional[str] = None
    institution: Optional[str] = None
    graduation_year: Optional[str] = None


class ExperienceItem(BaseModel):
    title: Optional[str] = None
    company: Optional[str] = None
    duration: Optional[str] = None
    responsibilities: List[str] = Field(default_factory=list)


class ProjectItem(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    technologies: List[str] = Field(default_factory=list)


class ResumeProfile(BaseModel):
    candidate_name: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    location: Optional[str] = None
    department: Optional[str] = None
    summary: Optional[str] = None
    total_experience_years: Optional[float] = None
    skills: List[str] = Field(default_factory=list)
    tools: List[str] = Field(default_factory=list)
    certifications: List[str] = Field(default_factory=list)
    education: List[EducationItem] = Field(default_factory=list)
    experience: List[ExperienceItem] = Field(default_factory=list)
    projects: List[ProjectItem] = Field(default_factory=list)
