"""CLI: freeze cached jobs, reconcile blind reviews, and compare shipped matchers."""
import argparse
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from services.research_evaluation import (ROOT, KEYS, digest, load_json, make_live_dataset,
    markdown_report, now_iso, reconcile, run_evaluation, seal_dataset, text_digest,
    validate_dataset, write_new_json)
from services.semantic_encoder import SemanticUnavailable


def export_cache(args):
    # Use a direct read-only query, not app.create_app() (which creates tables).
    from sqlalchemy import create_engine, select
    from config import Config
    from models.live_job import LiveJob
    from services.live_jobs import BOARDS, is_stale
    from models.assessment_attempt import iso_utc
    if not Config.SQLALCHEMY_DATABASE_URI:
        raise ValueError('Configure your private backend/.env DATABASE_URL first.')
    engine = create_engine(Config.SQLALCHEMY_DATABASE_URI)
    try:
        with engine.connect() as connection:
            rows = connection.execute(select(LiveJob.__table__).where(
                LiveJob.listed.is_(True), LiveJob.board.in_(BOARDS))).mappings().all()
            records = []
            for row in rows:
                record = dict(row)
                record.update(provider='greenhouse', employer=BOARDS[row['board']],
                              last_seen_at=iso_utc(row['last_seen_at']), stale=is_stale(row['last_seen_at']))
                records.append(record)
    except Exception as exc:
        raise ValueError('Could not read the live-job cache. Check PostgreSQL and backend/.env, then refresh the boards in the app.') from exc
    finally:
        engine.dispose()
    dataset = make_live_dataset(records, size=args.size, seed=args.seed)
    write_new_json(args.out, dataset)
    print(f"Frozen {len(dataset['cases'])} jobs. No model or candidate data was used.")
    print(f"Dataset: {args.out}")
    print(f"Employer counts: {dataset['selection']['employer_counts']}")
    print(f"Stale cases: {dataset['selection']['stale_case_count']}; inspect source timestamps before review.")
    print('Open research/review.html and load this packet. Obtain two independent reviews before evaluation.')


def create_adjudication(args):
    dataset = validate_dataset(load_json(args.dataset))
    a, b = load_json(args.review_a), load_json(args.review_b)
    _, disagreements, agreement = reconcile(dataset, a, b)
    print(f"Agreement: {agreement['raw_agreement']:.1%}; disputed cells: {agreement['disputed_cells']}.")
    if not disagreements:
        print('No disagreements. Evaluate using the two original review files; no adjudication file is needed.')
        return
    write_new_json(args.out, {'schema_version': 'career-skill-adjudication-packet-v1',
        'dataset': dataset, 'created_at': now_iso(), 'parent_review_hashes': [digest(a), digest(b)],
        'reviewer_ids': [a['reviewer_id'], b['reviewer_id']], 'disagreements': disagreements})
    print(f'Adjudication packet: {args.out}. A third reviewer opens it in research/review.html.')


def save_run(directory, report):
    directory = Path(directory)
    directory.mkdir(parents=True, exist_ok=False)
    write_new_json(directory / 'results.json', report)
    (directory / 'report.md').write_text(markdown_report(report), encoding='utf-8')
    print(f"Report: {directory / 'report.md'}")
    print(f"Audit details: {directory / 'results.json'}")
    if report['dataset_kind'] == 'synthetic_smoke':
        print('SMOKE TEST ONLY: AI-authored synthetic labels, not research results.')
    else:
        print(f"Completed {report['split']} extraction pilot on {report['case_count']} jobs. Read coverage and limitations before interpreting F1.")


def evaluate(args):
    if Path(args.out).exists():
        raise ValueError('Output directory already exists. Choose a new run directory to preserve the earlier result.')
    dataset = validate_dataset(load_json(args.dataset))
    if dataset['kind'] != 'live_job_pilot':
        raise ValueError('Use smoke for synthetic checks; research evaluation requires a live-job packet.')
    a, b = load_json(args.review_a), load_json(args.review_b)
    adjudication = load_json(args.adjudication) if args.adjudication else None
    gold, disagreements, agreement = reconcile(dataset, a, b, adjudication)
    if disagreements:
        raise ValueError(f"{len(disagreements)} cases have unresolved reviewer disagreements. Run prepare-adjudication before evaluation.")
    hashes = [digest(a), digest(b)] + ([digest(adjudication)] if adjudication else [])
    reference = 'two_self_attested_independent_reviews' + ('_plus_third_reviewer_adjudication' if adjudication else '')
    report = run_evaluation(dataset, gold, args.split, agreement, hashes, reference_status=reference)
    save_run(args.out, report)


def synthetic_packet():
    fixture = load_json(ROOT / 'research' / 'synthetic_smoke.json')
    cases, gold = [], {}
    for i, row in enumerate(fixture['cases']):
        cases.append({'id': row['id'], 'group_id': row['id'],
                      'split': 'development' if i < len(fixture['cases']) // 2 else 'test',
                      'title': row['title'], 'description': row['description'],
                      'text_sha256': text_digest(row['description']), 'source': {'type': 'AI-authored synthetic example'}})
        gold[row['id']] = {key: 'present' if key in row['expected_skills'] else 'absent' for key in KEYS}
    return seal_dataset(cases, {'method': 'AI-authored fixed smoke fixtures; development examples, not held-out research'}, kind='synthetic_smoke'), gold


def smoke(args):
    if Path(args.out).exists():
        raise ValueError('Output directory already exists; choose a new smoke output directory.')
    dataset, gold = synthetic_packet()
    report = run_evaluation(dataset, gold, 'development', reference_status='AI-authored synthetic smoke references')
    # Both halves are available for exercising review UI; neither is independent research data.
    save_run(args.out, report)
    write_new_json(Path(args.out) / 'practice-packet.json', dataset)
    print('Optional UI practice packet created. Practice reviews cannot be used by the research evaluate command.')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest='command', required=True)
    export = commands.add_parser('export', help='Freeze engineering-related postings already cached by the app')
    export.add_argument('--size', type=int, default=24)
    export.add_argument('--seed', default='career-pilot-2026-09-v1')
    export.add_argument('--out', default='data/research/pilot-v1.json')
    export.set_defaults(run=export_cache)
    smoke_parser = commands.add_parser('smoke', help='Run labelled synthetic checks; never research evidence')
    smoke_parser.add_argument('--out', default='data/research/smoke-v1')
    smoke_parser.set_defaults(run=smoke)
    for name, function in [('prepare-adjudication', create_adjudication), ('evaluate', evaluate)]:
        sub = commands.add_parser(name)
        sub.add_argument('--dataset', required=True)
        sub.add_argument('--review-a', required=True)
        sub.add_argument('--review-b', required=True)
        sub.add_argument('--out', required=True)
        if name == 'evaluate':
            sub.add_argument('--adjudication')
            sub.add_argument('--split', choices=['development', 'test'], required=True)
        sub.set_defaults(run=function)
    args = parser.parse_args()
    try:
        args.run(args)
    except (ValueError, TypeError, KeyError, OSError, SemanticUnavailable) as exc:
        parser.exit(2, f'Cannot complete evaluation step: {exc}\n')


if __name__ == '__main__':
    main()
