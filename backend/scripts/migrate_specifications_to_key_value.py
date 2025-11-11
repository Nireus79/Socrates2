#!/usr/bin/env python3
"""
Migrate Specification table from content-only to key-value structure.

This script:
1. Reads all specifications from the database
2. Intelligently extracts key and value from content based on category
3. Updates specifications with extracted key/value pairs
4. Validates results
5. Generates migration report

Usage:
    cd backend
    python scripts/migrate_specifications_to_key_value.py [--dry-run] [--sample]

Flags:
    --dry-run   Show what would be migrated without making changes
    --sample    Only process first 50 specs (for testing)

Author: Socrates Migration System
Date: November 10, 2025
"""

import sys
import os
import re
import argparse
from pathlib import Path

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.core.database import SessionLocalSpecs
from app.models.specification import Specification


def extract_key_value(content: str, category: str) -> tuple[str, str]:
    """
    Intelligently extract key and value from content based on category.

    Args:
        content: Raw specification content
        category: Specification category (goals, requirements, tech_stack, etc.)

    Returns:
        Tuple of (key, value)

    Examples:
        extract_key_value("FastAPI web framework", "tech_stack")
        → ("api_framework", "FastAPI")

        extract_key_value("Support 10k concurrent users", "scalability")
        → ("concurrent_users_target", "10k concurrent users")
    """
    if not content:
        return (f"unspecified_{category}", "")

    content = content.strip()

    # Strategy 1: Structured data with colon (key: value)
    if ':' in content:
        parts = content.split(':', 1)
        key_part = parts[0].strip()
        value_part = parts[1].strip() if len(parts) > 1 else content

        # Convert key to snake_case
        key = key_part.lower().replace(' ', '_')
        key = ''.join(c for c in key if c.isalnum() or c == '_')

        return (key, value_part)

    # Strategy 2: Category-specific extraction

    if category == 'tech_stack':
        # For tech stack, first 2-3 words are the technology
        words = content.split()[:3]
        value = ' '.join(words)
        key = f"tech_{words[0].lower()}" if words else f"{category}_unspecified"

    elif category == 'scalability' or category == 'performance':
        # Extract metrics and targets
        # Look for numbers and units
        match = re.search(r'(\d+[kmbt]?)\s*([a-zA-Z\s]*)', content)
        if match:
            value = f"{match.group(1)} {match.group(2)}".strip()
        else:
            # Take first 5-7 words
            words = content.split()[:6]
            value = ' '.join(words)

        # Generate key from first meaningful words
        key_words = value.split()[:2]
        key = '_'.join(key_words).lower()

    elif category == 'security':
        # Extract security requirement
        # Look for patterns like "JWT", "OAuth2", "TLS", "AES-256"
        words = content.split()[:4]
        value = ' '.join(words)
        key = f"security_{words[0].lower()}" if words else f"{category}_unspecified"

    elif category == 'requirements':
        # Extract requirement statement
        # Look for "should", "must", "needs" patterns
        match = re.search(r'(?:should|must|needs?)\s+(.+?)(?:\.|,|$)', content)
        if match:
            value = match.group(1).strip()
        else:
            value = content[:100]  # First 100 chars

        # Generate key from value
        value_words = value.split()[:3]
        key = '_'.join(value_words).lower()

    elif category == 'testing' or category == 'monitoring':
        # Extract percentage, targets, metrics
        match = re.search(r'(\d+%|\d+[kmbt]?|[\w\s]+)(?:minimum|target|threshold|required)?', content)
        if match:
            value = match.group(1).strip()
        else:
            words = content.split()[:5]
            value = ' '.join(words)

        key = f"{category}_target"

    elif category == 'data_retention' or category == 'disaster_recovery':
        # Extract retention periods or DR metrics
        match = re.search(r'(\d+\s*(?:year|month|day|hour|minute|second)s?)', content)
        if match:
            value = match.group(1).strip()
        else:
            words = content.split()[:5]
            value = ' '.join(words)

        key = f"{category}_policy"

    else:
        # Default: Extract first meaningful phrase
        for delimiter in ['. ', ', ', ' and ', ' or ']:
            if delimiter in content:
                value = content.split(delimiter)[0].strip()
                break
        else:
            words = content.split()[:5]
            value = ' '.join(words)

        # Generate key from category and first word
        value_words = value.split()[:2]
        key = '_'.join(value_words).lower() if value_words else category

    # Clean up key
    key = re.sub(r'[^a-z0-9_]', '', key)
    key = key[:50] if key else f"spec_{category}"

    # Clean up value
    value = value.strip()
    if len(value) > 1000:
        value = value[:1000]

    return (key, value)


def migrate_specifications(dry_run=False, sample=False):
    """
    Migrate specifications from content-only to key-value structure.

    Args:
        dry_run: If True, show changes without applying them
        sample: If True, only process first 50 specs (for testing)
    """
    db = SessionLocalSpecs()

    try:
        # Get all specifications
        query = db.query(Specification)
        total_specs = query.count()

        print(f"\n{'='*80}")
        print(f"Specification Key/Value Migration")
        print(f"{'='*80}")
        print(f"Total specifications in database: {total_specs}")
        print(f"Dry run: {dry_run}")
        print(f"Sample mode (first 50): {sample}")
        print()

        # Apply sample limit if requested
        if sample:
            query = query.limit(50)

        specs = query.all()
        print(f"Processing: {len(specs)} specifications\n")

        # Track statistics
        stats = {
            'total': len(specs),
            'with_content': 0,
            'already_has_key': 0,
            'migrated': 0,
            'skipped': 0,
            'errors': []
        }

        # Process each specification
        for i, spec in enumerate(specs, 1):
            try:
                # Skip if already has key/value
                if spec.key and spec.value:
                    stats['already_has_key'] += 1
                    continue

                # Skip if no content
                if not spec.content:
                    stats['skipped'] += 1
                    continue

                stats['with_content'] += 1

                # Extract key and value
                key, value = extract_key_value(spec.content, spec.category)

                # Show sample of what would be migrated
                if i <= 10 or i % 100 == 0:
                    print(f"[{i}/{len(specs)}] Spec ID: {spec.id}")
                    print(f"  Category: {spec.category}")
                    print(f"  Content: {spec.content[:60]}...")
                    print(f"  → Key: {key}")
                    print(f"  → Value: {value[:60]}...")
                    print()

                # Apply migration if not dry-run
                if not dry_run:
                    spec.key = key
                    spec.value = value
                    db.add(spec)

                stats['migrated'] += 1

            except Exception as e:
                stats['errors'].append({
                    'spec_id': spec.id,
                    'error': str(e)
                })
                print(f"  ERROR processing spec {spec.id}: {e}")
                continue

        # Commit if not dry-run
        if not dry_run and stats['migrated'] > 0:
            db.commit()
            print(f"\n✓ Committed {stats['migrated']} specifications to database")
        elif dry_run:
            print(f"\n[DRY RUN] Would migrate {stats['migrated']} specifications (not committed)")
            db.rollback()

        # Print summary
        print(f"\n{'='*80}")
        print(f"Migration Summary")
        print(f"{'='*80}")
        print(f"Total processed:      {stats['total']}")
        print(f"With content:         {stats['with_content']}")
        print(f"Already have key:     {stats['already_has_key']}")
        print(f"Migrated:             {stats['migrated']}")
        print(f"Skipped (no content): {stats['skipped']}")
        print(f"Errors:               {len(stats['errors'])}")

        if stats['errors']:
            print(f"\nErrors:")
            for err in stats['errors']:
                print(f"  - Spec {err['spec_id']}: {err['error']}")

        print(f"\n{'='*80}\n")

        return stats['migrated'] > 0

    finally:
        db.close()


def validate_migration():
    """
    Validate that migration was successful.
    """
    db = SessionLocalSpecs()

    try:
        print(f"{'='*80}")
        print(f"Validation Report")
        print(f"{'='*80}\n")

        # Check 1: All specs have key and value
        all_specs = db.query(Specification).count()
        specs_with_key = db.query(Specification).filter(Specification.key != None).count()
        specs_with_value = db.query(Specification).filter(Specification.value != None).count()

        print(f"Key/Value Coverage:")
        print(f"  Total specs:        {all_specs}")
        print(f"  With key:           {specs_with_key} ({specs_with_key*100/all_specs:.1f}%)")
        print(f"  With value:         {specs_with_value} ({specs_with_value*100/all_specs:.1f}%)")

        if specs_with_key == specs_with_value and specs_with_key == all_specs:
            print(f"  ✓ All specs have key and value\n")
        else:
            print(f"  ✗ Some specs are missing key or value\n")

        # Check 2: Sample recent specs
        print(f"Sample of Recent Specifications:")
        recent = db.query(Specification)\
            .filter(Specification.key != None)\
            .order_by(Specification.created_at.desc())\
            .limit(5).all()

        for i, spec in enumerate(recent, 1):
            print(f"  {i}. [{spec.category}] key='{spec.key}' value='{spec.value[:50]}...'")

        print(f"\n{'='*80}\n")

    finally:
        db.close()


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description='Migrate Specification table to key/value structure'
    )
    parser.add_argument('--dry-run', action='store_true',
                       help='Show what would be migrated without making changes')
    parser.add_argument('--sample', action='store_true',
                       help='Only process first 50 specs (for testing)')
    parser.add_argument('--validate', action='store_true',
                       help='Only validate existing migration')

    args = parser.parse_args()

    if args.validate:
        validate_migration()
    else:
        migrate_specifications(dry_run=args.dry_run, sample=args.sample)
        if not args.dry_run:
            validate_migration()


if __name__ == '__main__':
    main()
