# Supabase Storage Setup - Row-Level Security Fix

## Error
```
403 Unauthorized: new row violates row-level security policy
```

## Root Cause
Supabase Storage has Row-Level Security (RLS) enabled by default, but no policies exist to allow file uploads/downloads.

---

## Solution: Add RLS Policies

### Option 1: Allow All Access (Development/Testing)

Run this SQL in your Supabase SQL Editor:

```sql
-- Allow authenticated users to upload files
CREATE POLICY "Allow authenticated uploads"
ON storage.objects
FOR INSERT
TO authenticated
WITH CHECK (bucket_id = 'campaign-files');

-- Allow authenticated users to read files
CREATE POLICY "Allow authenticated downloads"
ON storage.objects
FOR SELECT
TO authenticated
USING (bucket_id = 'campaign-files');

-- Allow authenticated users to update files
CREATE POLICY "Allow authenticated updates"
ON storage.objects
FOR UPDATE
TO authenticated
USING (bucket_id = 'campaign-files')
WITH CHECK (bucket_id = 'campaign-files');

-- Allow authenticated users to delete files
CREATE POLICY "Allow authenticated deletes"
ON storage.objects
FOR DELETE
TO authenticated
USING (bucket_id = 'campaign-files');
```

### Option 2: Restrict by User (Production)

For better security, only allow users to access their own project files:

```sql
-- Allow users to upload files to their own project folders
CREATE POLICY "Allow user uploads to own projects"
ON storage.objects
FOR INSERT
TO authenticated
WITH CHECK (
    bucket_id = 'campaign-files' AND
    (storage.foldername(name))[1] IN (
        SELECT project_id::text
        FROM projects
        WHERE user_id = auth.uid()::text
    )
);

-- Allow users to read files from their own projects
CREATE POLICY "Allow user downloads from own projects"
ON storage.objects
FOR SELECT
TO authenticated
USING (
    bucket_id = 'campaign-files' AND
    (storage.foldername(name))[1] IN (
        SELECT project_id::text
        FROM projects
        WHERE user_id = auth.uid()::text
    )
);

-- Allow users to update files in their own projects
CREATE POLICY "Allow user updates to own projects"
ON storage.objects
FOR UPDATE
TO authenticated
USING (
    bucket_id = 'campaign-files' AND
    (storage.foldername(name))[1] IN (
        SELECT project_id::text
        FROM projects
        WHERE user_id = auth.uid()::text
    )
)
WITH CHECK (
    bucket_id = 'campaign-files' AND
    (storage.foldername(name))[1] IN (
        SELECT project_id::text
        FROM projects
        WHERE user_id = auth.uid()::text
    )
);

-- Allow users to delete files from their own projects
CREATE POLICY "Allow user deletes from own projects"
ON storage.objects
FOR DELETE
TO authenticated
USING (
    bucket_id = 'campaign-files' AND
    (storage.foldername(name))[1] IN (
        SELECT project_id::text
        FROM projects
        WHERE user_id = auth.uid()::text
    )
);
```

### Option 3: Service Role Bypass (Recommended for CLI)

If you're using the **service_role** key (not anon key), you can bypass RLS entirely.

**Update your `.env`**:
```bash
# Use service_role key instead of anon key for full access
SUPABASE_KEY=your_service_role_key_here  # Found in Settings > API
```

**Where to find it**:
1. Go to Supabase Dashboard
2. Settings → API
3. Copy the `service_role` key (NOT the `anon` key)
4. Update `.env` with this key

⚠️ **Warning**: Service role key bypasses all RLS. Only use in trusted environments (backend, CLI). Never expose in frontend code.

---

## Quick Fix for Development

**Easiest solution for testing**:

1. Go to Supabase Dashboard → Storage → `campaign-files` bucket
2. Click on "Policies" tab
3. Click "New Policy"
4. Choose "For full customization"
5. Paste this policy:

```sql
CREATE POLICY "Allow all operations for authenticated users"
ON storage.objects
FOR ALL
TO authenticated
USING (bucket_id = 'campaign-files')
WITH CHECK (bucket_id = 'campaign-files');
```

6. Click "Review" then "Save"

---

## Verification

After adding policies, test the upload:

```bash
python cli.py run --project-id test-campaign
```

You should see:
```
Uploading 1 file(s) to storage...
  Uploading historical.csv... ✓
```

---

## Alternative: Disable RLS (NOT RECOMMENDED)

If you want to completely disable RLS for the bucket (not secure):

```sql
ALTER TABLE storage.objects DISABLE ROW LEVEL SECURITY;
```

⚠️ **Not recommended for production!** Anyone with your anon key can access all files.

---

## Recommended Setup for This Project

Since this is a **CLI tool** (not a web app), the best approach is:

1. **Use service_role key** in `.env`
   - Bypasses RLS automatically
   - Safe for CLI/backend use
   - No need to configure policies

2. **Or use Option 1 policies** (authenticated access)
   - If you want to use anon key
   - Allows all authenticated operations
   - Good for development

Choose **service_role key** for simplest setup! 🚀
