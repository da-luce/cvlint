# 📝 cvlint

A tool for linting your [curriculum vitae](https://en.wikipedia.org/wiki/Curriculum_vitae)! Validates PDF resumes against quality criteria to ensure they meet professional standards.

![Screenshot Example](https://daluce-cvlint-assets.s3.us-east-2.amazonaws.com/screenshot.png)

## What is cvlint?

cvlint helps you create better resumes by automatically checking your PDF against common best practices and requirements. It validates everything from file size and formatting to spelling and structure, giving you a score and detailed feedback on what needs improvement.

## Installation

Install cvlint using Poetry:

```bash
poetry install
```

## Quick Start

Validate your resume PDF:

```bash
cvlint check my-resume.pdf
```

This will run all validation criteria and show you a detailed report with your score.

## Commands

### `check`

Validate a PDF resume against quality criteria.

```bash
cvlint check resume.pdf
cvlint check resume.pdf --passing-score 90
cvlint check resume.pdf --output json
cvlint check resume.pdf --criteria "PDF File Exists,Single Page Limit"
```

### `list-criteria`

Display all available validation criteria with their weights and descriptions.

```bash
cvlint list-criteria
```

### `config`

Show current configuration values.

```bash
cvlint config
```

## Exit Codes

- `0`: Success (score meets passing threshold)
- `1`: Failure (score below passing threshold or error occurred)

This makes cvlint perfect for use in CI/CD pipelines to automatically validate resumes.
