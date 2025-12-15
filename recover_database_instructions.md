# Database Recovery Instructions

## What Happened?
Your database was modified today (November 20, 2025 at 6:37 PM) and all bank accounts were lost.

## Recovery Options:

### Option 1: OneDrive Version History (RECOMMENDED)
Since your database is in OneDrive, you can restore a previous version:

1. **Right-click on `pennywise.db`** in File Explorer
2. Select **"Version history"** or **"Restore previous versions"**
3. OneDrive will show a list of previous versions
4. Select a version from **BEFORE** November 20, 2025 at 6:34 PM
5. Click **"Restore"** to recover your accounts

### Option 2: Check Windows File History
1. Open **File History** (search in Windows Start menu)
2. Navigate to: `Desktop\PennyWise\pennywise.db`
3. Look for versions from before today
4. Restore the older version

### Option 3: Check for SQLite Backup Files
Look for these files in your project folder:
- `pennywise.db-journal` (WAL journal)
- `pennywise.db-shm` (shared memory)
- `pennywise.db-wal` (write-ahead log)
- Any `.bak` or `.backup` files

### Option 4: Check Recycle Bin
If the database was deleted and recreated, check Windows Recycle Bin for the old file.

## Prevention:
To prevent this in the future:
1. Enable automatic database backups in the application
2. Manually backup `pennywise.db` before major updates
3. Consider using OneDrive version history more regularly

## If Recovery Fails:
You'll need to reconnect your bank accounts manually:
1. Open PennyWise
2. Log in
3. Go to Settings → Bank Connections
4. Reconnect each account via Plaid


