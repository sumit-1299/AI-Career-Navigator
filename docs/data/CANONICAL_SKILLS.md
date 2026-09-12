# Canonical Skills

## Purpose

The canonical skill layer provides a unified representation
of skills used across multiple data sources.

It acts as the central link between:

- Occupational knowledge
- University curricula
- Student skills
- Learning resources
- Professional certifications
- Job-market information

## Problem

Different sources may represent the same skill using different
names or terminology.

Examples may include:

- Python
- Python Programming
- Python Language

Therefore, source terminology must not be directly treated as
a unique skill.

## Approach

Source-specific skill names will first be preserved.

They will then pass through:

1. Normalization
2. Duplicate detection
3. Alias identification
4. Controlled validation
5. Canonical skill assignment

## Principle

Raw source terminology must be preserved.

Canonical skills must not overwrite source-specific information.

## Example

Source terminology:

Python Programming

Canonical skill:

Python

The relationship between the source terminology and canonical
skill will be stored separately.
