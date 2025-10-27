# ...existing code...
from django.core.management.base import BaseCommand
from django.core.files.uploadedfile import SimpleUploadedFile
import pandas as pd
from sports.models import Player, Team
from django.conf import settings
import os
from django.db import transaction
from django.db.models import Q
import shutil # Import shutil for file copying

class Command(BaseCommand):
    help = "Faster Excel import with bulk ops. Options: --file, --sheet, --media-subdir, --dry-run, --skip-images, --bulk, --batch-size"

    def add_arguments(self, parser):
        parser.add_argument('--file', '-f', default='data.xlsx')
        parser.add_argument('--sheet', '-s', default=0)
        parser.add_argument('--media-subdir', '-m', default='players/photos')
        parser.add_argument('--dry-run', action='store_true', help='Parse and validate only; do not write to DB or save files')
        parser.add_argument('--skip-images', action='store_true', help='Do not process or attach photos')
        parser.add_argument('--bulk', action='store_true', help='Use bulk_create for new players and bulk_update for updates (photos still saved per-instance)')
        parser.add_argument('--batch-size', type=int, default=500, help='Batch size for bulk operations')

    def handle(self, *args, **options):
        filepath = options['file']
        sheet = options['sheet']
        media_subdir = options['media_subdir']
        dry_run = options['dry_run']
        skip_images = options['skip_images']
        use_bulk = options['bulk']
        batch_size = options['batch_size']

        if not os.path.exists(filepath):
            self.stdout.write(self.style.ERROR(f"Excel file not found: {filepath}"))
            return

        try:
            df = pd.read_excel(filepath, sheet_name=sheet, dtype=object)
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"Failed to read Excel: {e}"))
            return

        df = df.where(pd.notnull(df), None)

        def as_str(v):
            return None if v is None else str(v).strip()

        def as_int(v):
            if v is None:
                return None
            try:
                if isinstance(v, float) and v.is_integer():
                    return int(v)
                return int(v)
            except Exception:
                return None

        def as_bool(v):
            if v is None:
                return False
            if isinstance(v, bool):
                return v
            return str(v).strip().lower() in ('1', 'true', 'yes', 'y', 't')

        def photo_file_for(photo_name, team_name=None):
            if not photo_name:
                return None
            pn = str(photo_name).strip()
            candidates = []
            if team_name:
                candidates.append(os.path.join(settings.MEDIA_ROOT, media_subdir, team_name, pn))
            candidates.append(os.path.join(settings.MEDIA_ROOT, media_subdir, pn))
            candidates.append(os.path.join(settings.MEDIA_ROOT, pn))
            for path in candidates:
                if path and os.path.exists(path):
                    return path
            return None

        # Prepare rows
        rows = []
        for idx, row in df.iterrows():
            first = as_str(row.get('first_name') or row.get('First name') or row.get('firstname'))
            last = as_str(row.get('last_name') or row.get('Last name') or row.get('lastname'))
            if not first and not last:
                self.stdout.write(self.style.WARNING(f"Row {idx+1}: missing both names; skipping"))
                continue
            team_raw = as_str(row.get('team') or row.get('Team')) or 'Unassigned'
            rows.append({
                'idx': idx + 1,
                'first_name': first or '',
                'last_name': last or '',
                'team_name': team_raw,
                'position': as_str(row.get('position')) or '',
                'year': as_int(row.get('year_group') or row.get('year')),
                'is_captain': as_bool(row.get('is_captain') or row.get('captain')),
                'shirt_number': as_int(row.get('kit_number') or row.get('shirt_number') or row.get('kit')),
                'quote': as_str(row.get('quote') or row.get('player_quote') or row.get('Quote')),
                'photo_raw': row.get('photo') or row.get('photo_filename') or row.get('Photo')
            })

        if not rows:
            self.stdout.write(self.style.WARNING("No valid rows to import"))
            return

        # Preload teams and existing players (minimises queries)
        team_names = set(r['team_name'] for r in rows)
        existing_teams = {t.name: t for t in Team.objects.filter(name__in=team_names)}
        # create missing teams if not dry-run
        missing_teams = [name for name in team_names if name not in existing_teams]
        if missing_teams and not dry_run:
            Team.objects.bulk_create([Team(name=n) for n in missing_teams])
            existing_teams.update({t.name: t for t in Team.objects.filter(name__in=team_names)})

        # Build lookup for players by (team_id, first_name, last_name)
        # Query existing players matching any of the teams to reduce DB hits
        team_ids = [existing_teams[n].id for n in existing_teams]
        existing_players_qs = Player.objects.filter(team_id__in=team_ids)
        existing_map = { (p.team_id, p.first_name.strip(), p.last_name.strip()): p for p in existing_players_qs }

        to_create = []
        to_update = []
        attach_photos = []  # tuples of (player_instance, source_photo_path, photo_name)
        created = updated = 0

        # Prepare model instances (not saved yet)
        for r in rows:
            team = existing_teams.get(r['team_name'])
            key = (team.id, r['first_name'], r['last_name'])
            existing = existing_map.get(key)
            if existing:
                # detect whether any of the updatable fields changed
                changed = False
                if existing.position != r['position']:
                    existing.position = r['position']
                    changed = True
                if (existing.year != r['year']):
                    existing.year = r['year']
                    changed = True
                if existing.is_captain != r['is_captain']:
                    existing.is_captain = r['is_captain']
                    changed = True
                if existing.shirt_number != r['shirt_number']:
                    existing.shirt_number = r['shirt_number']
                    changed = True
                if r['quote'] and (existing.quote != r['quote']):
                    existing.quote = r['quote']
                    changed = True
                if changed:
                    to_update.append(existing)
                # photo handling (attach if provided and not skipped)
                if r['photo_raw'] and not skip_images:
                    path = photo_file_for(r['photo_raw'], team_name=r['team_name'])
                    if path:
                        attach_photos.append((existing, path, os.path.basename(path)))
            else:
                # build new instance
                p = Player(
                    team=team,
                    first_name=r['first_name'],
                    last_name=r['last_name'],
                    position=r['position'],
                    year=r['year'],
                    is_captain=r['is_captain'],
                    shirt_number=r['shirt_number'],
                )
                if r['quote']:
                    p.quote = r['quote']
                to_create.append( (p, r) )  # keep row for photo later

        if dry_run:
            self.stdout.write(self.style.SUCCESS(f"Dry-run: {len(to_create)} to create, {len(to_update)} to update, {len(attach_photos)} photos to attach"))
            return

        # Perform DB writes
        with transaction.atomic():
            # bulk create new players in batches
            if to_create:
                if use_bulk:
                    for i in range(0, len(to_create), batch_size):
                        batch = [t[0] for t in to_create[i:i+batch_size]]
                        Player.objects.bulk_create(batch, batch_size=batch_size)
                    # need to refresh created instances to attach photos (query by recently created values)
                    # simple approach: query by team and names in created list
                    created_keys = [(p.team.id, p.first_name, p.last_name) for p,_ in to_create]
                    qs = Player.objects.filter(
                        Q()
                    )
                    # build Q to filter created players (construct ORs)
                    q = Q(pk__in=[])
                    created_lookup = []
                    for team_id, fn, ln in created_keys:
                        created_lookup.append(Q(team_id=team_id, first_name=fn, last_name=ln))
                    if created_lookup:
                        q = created_lookup.pop(0)
                        for qq in created_lookup:
                            q |= qq
                        qs = Player.objects.filter(q)
                    created_list = list(qs)
                    existing_map.update({ (p.team_id, p.first_name, p.last_name): p for p in created_list })
                    created = len(created_list)
                else:
                    # save individually so photos can be attached to instance immediately
                    for p, r in to_create:
                        p.save()
                        created += 1
                        if r['photo_raw'] and not skip_images:
                            path = photo_file_for(r['photo_raw'], team_name=r['team_name'])
                            if path:
                                attach_photos.append((p, path, os.path.basename(path)))

            # bulk update changed existing players (exclude photo/quote which we've already applied to model attributes)
            if to_update and use_bulk:
                # choose fields to update
                fields = ['position', 'year', 'is_captain', 'shirt_number', 'quote']
                for i in range(0, len(to_update), batch_size):
                    Player.objects.bulk_update(to_update[i:i+batch_size], fields, batch_size=batch_size)
                updated = len(to_update)
            elif to_update:
                for p in to_update:
                    p.save()
                    updated += 1

            # attach photos (per-instance save required)
            for inst, source_photo_path, photo_name in attach_photos:
                try:
                    # Simply copy the file from source to the location Django expects
                    # This avoids opening and re-saving the image, preserving original size/format
                    destination_path = os.path.join(settings.MEDIA_ROOT, inst.photo.field.upload_to, photo_name)
                    
                    # Ensure the destination directory exists
                    os.makedirs(os.path.dirname(destination_path), exist_ok=True)
                    
                    # Copy the file
                    shutil.copy2(source_photo_path, destination_path) # Use copy2 to preserve metadata if possible
                    
                    # Set the photo field on the instance to the new filename
                    # Django will handle the path relative to MEDIA_ROOT internally
                    inst.photo.name = os.path.relpath(destination_path, settings.MEDIA_ROOT).replace('\\', '/') # Ensure forward slashes for URLs
                    inst.save(update_fields=['photo']) # Save only the photo field to update the database reference
                    
                except Exception as e:
                    self.stdout.write(self.style.WARNING(f"Failed to attach photo for {inst.first_name} {inst.last_name} from {source_photo_path}: {e}"))

        self.stdout.write(self.style.SUCCESS(f"Import finished: {created} created, {updated} updated, {len(attach_photos)} photos attempted"))
# ...existing code...