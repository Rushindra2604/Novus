# Novus — AI-Powered Resume Intelligence & Career Platform

Novus is an AI-powered career platform designed to help freshers create ATS-friendly resumes, analyze resumes against job descriptions, identify skill and keyword gaps, and improve resume content using AI-assisted suggestions.

The project combines a resume-building workflow with an ATS analysis engine and Gemini-powered content improvement features.

---

## 🚀 Features

### Resume Studio

- Create and manage resumes
- Live resume preview
- ATS-friendly resume structure
- Resume sections with dynamic editing
- Automatic draft saving
- Resume completion tracking
- Support for multiple resumes

### ATS Resume Analyzer

- Analyze a resume against a job description
- Calculate an ATS match score
- Required skill matching
- Technical keyword matching
- Responsibility matching
- Practical experience analysis
- Education matching
- Preferred skill analysis
- Resume formatting and parseability analysis

### Gap Analysis

Novus identifies areas where the resume does not sufficiently match the target job description.

The analysis can highlight:

- Missing skills
- Missing keywords
- Responsibility gaps
- Experience gaps
- Education gaps
- Priority levels for identified gaps

### AI-Powered Improvements

Gemini AI is integrated into the ATS workflow to provide contextual resume improvement suggestions.

Users can:

- Generate AI suggestions
- Review suggested improvements
- Apply an improvement
- Try another suggestion
- Keep the original content

### Analysis History

- Save ATS analyses
- View previous analyses
- Reopen historical reports
- Restore previous analysis results
- Compare resume improvement progress over time

### Dashboard

The dashboard provides an overview of:

- Resumes
- Resume completion
- ATS analyses
- ATS performance
- Recent resume activity

### Authentication

- User registration
- User login
- Password hashing
- Session-based authentication
- Input validation

---

## 🧠 ATS Analysis Architecture

The ATS system follows a modular analysis pipeline:

```text
Resume
   │
   ▼
Resume Parser
   │
   ▼
Job Description Parser
   │
   ▼
Keyword Matching
   │
   ▼
Responsibility Matching
   │
   ▼
Gap Analysis
   │
   ▼
ATS Scoring Engine
   │
   ▼
AI Validation
   │
   ▼
Gemini AI Improvements
   │
   ▼
Final ATS Report